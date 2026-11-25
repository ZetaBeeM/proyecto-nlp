"""Pipeline RAG: router -> retrieval -> (abstención) -> generación -> verificación.

Medidas contra alucinaciones (en orden de aplicación):
  1. Router de año: si la pregunta menciona 2025/2026 se filtra el corpus; si es
     comparativa se recupera la mitad de fragmentos de cada año (evita sesgo de un año).
  2. Abstención previa: si el mejor fragmento tiene similitud densa < MIN_DENSE_SCORE
     no se llama al LLM (no hay evidencia -> no hay respuesta).
  3. Métricas deterministas: preguntas de densidad/cantidades reciben números ya
     calculados por density.py; el LLM tiene prohibido calcular otros.
  4. Prompt estricto + temperatura 0 + citas obligatorias [n].
  5. Verificación posterior: citas inexistentes, respuesta sin citas y números que no
     aparecen en el contexto quedan marcados como advertencias.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import config, density
from .ingest import KIND_LABELS, load_chunks
from .llm import chat
from .retrieval import Hit, make_retriever
from .textproc import strip_accents, tokenize

ABSTAIN = "No encontré esa información en el material del ramo."

SYSTEM_PROMPT = f"""Eres un asistente que responde preguntas sobre el material del ramo \
"Sistemas Operativos" de la Universidad Adolfo Ibáñez, semestres S2-2025 y S2-2026: presentaciones de clase, \
programas del curso, pautas de pruebas e informes de tareas. Cada fragmento indica su año y su tipo.

