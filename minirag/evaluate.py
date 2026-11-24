"""Evaluación: (1) retrieval por documento y (2) respuestas end-to-end.

Retrieval (sin LLM, rápido): Hit@1, Hit@3, Hit@k, MRR a nivel de documento, y
'AllGold@k' para preguntas comparativas (deben aparecer ambos años).
Respuestas: exactitud por hechos clave, abstención correcta en preguntas sin
respuesta, falsas abstenciones y advertencias de verificación (números no respaldados).
"""
from __future__ import annotations

import json
import time

import numpy as np

from . import config
from .rag import MiniRAG, route
from .textproc import strip_accents


def load_questions():
    return json.loads(config.EVAL_FILE.read_text(encoding="utf-8"))["questions"]


def _doc_ranking(hits):
    seen = []
    for h in hits:
        if h.chunk.doc_id not in seen:
            seen.append(h.chunk.doc_id)
    return seen


def eval_retrieval(retrievers=("tfidf", "bm25", "dense", "hybrid"), k=config.TOP_K):
    qs = [q for q in load_questions() if q["gold_docs"]]
    all_q = load_questions()
    summary, per_q = {}, {}
    for name in retrievers:
        rag = MiniRAG(retriever=name, k=k)
        rows = []
        for q in qs:
            ranking = _doc_ranking(rag.retrieve(q["question"], route(q["question"])))
            gold = set(q["gold_docs"])
            ranks = [i for i, d in enumerate(ranking, 1) if d in gold]
            first = ranks[0] if ranks else None
            rows.append({"id": q["id"], "first_rank": first, "ranking": ranking[:k],
                         "all_gold": gold <= set(ranking) if q.get("require_all_gold") else None})
        n = len(rows)
        comp = [r for r in rows if r["all_gold"] is not None]
        summary[name] = {
            "n": n,
            "hit@1": round(sum(r["first_rank"] == 1 for r in rows) / n, 3),
            "hit@3": round(sum(bool(r["first_rank"]) and r["first_rank"] <= 3 for r in rows) / n, 3),
            f"hit@{k}": round(sum(r["first_rank"] is not None for r in rows) / n, 3),
            "mrr": round(sum(1 / r["first_rank"] for r in rows if r["first_rank"]) / n, 3),
            "all_gold@k (comparativas)": round(sum(r["all_gold"] for r in comp) / len(comp), 3) if comp else None,
        }
        per_q[name] = rows
        # Para calibrar el umbral de abstención: similitud densa máxima por tipo de pregunta
        if name in ("dense", "hybrid"):
            best = {"answerable": [], "unanswerable": []}
            for q in all_q:
                if q["type"] == "density":
                    continue
                hits = rag.retrieve(q["question"], route(q["question"]))
                s = max(h.dense_score for h in hits)
                best["unanswerable" if q["type"] == "unanswerable" else "answerable"].append(round(s, 3))
            summary[name]["max_dense_score"] = {t: {"min": min(v), "mean": round(float(np.mean(v)), 3), "max": max(v)}
                                                for t, v in best.items()}
    return summary, per_q


def _norm(s):
    return strip_accents(s.lower())


def score_answer(q, ans):
    text = _norm(ans.answer)
    if q["type"] == "unanswerable":
        return {"correct": ans.abstained, "coverage": None}
    if ans.abstained:
        return {"correct": False, "coverage": 0.0}
    groups = q["must_include"]
    covered = [any(_norm(alt) in text for alt in g) for g in groups]
    return {"correct": all(covered), "coverage": round(sum(covered) / len(groups), 2) if groups else 1.0}


