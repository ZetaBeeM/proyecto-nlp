# Mini-RAG: ¿Se volvió más denso el ramo de Sistemas Operativos? (UAI, S2-2025 vs S2-2026)

Sistema de preguntas y respuestas (Retrieval-Augmented Generation) sobre las presentaciones
del ramo **Sistemas Operativos (TICS312)**, que **corre 100% local** con Ollama
(`qwen3:4b` / `gemma3:4b`). Además de responder preguntas sobre los contenidos, mide de forma
**determinista** cómo cambió la densidad de los contenidos entre 2025 y 2026.

> Proyecto 1 "Mini-RAG" del curso de Procesamiento de Lenguaje Natural.
> Esta es la **versión 0** (etapa 1: generada por IA sólo con prompt engineering, ver [`PROMPT.md`](PROMPT.md)).

---

## 1. Inicio rápido

```bash
# 1) Ollama (una de las dos opciones)
sudo pacman -S ollama-cuda && sudo systemctl enable --now ollama      # Arch/CachyOS
#   o binario oficial sin sudo:  ~/.local/opt/ollama/bin/ollama serve

# 2) Modelos
ollama pull qwen3:4b-instruct   # LLM por defecto
ollama pull bge-m3              # embeddings multilingües
ollama pull gemma3:4b           # opcional, LLM alternativo
ollama pull qwen3:4b            # opcional, variante "thinking"

# 3) Entorno Python (uv)
uv sync

# 4) Indexar (PDF -> documentos -> chunks -> embeddings + métricas de densidad)
uv run python -m minirag index

# 5) Usar
uv run python -m minirag ask "¿Qué es el priority boost en MLFQ?"
uv run python -m minirag ask "¿Cuántas pruebas tenía el curso en 2025 y cuántas en 2026?"
uv run python -m minirag ask "¿Cambió la densidad de contenidos entre 2025 y 2026?"
uv run python -m minirag chat                          # modo conversación
uv run python -m minirag density                       # reporte de densidad
uv run python -m minirag eval --retrieval              # compara TF-IDF / BM25 / denso / híbrido
uv run python -m minirag eval                          # evaluación end-to-end con el LLM
uv run python -m minirag eval --model gemma3:4b        # mismo eval con otro LLM
uv run python -m minirag ask "..." --retriever tfidf --show-context   # versión simplificada + contexto
```

Ejemplo de salida:

```
$ uv run python -m minirag ask "¿Cuántas pruebas tenía el curso en 2025 y cuántas en 2026?"

En 2025, el curso tenía 2 pruebas (P1 y P2) [1]. En 2026, el curso tenía 3 pruebas (P1, P2, P3) [2].

Fuentes recuperadas (citadas marcadas con *):
 *[1] 2025 | Clase_01.pdf págs. 12-22 | Información del curso (programa, evaluaciones, requisitos)
 *[2] 2026 | TICS_312_000_26_CFuentes.pdf págs. 16-29 | Información del curso (...)
  ...
```

---

## 2. Respuesta a la pregunta de investigación

Reporte completo: [`results/densidad.md`](results/densidad.md) (generado por `python -m minirag density`).

**Respuesta corta: con el material disponible, la densidad de los contenidos *no* aumentó.
Lo que cambió es la *cobertura*: 2026 trata menos temas, pero algunos con más profundidad.**

| Métrica (slides únicas, sin builds ni repeticiones) | 2025 | 2026 | Δ |
|---|---:|---:|---:|
| Decks / páginas PDF | 12 / 631 | 9 / 477 | −25% / −24% |
| Slides únicas | 567 | 414 | −27% |
| Palabras | 13 279 | 9 599 | −28% |
| **Palabras por slide** | **23.4** | **23.2** | **−1%** |
| Conceptos distintos (glosario) | 150 | 120 | −20% |
| **Conceptos por slide** | **2.04** | **2.01** | **−1%** |
| Slides con código | 31 | 13 | −58% |
| Slides de ejemplo/ejercicio | 60 | 35 | −42% |