REGLAS OBLIGATORIAS:
1. Responde SOLO con información presente en los FRAGMENTOS y en las MÉTRICAS entregadas. \
No uses conocimiento propio aunque lo tengas.
2. Después de cada afirmación escribe la cita del fragmento que la respalda, por ejemplo [1] o [2][3]. \
Todo número o dato que provenga de la sección MÉTRICAS se cita SIEMPRE como [M], nunca con [1], [2], etc.
3. Si los fragmentos no contienen la respuesta, responde exactamente: "{ABSTAIN}"
4. No inventes ni calcules números: usa sólo los que aparecen textualmente en el contexto.
5. Si la pregunta compara años, indica explícitamente qué dice cada año (2025 / 2026). \
Si un año no tiene fragmentos sobre el tema, dilo.
6. Responde en español, de forma breve y precisa (máximo 6 oraciones)."""

COMPARATIVE_RE = re.compile(r"\b(compar\w*|diferenci\w*|cambi\w*|vs|versus|entre (los )?(anos|semestres)|"
                            r"ambos|antes|ahora|mas dificil|aument\w*|disminu\w*|evolucion\w*)\b")
DENSITY_RE = re.compile(r"\b(densidad|dens[oa]s?|cuant[oa]s|cantidad|numero de|slides|diapositivas|palabras|"
                        r"concepto\w*|contenido\w*|dificil\w*|dificultad|carga|cobertura|temas?|extens\w*|"
                        r"elimina\w*|dejaron|agreg\w*|nuevo\w*|tareas?|pruebas?|evaluac\w*)\b")
YEAR_RE = re.compile(r"\b(2025|2026)\b")
SUPPORT_MIN = 0.35  # respaldo léxico mínimo por oración (ver verify_sentences)


@dataclass
class Route:
    years: list[str] | None
    comparative: bool
    density: bool


@dataclass
class Answer:
    question: str
    answer: str
    hits: list[Hit]
    route: Route
    abstained: bool = False
    cited: list[int] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    context: str = ""


def route(question: str) -> Route:
    q = strip_accents(question.lower())
    years = sorted(set(YEAR_RE.findall(q)))
    comparative = bool(COMPARATIVE_RE.search(q)) or len(years) == 2
    is_density = bool(DENSITY_RE.search(q)) and (comparative or "densidad" in q)
    if comparative or not years:
        return Route(years=None, comparative=comparative, density=is_density)
    return Route(years=years, comparative=False, density=is_density)


class MiniRAG:
    def __init__(self, retriever: str = "hybrid", model: str | None = None, k: int = config.TOP_K):
        self.chunks = load_chunks()
        self.retriever = make_retriever(retriever, self.chunks)
        self.model = model or config.LLM_MODEL
        self.k = k
        try:
            self.metrics = density.load()
        except FileNotFoundError:
            self.metrics = None

    def retrieve(self, question: str, r: Route) -> list[Hit]:
        if r.comparative:
            half = max(self.k // 2, 1)
            hits = self.retriever.search(question, half, ["2025"]) + self.retriever.search(question, half, ["2026"])
            return sorted(hits, key=lambda h: -h.score)
        return self.retriever.search(question, self.k, r.years)

    def build_context(self, hits: list[Hit], r: Route) -> str:
        parts = []
        if r.density and self.metrics:
            topics = sorted({h.chunk.topic for h in hits})
            parts.append("[M]\n" + density.context_for_llm(self.metrics, topics))
        for i, h in enumerate(hits, 1):
            c = h.chunk
            body = c.text.split("\n", 1)[1] if "\n" in c.text else c.text
            parts.append(f"[{i}] (año {c.year} | {KIND_LABELS.get(c.kind, c.kind)}: {c.deck} | {c.topic_label} | "
                         f"págs. {c.pages[0]}-{c.pages[-1]})\n{body}")
        return "\n\n".join(parts)

    def ask(self, question: str) -> Answer:
        r = route(question)
        hits = self.retrieve(question, r)
        best = max((h.dense_score for h in hits if h.dense_score is not None), default=None)
        ans = Answer(question=question, answer="", hits=hits, route=r)
        if not r.density and (not hits or (best is not None and best < config.MIN_DENSE_SCORE)):
            ans.answer, ans.abstained = ABSTAIN, True
            ans.warnings.append(f"abstención previa: similitud máxima {best:.2f} < {config.MIN_DENSE_SCORE}"
                                if best is not None else "abstención previa: sin fragmentos")
            return ans
        ans.context = self.build_context(hits, r)
        user = f"FRAGMENTOS:\n{ans.context}\n\nPREGUNTA: {question}\n\nRESPUESTA (con citas):"
        text = chat(SYSTEM_PROMPT, user, model=self.model)
        ans.abstained = is_abstention(text)
        if not ans.abstained and ABSTAIN in text:
            # el modelo respondió y además agregó la frase de abstención (respuesta parcial)
            text = text.replace(ABSTAIN, "").strip()
            ans.warnings.append("respuesta parcial: el modelo indicó que parte de lo pedido no está en las presentaciones")
        ans.answer = text
        if not ans.abstained:
            self.verify(ans)
        return ans

    @staticmethod
    def verify(ans: Answer) -> None:
        MiniRAG.verify_sentences(ans)
        if ans.abstained:
            return
        cites = [int(n) for n in re.findall(r"\[(\d+)\]", ans.answer)]
        valid = sorted({n for n in cites if 1 <= n <= len(ans.hits)})
        invalid = sorted({n for n in cites if not 1 <= n <= len(ans.hits)})
        ans.cited = valid
        if invalid:
            ans.warnings.append(f"citas inexistentes eliminadas: {invalid}")
            for n in invalid:
                ans.answer = ans.answer.replace(f"[{n}]", "")
        if not valid and "[M]" not in ans.answer:
            ans.warnings.append("la respuesta no cita ningún fragmento: verificar manualmente")
        ctx_nums = set(re.findall(r"\d+(?:[.,]\d+)?", ans.context))
        body = re.sub(r"\[(\d+|M)\]", "", ans.answer)
        unsupported = sorted({n for n in re.findall(r"\d+(?:[.,]\d+)?", body)
                              if n not in ctx_nums and n.replace(",", ".") not in ctx_nums})
        if unsupported:
            ans.warnings.append(f"números no presentes en el contexto (posible alucinación): {unsupported}")


    @staticmethod
    def verify_sentences(ans: Answer, min_support: float = SUPPORT_MIN) -> None:
        """Chequeos por oración contra los fragmentos que la oración cita.

        * año: una oración que menciona sólo 2025 (o 2026) no puede citar sólo fragmentos del otro año.
        * respaldo léxico: fracción de términos de contenido de la oración presentes en los fragmentos
          citados. Bajo `min_support` -> posible afirmación no respaldada (p.ej. conocimiento propio del LLM).
        """
        # se corta tras ".!?" salvo que sigan citas, y tras citas si empieza una oración nueva
        checked = flagged = 0
        for sent in re.split(r"(?<=[.!?])\s+(?=[^\[\s])|(?<=\])\s+(?=[A-ZÁÉÍÓÚÑ¿•●*-])|\n+", ans.answer):
            ids = [int(n) for n in re.findall(r"\[(\d+)\]", sent) if 1 <= int(n) <= len(ans.hits)]
            # oración sin cita: se contrasta (con más indulgencia) contra todos los fragmentos
            cited = [ans.hits[i - 1].chunk for i in ids] if ids else [h.chunk for h in ans.hits]
            years = set(YEAR_RE.findall(sent))
            if ids and len(years) == 1 and all(c.year not in years for c in cited):
                ans.warnings.append(f"oración sobre {years.pop()} cita sólo fragmentos de otro año: "
                                    f"\"{sent.strip()[:90]}\"")
            toks = {t for t in tokenize(re.sub(r"\[\d+\]|\b20(25|26)\b", "", sent)) if not t.isdigit()}
            if len(toks) < 4:
                continue
            support_text = " ".join(c.text for c in cited)
            if "[M]" in sent or not ids:
                support_text += " " + ans.context.split("\n\n[1]")[0]  # bloque de métricas, si existe
            support_vocab = set(tokenize(support_text))
            support = len(toks & support_vocab) / len(toks)
            checked += 1
            if support < min_support:
                flagged += 1
                ans.warnings.append(f"bajo respaldo léxico ({support:.0%}) en: \"{sent.strip()[:90]}\"")
        if checked and flagged / checked > 0.5:
            # la mayoría de la respuesta no está en los fragmentos que cita -> se descarta
            ans.warnings.append(f"respuesta descartada: {flagged}/{checked} oraciones sin respaldo en sus fuentes")
            ans.answer, ans.abstained, ans.cited = ABSTAIN, True, []


def is_abstention(text: str) -> bool:
    """Abstención = la respuesta ES la frase de abstención (no una respuesta que además la incluye)."""
    t = strip_accents(text.lower()).strip()
    return t.startswith("no encontre") and len(t) <= len(ABSTAIN) + 40
