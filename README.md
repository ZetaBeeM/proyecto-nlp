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

**Respuesta corta: la densidad *por slide* de las clases no cambió (−1 %), pero la carga del
curso sí bajó en 2026.** Hay menos temas, las tareas pasaron de obligatorias a opcionales y los
contenidos se reparten en más pruebas (3 en vez de 2). Cada prueba cubre así menos de la mitad de
temas y conceptos.

El análisis usa **todo el material** (30 archivos), no sólo las slides:

| Tipo de material | Archivos 25 | Palabras 25 | Archivos 26 | Palabras 26 |
|---|---:|---:|---:|---:|
| Clases (slides) | 12 | 13 473 | 9 | 10 087 |
| Programa oficial del curso | 1 | 617 | 1 | 957 |
| Pautas de prueba (P1, P2 2025-2) | 2 | 4 453 | 0 | 0 |
| Pauta de repaso (P2 2023-2) | 1 | 751 | 0 | 0 |
| Informes de tareas (T0–T3, xv6) | 4 | 2 514 | 0 | 0 |
| **Total** | **20** | **21 808** | **10** | **11 044** (−49 %) |

**Carga evaluativa** (declarada por el curso: Clase_01 2025 págs. 15-16; Clase 000 2026 págs. 20-21
y programa 2026 pág. 3):

| | 2025 | 2026 | Δ |
|---|---:|---:|---:|
| Pruebas oficiales | 2 | 3 (30/35/35 %) | +50 % |
| Tareas | obligatorias (modificar xv6) | opcionales | |
| Temas de clase por prueba | 13.5 | 6.0 | −56 % |
| Conceptos de clase por prueba | 75 | 40 | −47 % |
| Slides por prueba | 283.5 | 138 | −51 % |

**Densidad de las clases** (slides únicas, sin builds ni repeticiones; es la única unidad comparable
entre años, porque una página de pauta no equivale a una slide):

| Métrica | 2025 | 2026 | Δ |
|---|---:|---:|---:|
| Decks / páginas PDF | 12 / 631 | 9 / 477 | −25% / −24% |
| Slides únicas | 567 | 414 | −27% |
| Palabras | 13 208 | 9 550 | −28% |
| **Palabras por slide** | **23.3** | **23.1** | **−1%** |
| Conceptos distintos (glosario) | 150 | 120 | −20% |
| **Conceptos por slide** | **2.04** | **2.01** | **−1%** |
| Slides con código | 31 | 13 | −58% |
| Slides de ejemplo/ejercicio | 60 | 35 | −42% |

- **Densidad por slide: prácticamente igual** (−1% en palabras y en conceptos por slide).
- **Cobertura:** 18 temas aparecen en ambos años. **9 temas de 2025 no aparecen en 2026**
  (semáforos y productor/consumidor, bugs de concurrencia, variables de condición, swap, reemplazo
  de páginas, tablas multinivel, lottery/stride, planificación multiprocesador, laboratorio xv6).
  No hay temas nuevos en 2026. Dos de esos temas además se *evaluaron* en 2025: semáforos (P1) y
  reemplazo de páginas (P2). Lottery scheduling tuvo una tarea (T2).
- **Carga práctica:** en 2025 las 4 tareas obligatorias implicaban modificar el kernel de xv6
  (system calls, lottery scheduler, protección de páginas). En 2026 son opcionales y no hay informes.
- **Profundización en temas comunes:** planificación básica (38 → 52 slides), MLFQ (21 → 31),
  locks (25 → 30) y threads (17 → 23) tienen más material en 2026.
- **Menos práctica en slides:** 2026 tiene menos slides con código C y menos ejemplos/ejercicios.

> ⚠ **Advertencia:** la numeración de los decks 2026 tiene huecos (000, 001, 003, 010, 011) y
> faltan temas que normalmente van al final del semestre, así que **el material 2026 podría estar
> incompleto**. Las conclusiones sobre cobertura deben revisarse con el set completo. La conclusión
> sobre *densidad por slide* es más robusta porque no depende del volumen total.
> El material complementario es **asimétrico**: no hay pautas de prueba de 2026, y eso es falta de
> material, no evidencia de que no existan. Las métricas "por prueba" usan el número de pruebas
> declarado, no las pautas disponibles. Los informes de tareas son de estudiantes: miden la carga
> práctica, no el material del profesor.

Estas cifras también se pueden consultar en lenguaje natural:
`python -m minirag ask "¿Qué temas se vieron en 2025 pero no aparecen en 2026?"`.

---

## 3. Supuestos verificados antes de diseñar

| Supuesto | Verificación | Consecuencia en el diseño |
|---|---|---|
| "40 ± 10 documentos" | Hay **30 archivos**: 21 decks de clases, 2 programas, 3 pautas de prueba (PDF) y 4 informes de tareas (Markdown) | Un *documento* = **sección temática de un archivo** (`data/topics.json`) → **65 documentos**. Así "recuperar el documento correcto" es más exigente que "recuperar el archivo" y los temas quedan alineados entre años y tipos de material. |
| Todo el material son slides | Falso: programas, pautas e informes tienen páginas largas, otro formato y (las pautas) líneas de puntos para responder | Cada sección tiene un `kind` (clase, programa, evaluacion, repaso, tarea). La densidad por slide se calcula sólo sobre clases y el resto se mide por tipo. No se fusionan *builds* fuera de las clases. Se eliminan líneas de relleno y pies "Página N de M". En archivos de menos de 6 páginas no se detecta boilerplate por frecuencia (todo parecería boilerplate). |
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
 S2-2025/*.pdf|md│ PyMuPDF / Markdown → limpieza → fusión builds  │
 S2-2026/*.pdf|md►│ → segmentación temática + kind (topics.json)  │──► 30 archivos / 65 documentos / 239 chunks
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
| `minirag/ingest.py` | PDF/Markdown → páginas limpias → documentos temáticos (con `kind`) → chunks. |
| `minirag/textproc.py` | Normalización (minúsculas, sin tildes), stopwords es/en, stemming liviano para BM25/TF-IDF. |
| `minirag/retrieval.py` | 4 retrievers intercambiables: `tfidf`, `bm25`, `dense`, `hybrid` (RRF). |
| `minirag/llm.py` | Cliente REST mínimo de Ollama (chat + embeddings). |
| `minirag/rag.py` | Router, construcción de contexto, prompt, abstención y verificación posterior. |
| `minirag/density.py` | Métricas deterministas: todo el material por tipo, carga evaluativa y densidad por slide; resumen para el LLM. |
| `minirag/evaluate.py` | Evaluación de retrieval y end-to-end. |
| `data/topics.json` | Segmentación manual de cada archivo en secciones temáticas (taxonomía OSTEP), tipo de material y estructura de evaluación declarada (`course`). |
| `data/glossary.txt` | Glosario curado de ~160 conceptos de SO (es/en) para medir densidad conceptual. |
| `eval/questions.json` | 51 preguntas de prueba con documento(s) gold y hechos clave. |

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

`eval/questions.json` tiene **51 preguntas** (el enunciado pide ≥ 20). Las preguntas q41–q51 son
sobre el material complementario (programa 2026, pautas, tareas):

| Tipo | N | Qué mide |
|---|---:|---|
| factual | 34 | Un dato puntual del material (2025, 2026 o ambos). |
| comparative | 2 | Comparar ambos años (debe recuperar al menos un documento gold **de cada año**). |
| density | 5 | Preguntas cuantitativas, respondidas con métricas `[M]`. |
| paraphrase | 5 | Mismas ideas **sin** el vocabulario de la slide (contrarresta el sesgo de haber escrito las preguntas mirando las slides). |
| unanswerable | 5 | Información que **no** está en el corpus (RAID 5, journaling, algoritmo del banquero, % de aprobación, receta). Lo correcto es abstenerse. |

Cada hecho gold se verificó contra el texto extraído (campo `src`). Una respuesta se cuenta como
correcta si contiene **todos** los grupos de hechos clave (`must_include`).

### Retrieval (nivel documento, sin LLM)

| Retriever | Hit@1 | Hit@3 | Hit@k | MRR | AllGold@k (comparativas) |
|---|---:|---:|---:|---:|---:|
| tfidf | 0.81 | 0.905 | 0.976 | 0.867 | 0.333 |
| bm25 | 0.833 | 0.952 | 0.976 | 0.894 | 0.333 |
| dense | 0.857 | 0.929 | 0.976 | 0.9 | 0.333 |
| hybrid | 0.905 | 0.976 | 1.0 | 0.94 | 0.333 |

### End-to-end (51 preguntas)

| Retriever | LLM | Exactitud (respondibles) | Cobertura hechos | Abstención correcta | Falsa abstención | Resp. con números no respaldados | Resp. con bajo respaldo léxico | Seg/pregunta |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| bm25 | qwen3:4b-instruct | 100.0% | 100.0% | 100% | 0.0% | 1 | 6 | 1.2 |
| hybrid | qwen3:4b-instruct | 95.7% | 95.7% | 100% | 4.3% | 0 | 7 | 1.2 |
| tfidf | qwen3:4b-instruct | 93.5% | 94.6% | 100% | 2.2% | 1 | 5 | 1.2 |

Exactitud por tipo de pregunta:

| Retriever | LLM | comparative | density | factual | paraphrase | unanswerable |
|---|---|---:|---:|---:|---:|---:|
| bm25 | qwen3:4b-instruct | 100% | 100% | 100% | 100% | 100% |
| hybrid | qwen3:4b-instruct | 100% | 100% | 97% | 80% | 100% |
| tfidf | qwen3:4b-instruct | 100% | 100% | 94% | 80% | 100% |

Fallos por configuración:

- `bm25` + `qwen3:4b-instruct`: ninguno
- `hybrid` + `qwen3:4b-instruct`: q05, q37
- `tfidf` + `qwen3:4b-instruct`: q05, q20, q37

Comparado con la versión de 21 PDFs (32 preguntas con gold): el híbrido pasó de Hit@1 0.938 a 0.905
y las comparativas, de AllGold@k 1.0 a 0.333 (falla en q11 y q50). La razón es que el material
nuevo de 2025 trae distractores: las pautas dicen "Prueba … 2025" y los informes dicen "Tarea", y
desplazan la slide de Clase_01 que tiene la respuesta fuera de los k/2 = 3 fragmentos por año. Las
respuestas de q11 y q50 son correctas igual, porque las métricas `[M]` traen la estructura de
evaluación.

---

## 6. Limitaciones conocidas y mejoras para próximas iteraciones

- **Comparativas con más material (q11, q50)**: el lado 2025 queda dominado por pautas e informes
  → probar k por año mayor en comparativas, diversificar por tipo de material (≤ 1 fragmento por
  `kind`) o un router de intención "organización del curso" que priorice `curso_admin`.
- **q05 se descarta por el verificador** (el LLM parafrasea y el respaldo léxico queda < 35 %).
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
- **Densidad ≠ dificultad**: falta la explicación oral y el material complementario es sólo de 2025.
  Si se consiguen pautas 2026, basta con agregarlas con `kind: "evaluacion"` y el reporte las compara.
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