- **Densidad por slide: prácticamente igual** (−1% en palabras y en conceptos por slide).
- **Cobertura:** 18 temas aparecen en ambos años. **9 temas de 2025 no aparecen en 2026**
  (semáforos y productor/consumidor, bugs de concurrencia, variables de condición, swap, reemplazo
  de páginas, tablas multinivel, lottery/stride, planificación multiprocesador, laboratorio xv6).
  No hay temas nuevos en 2026.
- **Profundización en temas comunes:** planificación básica (38 → 52 slides), MLFQ (21 → 31),
  locks (25 → 30) y threads (17 → 23) tienen más material en 2026. LDE baja (25 → 12), pero
  porque en 2026 su repaso duplicado se excluye.
- **Menos práctica en slides:** 2026 tiene menos slides con código C y menos ejemplos/ejercicios.
- **Evaluaciones:** 2025 tenía 2 pruebas + tareas + examen; 2026 tiene **3 pruebas + examen** y
  tareas opcionales (slide "Evaluaciones" de cada año). Este es el cambio formal más concreto
  y podría explicar mejor la percepción de "más difícil" que la densidad de las slides.

> ⚠ **Advertencia:** la numeración de los decks 2026 tiene huecos (000, 001, 003, 010, 011) y
> faltan temas que normalmente van al final del semestre, así que **el material 2026 podría estar
> incompleto**. Las conclusiones sobre cobertura deben revisarse con el set completo. La conclusión
> sobre *densidad por slide* es más robusta porque no depende del volumen total.
> La densidad de las slides no mide dificultad: no incluye explicación oral, tareas ni pruebas.

Estas cifras también se pueden consultar en lenguaje natural:
`python -m minirag ask "¿Qué temas se vieron en 2025 pero no aparecen en 2026?"`.

---

## 3. Supuestos verificados antes de diseñar

| Supuesto | Verificación | Consecuencia en el diseño |
|---|---|---|
| "40 ± 10 documentos" | Hay **21 PDFs** (12 de 2025 y 9 de 2026), no 40 | Un *documento* = **sección temática de un deck** (`data/topics.json`) → **48 documentos**. Así "recuperar el documento correcto" es más exigente que "recuperar el PDF" y los temas quedan alineados entre años. |
| Las slides tienen texto extraíble | Sí (PyMuPDF); no hace falta OCR | Las imágenes/diagramas no se indexan (limitación documentada). |
| Texto limpio | Cada slide trae boilerplate ("INGENIERÍA", "Interna", "TICS 312") | Eliminación de boilerplate **por frecuencia** dentro de cada deck. |
| 1 página = 1 slide distinta | Falso: hay *builds* de animación (la misma slide con una línea más) | Se **fusionan builds** (se queda el estado final). |
| Contenido sin repetición | Falso: en 2026 las slides de LDE de `001` (págs. 47-57) se repiten en `003_F` (págs. 1-12) como repaso | Las métricas de densidad **excluyen slides repetidas textualmente** dentro del año. |
| Ambos semestres completos y comparables | 2025: `Clase_01..12`. 2026: 9 decks con numeración no correlativa (000, 001, 003, 010, 011 + decks por tema) y sin semáforos, swap, reemplazo de páginas, tablas multinivel, lottery ni multiprocesador | El sistema **reporta cobertura por tema** y advierte que 2026 podría estar incompleto. No se concluye "menos contenido" a partir de totales. |
| Se puede medir "densidad por clase" | No se conoce el número de sesiones de 2026 | Densidad **por slide y por tema**, no por clase. |
| `qwen3:4b` permite desactivar el razonamiento | Falso en Ollama 0.40: el tag actual es *thinking-only* y `think:false` se ignora (el razonamiento se filtraba en la respuesta, ~80 s/pregunta) | Por defecto `qwen3:4b-instruct` (mismo Qwen3-4B, sin thinking). `qwen3:4b` se usa con `think:true` para que Ollama separe el razonamiento. |
| Los términos están en español | Mezcla es/en (OSTEP: "Chapter 7", "Priority Boost", "Building a LOCK") | Embeddings **multilingües** (bge-m3) + BM25. |

---

## 4. Arquitectura

