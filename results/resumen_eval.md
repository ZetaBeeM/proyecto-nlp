# Resumen de evaluación

## Retrieval (nivel documento, sin LLM)

| Retriever | Hit@1 | Hit@3 | Hit@k | MRR | AllGold@k (comparativas) |
|---|---:|---:|---:|---:|---:|
| tfidf | 0.844 | 0.906 | 0.969 | 0.891 | 1.0 |
| bm25 | 0.906 | 0.938 | 0.969 | 0.93 | 1.0 |
| dense | 0.906 | 0.938 | 0.969 | 0.928 | 1.0 |
| hybrid | 0.938 | 1.0 | 1.0 | 0.958 | 1.0 |

## End-to-end (40 preguntas)

| Retriever | LLM | Exactitud (respondibles) | Cobertura hechos | Abstención correcta | Falsa abstención | Resp. con números no respaldados | Resp. con bajo respaldo léxico | Seg/pregunta |
|---|---|---:|---:|---:|---:|---:|---:|---:|

Exactitud por tipo de pregunta:

| Retriever | LLM | comparative | density | factual | paraphrase | unanswerable |
|---|---|---:|---:|---:|---:|---:|

Fallos por configuración:

