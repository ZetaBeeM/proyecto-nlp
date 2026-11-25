# Resumen de evaluación

## Retrieval (nivel documento, sin LLM)

| Retriever | Hit@1 | Hit@3 | Hit@k | MRR | AllGold@k (comparativas) |
|---|---:|---:|---:|---:|---:|
| tfidf | 0.81 | 0.905 | 0.976 | 0.867 | 0.333 |
| bm25 | 0.833 | 0.952 | 0.976 | 0.894 | 0.333 |
| dense | 0.857 | 0.929 | 0.976 | 0.9 | 0.333 |
| hybrid | 0.905 | 0.976 | 1.0 | 0.94 | 0.333 |

## End-to-end (51 preguntas)

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
