"""Ingesta: PDF -> slides limpias -> documentos temáticos -> chunks.

Decisiones (ver README):
  * Se usa PyMuPDF por página: cada página del PDF es una slide.
  * Boilerplate (logo "INGENIERÍA", "Interna", códigos de ramo, números de página) se
    detecta por frecuencia dentro de cada deck, no con una lista fija.
  * Las slides "build" (animaciones que repiten la slide anterior agregando una línea) se
    fusionan: sólo se conserva el estado final. Así no se infla la densidad ni se
    duplican fragmentos en el retrieval.
  * Un "documento" = sección temática de un archivo, definida en data/topics.json.
  * Tipos de archivo (campo `kind`): "clase" (slides), "programa" (programa oficial del
    curso), "evaluacion" (pautas de pruebas del semestre), "repaso" (pautas de semestres
    anteriores entregadas para estudiar) y "tarea" (informes de tareas, en Markdown).
  * PDF (.pdf/.PDF): cada página es una "página". Markdown (.md): se divide por encabezados
    y luego en bloques de párrafos de a lo más MD_BLOCK_WORDS palabras; cada bloque es una
    "página" (así los límites de topics.json funcionan igual para ambos formatos).
"""
from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass, field, asdict

import pymupdf as fitz

from . import config

BOILERPLATE_MIN_FRACTION = 0.3
ALWAYS_BOILERPLATE = {"INGENIERÍA", "Interna"}
PAGE_NUM_RE = re.compile(r"^\d{1,3}$")
PAGE_FOOTER_RE = re.compile(r"^P[áa]gina \d+ de \d+$")
FILL_LINE_RE = re.compile(r"^[.\s…_-]+$")          # líneas de puntos para responder a mano
MIN_PAGES_FOR_BOILERPLATE = 6                       # en archivos cortos no hay "frecuencia" fiable
SUPPORTED_EXT = {".pdf", ".md"}
MD_BLOCK_WORDS = 150
KINDS = ("clase", "programa", "evaluacion", "repaso", "tarea")


@dataclass
class Slide:
    year: str
    deck: str
    page: int                 # página final (1-based) tras fusionar builds
    pages: list[int]          # todas las páginas fusionadas en esta slide
    title: str
    text: str
    n_words: int
    doc_id: str = ""


@dataclass
class Document:
    doc_id: str
    year: str
    deck: str
    topic: str
    topic_label: str
    page_start: int
    page_end: int
    kind: str = "clase"
    slides: list[Slide] = field(default_factory=list)


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    year: str
    deck: str
    topic: str
    topic_label: str
    pages: list[int]
    text: str                 # texto con encabezado de metadatos (para indexar y para el LLM)
    kind: str = "clase"


KIND_LABELS = {"clase": "Clase", "programa": "Programa del curso", "evaluacion": "Pauta de prueba",
               "repaso": "Pauta de repaso (semestre anterior)", "tarea": "Informe de tarea"}


def _norm_line(line: str) -> str:
    return re.sub(r"\s+", " ", line).strip()


def _md_clean(line: str) -> str:
    line = re.sub(r"^#+\s*", "", line)            # encabezados
    line = re.sub(r"^\s*[-*]\s+", "", line)        # viñetas
    line = line.replace("**", "").replace("`", "")
    return _norm_line(line)


def split_markdown(text: str) -> list[list[str]]:
    """Markdown -> "páginas": una por encabezado, partida en bloques de <= MD_BLOCK_WORDS palabras."""
    sections, cur = [], []
    for line in text.splitlines():
        if re.match(r"^#{1,6}\s", line) and cur:
            sections.append(cur)
            cur = []
        cur.append(line)
    if cur:
        sections.append(cur)
    pages = []
    for sec in sections:
        paras, para = [], []
        for line in sec:
            if not line.strip() or line.strip() in {"---", "```", "```c", "```sh"}:
                if para:
                    paras.append(para)
                para = []
            elif _md_clean(line):
                para.append(_md_clean(line))
        if para:
            paras.append(para)
        block, words = [], 0
        for para in paras:
            w = sum(len(l.split()) for l in para)
            if block and words + w > MD_BLOCK_WORDS:
                pages.append(block)
                block, words = [], 0
            block += para
            words += w
        if block:
            pages.append(block)
    return pages


def extract_raw_pages(path) -> list[list[str]]:
    if path.suffix.lower() == ".md":
        return split_markdown(path.read_text(encoding="utf-8"))
    with fitz.open(path) as doc:
        return [[_norm_line(l) for l in p.get_text("text").splitlines() if _norm_line(l)] for p in doc]


def find_boilerplate(pages: list[list[str]]) -> set[str]:
    n = len(pages)
    if n < MIN_PAGES_FOR_BOILERPLATE:
        return set(ALWAYS_BOILERPLATE)
    counts = Counter(l for p in pages for l in set(p))
    return ALWAYS_BOILERPLATE | {l for l, c in counts.items()
                                 if c >= 2 and c / n >= BOILERPLATE_MIN_FRACTION and len(l) < 40}


def clean_pages(pages: list[list[str]]) -> list[list[str]]:
    bp = find_boilerplate(pages)
    return [[l for l in p if l not in bp and not PAGE_NUM_RE.match(l)
             and not PAGE_FOOTER_RE.match(l) and not FILL_LINE_RE.match(l)] for p in pages]


def _is_build_of(a: list[str], b: list[str]) -> bool:
    """True si la slide `a` es un estado intermedio (build) de la slide `b`."""
    if not a or not b or len(a) > len(b):
        return False
    if a[0] != b[0]:  # mismo título
        return False
    sb = set(b)
    return sum(l in sb for l in a) / len(a) >= 0.9