```
                 ┌────────────── index (offline) ───────────────┐
 S2-2025/*.pdf   │ PyMuPDF → limpieza boilerplate → fusión builds │
 S2-2026/*.pdf ─►│ → segmentación temática (data/topics.json)     │──► 48 documentos / 184 chunks
                 │ → chunks (≈180 palabras, overlap 1 slide)      │──► embeddings bge-m3 (index/)
                 │ → métricas de densidad deterministas           │──► results/densidad.{md,json}
                 └────────────────────────────────────────────────┘

 pregunta ─► Router ─────────────► Retriever híbrido ─► ¿sim. máx < 0.45? ──sí──► "No encontré..."
            (año / comparativa /   BM25 + denso, RRF            │no
             densidad)             (k/2 por año si compara)     ▼
                                                    Contexto: [M] métricas + [1..k] fragmentos
                                                                │
                                                     LLM local (T=0, prompt estricto)
                                                                │
                                               Verificación: citas válidas, números en contexto
                                                                ▼
                                                 Respuesta + fuentes (deck, páginas) + ⚠
```

| Módulo | Qué hace |
|---|---|
| `minirag/ingest.py` | PDF → slides limpias → documentos temáticos → chunks. |
| `minirag/textproc.py` | Normalización (minúsculas, sin tildes), stopwords es/en, stemming liviano para BM25/TF-IDF. |
| `minirag/retrieval.py` | 4 retrievers intercambiables: `tfidf`, `bm25`, `dense`, `hybrid` (RRF). |
| `minirag/llm.py` | Cliente REST mínimo de Ollama (chat + embeddings). |
| `minirag/rag.py` | Router, construcción de contexto, prompt, abstención y verificación posterior. |
| `minirag/density.py` | Métricas deterministas de densidad y su resumen para el LLM. |
| `minirag/evaluate.py` | Evaluación de retrieval y end-to-end. |
| `data/topics.json` | Segmentación manual de cada deck en secciones temáticas (taxonomía OSTEP). |
| `data/glossary.txt` | Glosario curado de ~160 conceptos de SO (es/en) para medir densidad conceptual. |
| `eval/questions.json` | 40 preguntas de prueba con documento(s) gold y hechos clave. |

### Decisiones razonadas

1. **Documento = sección temática.** Cumple el rango 40±10, hace más exigente la evaluación del
   retrieval y permite comparar el *mismo tema* entre años (MLFQ 2025 vs MLFQ 2026).
2. **Chunks de varias slides (≈180 palabras).** Una slide tiene en promedio 23 palabras: muy poco
   contexto para embeddings. Se agrupan slides consecutivas *dentro del mismo documento* (nunca se
   cruza un límite temático) con 1 slide de traslape. Cada chunk lleva un encabezado con año, deck,
   tema y páginas, que ayuda al retrieval ("2026", "MLFQ") y permite citar.
3. **Retrieval híbrido.** BM25 captura términos exactos (`sem_wait`, `MLFQ`, `ASID`); los
   embeddings densos capturan paráfrasis y el cruce es/en. Se fusionan con *Reciprocal Rank Fusion*,
   que no necesita calibrar escalas de score. En la evaluación con preguntas parafraseadas es el único
   con Hit@3 = 1.0.
4. **Router por año.** Si la pregunta menciona un año, se filtra. Si es comparativa, se recuperan
   k/2 fragmentos **por año**; si no, un año puede acaparar el contexto y el LLM "compararía" con un
   solo lado.
5. **Los números los calcula Python, no el LLM.** Un modelo de 4B no cuenta slides ni promedia
   bien. `density.py` calcula todo y el LLM recibe un bloque `[M]` con hechos exactos y la regla
   "no calcules otros números".
