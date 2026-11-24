"""Métricas deterministas de densidad de contenidos (2025 vs 2026).

El LLM NUNCA calcula estos números: se calculan aquí y el LLM sólo los verbaliza.
Esto elimina la principal fuente de alucinación en preguntas cuantitativas.

Métricas (por año, por unidad y por tema):
  * pages_raw        páginas del PDF
  * slides           slides únicas (tras fusionar builds y eliminar slides repetidas
                     textualmente dentro del mismo año, p.ej. el "repaso" de LDE en 2026)
  * words            palabras de contenido (sin boilerplate) en slides únicas
  * words_per_slide  densidad de texto
  * concepts         conceptos distintos del glosario (data/glossary.txt) presentes
  * concept_mentions apariciones de conceptos (1 por concepto por slide)
  * concepts_per_slide  densidad conceptual
  * code_slides      slides con código (C/pseudo-código)
  * example_slides   slides de ejemplo/ejercicio/quiz
"""
from __future__ import annotations

import json
import re
from collections import defaultdict

from . import config
from .ingest import Document, load_topics
from .textproc import strip_accents

CODE_RE = re.compile(r"(#include|\bint\s+\w+\s*\(|\bvoid\s*\*?\s*\w+\s*\(|pthread_\w+\(|;\s*$|\{\s*$|\bwhile\s*\(|\bif\s*\()", re.M)
EXAMPLE_RE = re.compile(r"^(ejemplo|ejercicio|example|mini quiz|resuelva|pre-ejemplo)", re.I)


def load_glossary() -> dict[str, list[re.Pattern]]:
    gl = {}
    for line in (config.ROOT / "data" / "glossary.txt").read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        variants = [v.strip() for v in line.split("|") if v.strip()]
        gl[variants[0]] = [re.compile(r"(?<![a-z0-9])" + re.escape(strip_accents(v.lower())) + r"(?![a-z0-9])")
                           for v in variants]
    return gl


def slide_concepts(text: str, glossary) -> set[str]:
    t = strip_accents(text.lower())
    return {c for c, pats in glossary.items() if any(p.search(t) for p in pats)}


def _empty():
    return {"decks": set(), "pages_raw": 0, "slides": 0, "words": 0, "concepts": set(),
            "concept_mentions": 0, "code_slides": 0, "example_slides": 0, "duplicate_slides": 0}


def compute(docs: list[Document]) -> dict:
    glossary = load_glossary()
    topics = load_topics()
    unit_of = {t: u for u, ts in topics["units"].items() for t in ts}
    agg = defaultdict(_empty)  # claves: (year,), (year, unit), (year, unit, topic)
    seen_text = defaultdict(set)
    for d in docs:
        keys = [(d.year,), (d.year, unit_of[d.topic]), (d.year, unit_of[d.topic], d.topic)]
        for k in keys:
            agg[k]["decks"].add(d.deck)
            agg[k]["pages_raw"] += d.page_end - d.page_start + 1
        for s in d.slides:
            norm = re.sub(r"\s+", " ", s.text).strip().lower()
            if not norm:
                continue
            if norm in seen_text[d.year]:
                for k in keys:
                    agg[k]["duplicate_slides"] += 1
                continue
            seen_text[d.year].add(norm)
            cs = slide_concepts(s.text, glossary)
            is_code = len(CODE_RE.findall(s.text)) >= 2
            is_example = bool(EXAMPLE_RE.match(s.title.strip()))
            for k in keys:
                a = agg[k]
                a["slides"] += 1
                a["words"] += s.n_words
                a["concepts"] |= cs
                a["concept_mentions"] += len(cs)
                a["code_slides"] += is_code
                a["example_slides"] += is_example

    def finalize(a):
        n = max(a["slides"], 1)
        return {"decks": len(a["decks"]), "pages_raw": a["pages_raw"], "slides": a["slides"],
                "duplicate_slides": a["duplicate_slides"], "words": a["words"],
                "words_per_slide": round(a["words"] / n, 1), "concepts": len(a["concepts"]),
                "concept_list": sorted(a["concepts"]), "concept_mentions": a["concept_mentions"],
                "concepts_per_slide": round(a["concept_mentions"] / n, 2),
                "code_slides": a["code_slides"], "example_slides": a["example_slides"]}

    out = {"years": {}, "units": {}, "topics": {}, "coverage": {}}
    for k, a in agg.items():
        f = finalize(a)
        if len(k) == 1:
            out["years"][k[0]] = f
        elif len(k) == 2:
            out["units"].setdefault(k[1], {})[k[0]] = f
        else:
            out["topics"].setdefault(k[2], {"label": topics["labels"][k[2]], "unit": k[1]})[k[0]] = f
    for year in out["years"]:
        others = [y for y in out["years"] if y != year]
        out["coverage"][f"solo_{year}"] = sorted(
            t for t, v in out["topics"].items() if year in v and not any(o in v for o in others))
    out["coverage"]["ambos"] = sorted(t for t, v in out["topics"].items() if all(y in v for y in out["years"]))
    out["caveats"] = CAVEATS
    return out


CAVEATS = [
    "S2-2025 tiene 12 decks numerados (Clase_01..Clase_12); S2-2026 tiene 9 decks con numeración "
    "no correlativa (000, 001, 003, 010, 011 + decks por tema), por lo que el material 2026 podría "
    "estar incompleto o el semestre aún no terminar.",
    "No se conoce el número de sesiones de 2026: no es posible medir densidad 'por clase'; se mide por slide y por tema.",
    "Densidad de texto/conceptos es un proxy de carga de contenido, no de dificultad: no mide profundidad "
    "de explicaciones orales, tareas, ni pruebas.",
    "El glosario de conceptos es curado manualmente (data/glossary.txt) y se aplica igual a ambos años.",
]