def load_deck(year: str, pdf_path, merge_builds: bool = True) -> list[Slide]:
    pages = clean_pages(extract_raw_pages(pdf_path))
    deck = pdf_path.stem
    slides: list[Slide] = []
    pending: list[int] = []
    for i, lines in enumerate(pages):
        pending.append(i + 1)
        nxt = pages[i + 1] if i + 1 < len(pages) else None
        if merge_builds and nxt is not None and _is_build_of(lines, nxt):
            continue  # se fusiona con la siguiente
        text = "\n".join(lines)
        slides.append(Slide(year=year, deck=deck, page=i + 1, pages=pending,
                            title=lines[0] if lines else "", text=text,
                            n_words=len(text.split())))
        pending = []
    return slides


def raw_page_count(path) -> int:
    if path.suffix.lower() == ".md":
        return len(extract_raw_pages(path))
    with fitz.open(path) as doc:
        return doc.page_count


def corpus_files(folder) -> list:
    return sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED_EXT)


def deck_spec(spec) -> dict:
    """Una entrada de topics.json["decks"]: lista de secciones (= clase) o {"kind", "sections"}."""
    if isinstance(spec, list):
        return {"kind": "clase", "sections": spec}
    if spec.get("kind") not in KINDS:
        raise ValueError(f"kind inválido: {spec.get('kind')} (válidos: {KINDS})")
    return spec


def load_topics() -> dict:
    return json.loads(config.TOPICS_FILE.read_text(encoding="utf-8"))


def build_documents() -> list[Document]:
    topics = load_topics()
    labels = topics["labels"]
    docs: list[Document] = []
    for year, folder in config.CORPUS_DIRS.items():
        for pdf in corpus_files(folder):
            spec = topics["decks"].get(f"{year}/{pdf.stem}")
            if spec is None:
                raise ValueError(f"Falta segmentación para {year}/{pdf.stem} en {config.TOPICS_FILE} "
                                 f"(ver: python -m minirag titles {year} \"{pdf.stem}\")")
            spec = deck_spec(spec)
            sections = spec["sections"]
            n_pages = raw_page_count(pdf)
            _validate_sections(f"{year}/{pdf.stem}", sections, n_pages)
            slides = load_deck(year, pdf, merge_builds=spec["kind"] == "clase")
            for topic, start, end in sections:
                d = Document(doc_id=f"{year}:{pdf.stem}:{topic}", year=year, deck=pdf.stem,
                             topic=topic, topic_label=labels[topic], page_start=start, page_end=end,
                             kind=spec["kind"])
                # una slide fusionada pertenece a la sección de su página final
                d.slides = [s for s in slides if start <= s.page <= end]
                for s in d.slides:
                    s.doc_id = d.doc_id
                docs.append(d)
    return docs


def _validate_sections(name, sections, n_pages):
    expected = 1
    for topic, start, end in sections:
        if start != expected or end < start:
            raise ValueError(f"{name}: secciones no contiguas en {topic} ({start}-{end})")
        expected = end + 1
    if expected - 1 != n_pages:
        raise ValueError(f"{name}: secciones cubren hasta {expected - 1} pero el PDF tiene {n_pages} páginas")


def chunk_documents(docs: list[Document]) -> list[Chunk]:
    chunks: list[Chunk] = []
    for d in docs:
        slides = [s for s in d.slides if s.n_words > 0]
        i = 0
        n = 0
        while i < len(slides):
            group, words = [], 0
            j = i
            while j < len(slides) and (not group or words + slides[j].n_words <= config.CHUNK_MAX_WORDS):
                group.append(slides[j])
                words += slides[j].n_words
                j += 1
            pages = [p for s in group for p in s.pages]
            header = (f"[{d.year} | {KIND_LABELS[d.kind]}: {d.deck} | {d.topic_label} | "
                      f"págs. {pages[0]}-{pages[-1]}]")
            body = "\n---\n".join(s.text for s in group)
            chunks.append(Chunk(chunk_id=f"{d.doc_id}#{n}", doc_id=d.doc_id, year=d.year,
                                deck=d.deck, topic=d.topic, topic_label=d.topic_label,
                                pages=pages, text=f"{header}\n{body}", kind=d.kind))
            n += 1
            if j >= len(slides):
                break
            i = max(j - config.CHUNK_OVERLAP_SLIDES, i + 1)
    return chunks


def save_corpus(docs: list[Document], chunks: list[Chunk]) -> None:
    config.INDEX_DIR.mkdir(exist_ok=True)
    (config.INDEX_DIR / "documents.json").write_text(json.dumps(
        [{**{k: v for k, v in asdict(d).items() if k != "slides"},
          "slides": [asdict(s) for s in d.slides]} for d in docs],
        ensure_ascii=False, indent=1), encoding="utf-8")
    (config.INDEX_DIR / "chunks.json").write_text(json.dumps(
        [asdict(c) for c in chunks], ensure_ascii=False, indent=1), encoding="utf-8")


def load_chunks() -> list[Chunk]:
    data = json.loads((config.INDEX_DIR / "chunks.json").read_text(encoding="utf-8"))
    return [Chunk(**c) for c in data]


def load_documents() -> list[Document]:
    data = json.loads((config.INDEX_DIR / "documents.json").read_text(encoding="utf-8"))
    docs = []
    for d in data:
        slides = [Slide(**s) for s in d.pop("slides")]
        docs.append(Document(**d, slides=slides))
    return docs


def print_titles(year: str, deck: str) -> None:
    """Utilidad para segmentar decks: imprime página -> título (tras limpieza)."""
    pdf = next(p for p in corpus_files(config.CORPUS_DIRS[year]) if p.stem == deck)
    for i, lines in enumerate(clean_pages(extract_raw_pages(pdf)), 1):
        print(f"{i:3d} | {' / '.join(lines[:3])[:110]}")