6. **Defensas contra alucinación, en capas:**
   - *antes del LLM*: abstención si la similitud máxima es < 0.45 (calibrado: ninguna pregunta
     respondible quedó bajo ese umbral);
   - *en el prompt*: usar sólo el contexto, citar `[n]` en cada afirmación, frase de abstención
     exacta, temperatura 0, semilla fija;
   - *después del LLM* (deterministas, en `MiniRAG.verify*`):
     - se eliminan citas a fragmentos inexistentes y se advierte si no hay citas;
     - se marcan **números que no aparecen en el contexto**;
     - **consistencia de año**: una oración que habla de 2025 no puede citar sólo fragmentos de 2026;
     - **respaldo léxico por oración**: fracción de términos de la oración presentes en los
       fragmentos que cita (< 35% → advertencia);
     - **descarte**: si más de la mitad de las oraciones no tienen respaldo, la respuesta se
       reemplaza por la abstención.
     Estas dos últimas reglas salieron de la evaluación: `gemma3:4b` inventó una explicación del
     "algoritmo del banquero" (que no está en las slides) con una cita válida `[3]` (respaldo léxico
     del 0-31%), y con TF-IDF el LLM afirmó "3 pruebas en 2025" citando un fragmento de 2026.
7. **Todo intercambiable desde la CLI** (`--retriever`, `--model`, `-k`), que es lo que la etapa 2
   del enunciado necesita para comparar versiones simplificadas.

---

## 5. Evaluación

`eval/questions.json` tiene **40 preguntas** (el enunciado pide ≥ 20):

| Tipo | N | Qué mide |
|---|---:|---|
| factual | 26 | Un dato puntual de las slides (2025, 2026 o ambos). |
| comparative | 1 | Comparar ambos años (debe recuperar **los dos** documentos). |
| density | 4 | Preguntas cuantitativas, respondidas con métricas `[M]`. |
| paraphrase | 4 | Mismas ideas **sin** el vocabulario de la slide (contrarresta el sesgo de haber escrito las preguntas mirando las slides). |
| unanswerable | 5 | Información que **no** está en el corpus (RAID 5, journaling, algoritmo del banquero, % de aprobación, receta). Lo correcto es abstenerse. |

Cada hecho gold se verificó contra el texto extraído (campo `src`). Una respuesta se cuenta como
correcta si contiene **todos** los grupos de hechos clave (`must_include`).

RESULTADOS_EVAL

---

## 6. Limitaciones conocidas y mejoras para próximas iteraciones

- **Q37 (paráfrasis del efecto convoy) falla**: el chunk correcto queda fuera del top-k → probar
  *query rewriting*/HyDE con el mismo LLM, re-ranking con cross-encoder (p.ej. `bge-reranker-v2-m3`)
  o aumentar k.
- **La exactitud se mide por palabras clave**: es indulgente con respuestas que mencionan el término
  pero lo explican mal. Mejora: LLM-as-judge local más revisión humana de una muestra.
- **Imágenes y diagramas no se indexan** (muchas slides son diagramas). Mejora: OCR o un VLM local
  (`gemma3:4b` es multimodal) para describir figuras.
- **Segmentación temática manual** (`data/topics.json`). Mejora: segmentación automática por
  cambios de título y similitud entre slides, validada contra la manual.
- **El glosario de conceptos es curado a mano** y algunos términos cortos (`free`, `open`, `stack`)
  pueden contar falsos positivos (afecta a ambos años por igual). Mejora: extracción de
  términos con TF-IDF por tema o con el LLM, revisada.
- **Router basado en reglas** (regex). Mejora: clasificación de intención con el LLM.
- **Densidad ≠ dificultad**: faltan tareas, pruebas y la explicación oral. Si se consiguen
  pruebas de ambos años, el mismo pipeline podría compararlas.
- **El material 2026 puede estar incompleto**: al agregar decks nuevos basta con añadirlos a
  `data/topics.json` y correr `index`.

---

## 7. Mapeo con las etapas del enunciado

| Etapa | Dónde |
|---|---|
| 1. Versión cruda con IA (sólo prompt engineering) | Este commit inicial + [`PROMPT.md`](PROMPT.md). |
| 2. Explicar el código y comparar versiones simplificadas | Secciones 3-5 de este README; `--retriever tfidf|bm25|dense|hybrid`, `--model`; `results/`. |
| 3. Repositorio con historial | Este repositorio git. |
| 4. Presentación de 15 min | Material: secciones 2-6 y `results/`. |