def save(report: dict) -> None:
    config.RESULTS_DIR.mkdir(exist_ok=True)
    (config.RESULTS_DIR / "densidad.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    (config.RESULTS_DIR / "densidad.md").write_text(to_markdown(report), encoding="utf-8")


def load() -> dict:
    return json.loads((config.RESULTS_DIR / "densidad.json").read_text(encoding="utf-8"))


def _delta(a, b):
    if a == 0:
        return "n/a"
    return f"{(b - a) / a * 100:+.0f}%"


COLS = [("slides", "Slides únicas"), ("words", "Palabras"), ("words_per_slide", "Palabras/slide"),
        ("concepts", "Conceptos distintos"), ("concepts_per_slide", "Conceptos/slide"),
        ("code_slides", "Slides con código"), ("example_slides", "Slides de ejemplo")]


def to_markdown(r: dict) -> str:
    y25, y26 = r["years"]["2025"], r["years"]["2026"]
    L = ["# Densidad de contenidos: Sistemas Operativos S2-2025 vs S2-2026", "",
         "Métricas calculadas de forma determinista (`python -m minirag density`).", "",
         "## Totales por año", "", "| Métrica | 2025 | 2026 | Δ |", "|---|---:|---:|---:|"]
    for k, lab in [("decks", "Decks (PDF)"), ("pages_raw", "Páginas PDF"), ("duplicate_slides", "Slides repetidas (excluidas)")] + COLS:
        L.append(f"| {lab} | {y25[k]} | {y26[k]} | {_delta(y25[k], y26[k])} |")
    L += ["", "## Cobertura de temas", "",
          f"- **En ambos años ({len(r['coverage']['ambos'])})**: " + ", ".join(r["coverage"]["ambos"]),
          f"- **Sólo 2025 ({len(r['coverage']['solo_2025'])})**: " + ", ".join(r["coverage"]["solo_2025"]),
          f"- **Sólo 2026 ({len(r['coverage']['solo_2026'])})**: " + (", ".join(r["coverage"]["solo_2026"]) or "—"),
          "", "## Por unidad", "", "| Unidad | Slides 25 | Slides 26 | Pal/slide 25 | Pal/slide 26 | Conc/slide 25 | Conc/slide 26 |",
          "|---|---:|---:|---:|---:|---:|---:|"]
    for u, v in r["units"].items():
        a, b = v.get("2025"), v.get("2026")
        g = lambda x, k: x[k] if x else "—"
        L.append(f"| {u} | {g(a,'slides')} | {g(b,'slides')} | {g(a,'words_per_slide')} | {g(b,'words_per_slide')} | "
                 f"{g(a,'concepts_per_slide')} | {g(b,'concepts_per_slide')} |")
    L += ["", "## Temas presentes en ambos años", "",
          "| Tema | Slides 25 | Slides 26 | Palabras 25 | Palabras 26 | Conceptos 25 | Conceptos 26 | Conc/slide 25 | Conc/slide 26 |",
          "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for t in r["coverage"]["ambos"]:
        a, b = r["topics"][t]["2025"], r["topics"][t]["2026"]
        L.append(f"| {r['topics'][t]['label']} | {a['slides']} | {b['slides']} | {a['words']} | {b['words']} | "
                 f"{a['concepts']} | {b['concepts']} | {a['concepts_per_slide']} | {b['concepts_per_slide']} |")
    L += ["", "## Advertencias", ""] + [f"- {c}" for c in r["caveats"]]
    return "\n".join(L) + "\n"


def context_for_llm(r: dict, topics: list[str] | None = None) -> str:
    """Resumen compacto en texto plano para pasar al LLM como 'hechos verificados'."""
    y25, y26 = r["years"]["2025"], r["years"]["2026"]
    labels = lambda ts: ", ".join(r["topics"][t]["label"] for t in ts) or "ninguno"
    lines = ["MÉTRICAS CALCULADAS (exactas, no estimar otras; cita [M] para cualquier dato de esta sección):"]
    for k, lab in [("decks", "decks"), ("pages_raw", "páginas PDF")] + COLS:
        lines.append(f"- {lab}: 2025={y25[k]} | 2026={y26[k]} | cambio={_delta(y25[k], y26[k])}")
    lines.append(f"- temas en ambos años: {labels(r['coverage']['ambos'])}")
    lines.append(f"- temas sólo en 2025 (no aparecen en 2026): {labels(r['coverage']['solo_2025'])}")
    lines.append(f"- temas sólo en 2026 (no aparecen en 2025): {labels(r['coverage']['solo_2026'])}")
    for t in topics or []:
        v = r["topics"].get(t)
        if not v:
            continue
        for y in ("2025", "2026"):
            m = v.get(y)
            lines.append(f"- tema '{v['label']}' {y}: " + (
                f"{m['slides']} slides, {m['words']} palabras, {m['concepts']} conceptos distintos, "
                f"{m['concepts_per_slide']} conceptos/slide" if m else "NO CUBIERTO"))
    lines.append("INTERPRETACIÓN: un cambio de menos de 5% en palabras/slide o conceptos/slide se considera "
                 "'prácticamente sin cambio'; los cambios de volumen (slides, palabras) reflejan cobertura, no densidad.")
    lines.append("ADVERTENCIAS: " + " ".join(r["caveats"]))
    return "\n".join(lines)