def eval_answers(retriever="hybrid", model=None, k=config.TOP_K, only=None):
    rag = MiniRAG(retriever=retriever, model=model, k=k)
    rows = []
    for q in load_questions():
        if only and q["id"] not in only:
            continue
        t = time.time()
        ans = rag.ask(q["question"])
        dt = time.time() - t
        sc = score_answer(q, ans)
        docs = _doc_ranking(ans.hits)
        rows.append({"id": q["id"], "type": q["type"], "question": q["question"], "answer": ans.answer,
                     "correct": sc["correct"], "coverage": sc["coverage"], "abstained": ans.abstained,
                     "retrieved_gold": bool(set(q["gold_docs"]) & set(docs)) if q["gold_docs"] else None,
                     "cited": ans.cited, "warnings": ans.warnings, "seconds": round(dt, 1),
                     "sources": [f"{h.chunk.year}/{h.chunk.deck} p{h.chunk.pages[0]}-{h.chunk.pages[-1]}" for h in ans.hits]})
        print(f"  {q['id']} {'OK ' if sc['correct'] else 'BAD'} {dt:5.1f}s {q['question'][:60]}")
    answerable = [r for r in rows if r["type"] != "unanswerable"]
    unans = [r for r in rows if r["type"] == "unanswerable"]
    summary = {
        "retriever": retriever, "model": rag.model, "n": len(rows),
        "accuracy_answerable": round(sum(r["correct"] for r in answerable) / max(len(answerable), 1), 3),
        "mean_fact_coverage": round(float(np.mean([r["coverage"] for r in answerable])), 3) if answerable else None,
        "false_abstention_rate": round(sum(r["abstained"] for r in answerable) / max(len(answerable), 1), 3),
        "correct_abstention_rate": round(sum(r["abstained"] for r in unans) / max(len(unans), 1), 3) if unans else None,
        "answers_with_unsupported_numbers": sum(any("números no presentes" in w for w in r["warnings"]) for r in rows),
        "answers_without_citations": sum(any("no cita" in w for w in r["warnings"]) for r in rows),
        "answers_with_low_lexical_support": sum(any("bajo respaldo" in w for w in r["warnings"]) for r in rows),
        "answers_with_year_mismatch": sum(any("otro año" in w for w in r["warnings"]) for r in rows),
        "mean_seconds": round(float(np.mean([r["seconds"] for r in rows])), 1),
        "by_type": {t: round(np.mean([r["correct"] for r in rows if r["type"] == t]), 3)
                    for t in sorted({r["type"] for r in rows})},
    }
    return summary, rows


def save(name: str, payload: dict):
    config.RESULTS_DIR.mkdir(exist_ok=True)
    path = config.RESULTS_DIR / f"{name}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    return path


def report() -> str:
    """Consolida results/eval_*.json en una tabla markdown (results/resumen_eval.md)."""
    L = ["# Resumen de evaluación", "", "## Retrieval (nivel documento, sin LLM)", "",
         "| Retriever | Hit@1 | Hit@3 | Hit@k | MRR | AllGold@k (comparativas) |", "|---|---:|---:|---:|---:|---:|"]
    rp = config.RESULTS_DIR / "eval_retrieval.json"
    if rp.exists():
        for name, m in json.loads(rp.read_text())["summary"].items():
            hk = next(v for k, v in m.items() if k.startswith("hit@") and k not in ("hit@1", "hit@3"))
            L.append(f"| {name} | {m['hit@1']} | {m['hit@3']} | {hk} | {m['mrr']} | {m['all_gold@k (comparativas)']} |")
    L += ["", "## End-to-end (40 preguntas)", "",
          "| Retriever | LLM | Exactitud (respondibles) | Cobertura hechos | Abstención correcta | Falsa abstención | "
          "Resp. con números no respaldados | Resp. con bajo respaldo léxico | Seg/pregunta |",
          "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for f in sorted(config.RESULTS_DIR.glob("eval_answers_*.json")):
        m = json.loads(f.read_text())["summary"]
        L.append(f"| {m['retriever']} | {m['model']} | {m['accuracy_answerable']:.1%} | {m['mean_fact_coverage']:.1%} | "
                 f"{m['correct_abstention_rate']:.0%} | {m['false_abstention_rate']:.1%} | "
                 f"{m['answers_with_unsupported_numbers']} | {m.get('answers_with_low_lexical_support', '—')} | {m['mean_seconds']} |")
    L += ["", "Exactitud por tipo de pregunta:", "", "| Retriever | LLM | " + " | ".join(
        ["comparative", "density", "factual", "paraphrase", "unanswerable"]) + " |", "|---|---|" + "---:|" * 5]
    for f in sorted(config.RESULTS_DIR.glob("eval_answers_*.json")):
        m = json.loads(f.read_text())["summary"]
        L.append(f"| {m['retriever']} | {m['model']} | " + " | ".join(
            f"{m['by_type'].get(t, 0):.0%}" for t in ["comparative", "density", "factual", "paraphrase", "unanswerable"]) + " |")
    L += ["", "Fallos por configuración:", ""]
    for f in sorted(config.RESULTS_DIR.glob("eval_answers_*.json")):
        d = json.loads(f.read_text())
        bad = [r["id"] for r in d["per_question"] if not r["correct"]]
        L.append(f"- `{d['summary']['retriever']}` + `{d['summary']['model']}`: {', '.join(bad) or 'ninguno'}")
    md = "\n".join(L) + "\n"
    (config.RESULTS_DIR / "resumen_eval.md").write_text(md, encoding="utf-8")
    return md
