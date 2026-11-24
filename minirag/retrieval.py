"""Retrievers intercambiables: TF-IDF, BM25, denso (embeddings Ollama) e híbrido (RRF).

Todos exponen `search(query, k, years=None) -> list[Hit]`. Tenerlos intercambiables es lo
que permite la comparación de versiones simplificadas que pide el enunciado
(p.ej. embeddings vs TF-IDF) con `python -m minirag eval --retriever ...`.
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from . import config
from .ingest import Chunk
from .llm import embed
from .textproc import tokenize


@dataclass
class Hit:
    chunk: Chunk
    score: float
    dense_score: float | None = None  # similitud coseno, usada para abstención


def _mask(chunks, years):
    return np.array([years is None or c.year in years for c in chunks])


class TfidfRetriever:
    name = "tfidf"

    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks
        self.vec = TfidfVectorizer(tokenizer=tokenize, lowercase=False, token_pattern=None,
                                   sublinear_tf=True, ngram_range=(1, 2), min_df=1)
        self.m = self.vec.fit_transform([c.text for c in chunks])

    def scores(self, query):
        return (self.m @ self.vec.transform([query]).T).toarray().ravel()

    def search(self, query, k=config.TOP_K, years=None):
        return _top(self.chunks, self.scores(query), k, years)


class BM25Retriever:
    name = "bm25"

    def __init__(self, chunks: list[Chunk], k1=1.5, b=0.75):
        self.chunks, self.k1, self.b = chunks, k1, b
        self.docs = [Counter(tokenize(c.text)) for c in chunks]
        self.lens = np.array([sum(d.values()) for d in self.docs], dtype=float)
        self.avgdl = self.lens.mean()
        df = Counter(t for d in self.docs for t in d)
        n = len(chunks)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def scores(self, query):
        q = tokenize(query)
        s = np.zeros(len(self.docs))
        for i, d in enumerate(self.docs):
            norm = self.k1 * (1 - self.b + self.b * self.lens[i] / self.avgdl)
            s[i] = sum(self.idf.get(t, 0) * d[t] * (self.k1 + 1) / (d[t] + norm) for t in q if t in d)
        return s

    def search(self, query, k=config.TOP_K, years=None):
        return _top(self.chunks, self.scores(query), k, years)


class DenseRetriever:
    name = "dense"

    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks
        self.emb = load_or_build_embeddings(chunks)

    def scores(self, query):
        q = np.array(embed([query])[0])
        q /= np.linalg.norm(q)
        return self.emb @ q

    def search(self, query, k=config.TOP_K, years=None):
        s = self.scores(query)
        hits = _top(self.chunks, s, k, years)
        for h in hits:
            h.dense_score = h.score
        return hits


class HybridRetriever:
    """Reciprocal Rank Fusion de BM25 (exactitud léxica: 'MLFQ', 'fork') + denso (paráfrasis, es/en)."""
    name = "hybrid"

    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks
        self.bm25 = BM25Retriever(chunks)
        self.dense = DenseRetriever(chunks)

    def search(self, query, k=config.TOP_K, years=None):
        mask = _mask(self.chunks, years)
        ds = self.dense.scores(query)
        fused = np.zeros(len(self.chunks))
        for s in (self.bm25.scores(query), ds):
            s = np.where(mask, s, -np.inf)
            for rank, i in enumerate(np.argsort(-s)):
                if mask[i]:
                    fused[i] += 1 / (config.RRF_K + rank + 1)
        hits = _top(self.chunks, fused, k, years)
        for h in hits:
            h.dense_score = float(ds[self.chunks.index(h.chunk)])
        return hits


def _top(chunks, scores, k, years):
    mask = _mask(chunks, years)
    order = [i for i in np.argsort(-scores) if mask[i]][:k]
    return [Hit(chunk=chunks[i], score=float(scores[i])) for i in order]


def load_or_build_embeddings(chunks: list[Chunk]) -> np.ndarray:
    path = config.INDEX_DIR / f"embeddings_{config.EMBED_MODEL.replace(':', '_')}.npz"
    ids = [c.chunk_id for c in chunks]
    if path.exists():
        data = np.load(path, allow_pickle=False)
        if list(data["ids"]) == ids:
            return data["emb"]
    vecs = []
    for i in range(0, len(chunks), 16):
        vecs.extend(embed([c.text for c in chunks[i:i + 16]]))
    emb = np.array(vecs, dtype=np.float32)
    emb /= np.linalg.norm(emb, axis=1, keepdims=True)
    np.savez(path, ids=np.array(ids), emb=emb)
    return emb


RETRIEVERS = {r.name: r for r in (TfidfRetriever, BM25Retriever, DenseRetriever, HybridRetriever)}


def make_retriever(name: str, chunks: list[Chunk]):
    return RETRIEVERS[name](chunks)
