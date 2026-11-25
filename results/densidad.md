# Densidad de contenidos: Sistemas Operativos S2-2025 vs S2-2026

Métricas calculadas de forma determinista (`python -m minirag density`).

## Todo el material del ramo, por tipo

| Tipo | Archivos 2025 | Páginas 2025 | Palabras 2025 | Conceptos 2025 | Archivos 2026 | Páginas 2026 | Palabras 2026 | Conceptos 2026 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Clase | 12 | 631 | 13473 | 150 | 9 | 477 | 10087 | 120 |
| Programa del curso | 1 | 3 | 617 | 5 | 1 | 4 | 957 | 5 |
| Pauta de prueba | 2 | 25 | 4453 | 69 | 0 | 0 | 0 | 0 |
| Pauta de repaso (semestre anterior) | 1 | 4 | 751 | 21 | 0 | 0 | 0 | 0 |
| Informe de tarea | 4 | 28 | 2514 | 19 | 0 | 0 | 0 | 0 |
| **Total** | 20 | 691 | 21808 | 153 | 10 | 481 | 11044 | 120 |

Cuenta todas las páginas (incluye slides repetidas; la sección de densidad por slide las excluye).

Total de palabras: 21808 → 11044 (-49%); conceptos distintos: 153 → 120 (-22%).

## Carga evaluativa

| | 2025 | 2026 | Δ |
|---|---:|---:|---:|
| Pruebas oficiales | 2 | 3 | +50% |
| Tareas | obligatorias | opcionales |  |
| Examen final | sí | sí |  |
| Informes de tareas en el corpus | 4 | 0 | -100% |
| Palabras en informes de tareas | 2514 | 0 | -100% |
| Pautas de prueba en el corpus | 2 | 0 | -100% |
| Temas vistos en clases | 27 | 18 | -33% |
| **Temas de clase por prueba** | 13.5 | 6.0 | -56% |
| **Conceptos de clase por prueba** | 75.0 | 40.0 | -47% |
| Slides por prueba | 283.5 | 138.0 | -51% |

- Fuente 2025: 2025/Clase_01 págs. 15-16 ('2 Pruebas (P1 y P2) | Tareas (T) | Examen Final'; tareas = modificar un SO educacional)
- Fuente 2026: 2026/TICS_312_000_26_CFuentes págs. 20-21 ('Tareas opcionales', '3 Pruebas (P1, P2, P3)'); 2026/142302 (2) pág. 3
- Ponderación 2026: P1 30%, P2 35%, P3 35% (NPE); NF = 0,30·NE + 0,70·NPE si rinde examen
- Temas con tarea 2025: estructura_so, lab_xv6, paginacion, sched_proporcional
- Temas evaluados en las pautas 2025 disponibles: eval_conceptos, fs_implementacion, paginacion, reemplazo_paginas, sched_basico, semaforos, threads, traduccion_direcciones

## Densidad de las clases (por slide)

Sólo slides: son las únicas unidades comparables entre años.

| Métrica | 2025 | 2026 | Δ |
|---|---:|---:|---:|
| Decks (PDF) | 12 | 9 | -25% |
| Páginas PDF | 631 | 477 | -24% |
| Slides repetidas (excluidas) | 39 | 32 | -18% |
| Slides únicas | 567 | 414 | -27% |
| Palabras | 13208 | 9550 | -28% |
| Palabras/slide | 23.3 | 23.1 | -1% |
| Conceptos distintos | 150 | 120 | -20% |
| Conceptos/slide | 2.04 | 2.01 | -1% |
| Slides con código | 31 | 13 | -58% |
| Slides de ejemplo | 60 | 35 | -42% |

## Cobertura de temas

- **En ambos años (18)**: api_procesos, curso_admin, dispositivos_io, espacio_direcciones, estructura_so, fs_api, fs_implementacion, intro_so, lde, locks, mlfq, paginacion, procesos, sched_basico, segmentacion, threads, tlb, traduccion_direcciones
- **Sólo 2025 (9)**: bugs_concurrencia, lab_xv6, reemplazo_paginas, sched_multiprocesador, sched_proporcional, semaforos, swap, tablas_multinivel, variables_condicion
- **Sólo 2026 (0)**: —

## Por unidad

| Unidad | Slides 25 | Slides 26 | Pal/slide 25 | Pal/slide 26 | Conc/slide 25 | Conc/slide 26 |
|---|---:|---:|---:|---:|---:|---:|
| Introducción | 44 | 51 | 16.7 | 16.4 | 1.41 | 1.1 |
| Virtualización de CPU | 204 | 138 | 23.6 | 24.2 | 1.81 | 1.93 |
| Concurrencia | 82 | 53 | 18.8 | 19.8 | 1.94 | 2.04 |
| Virtualización de memoria | 143 | 85 | 24.7 | 24.1 | 2.38 | 2.49 |
| Persistencia | 94 | 87 | 27.6 | 26.2 | 2.38 | 2.21 |

## Temas presentes en ambos años

| Tema | Slides 25 | Slides 26 | Palabras 25 | Palabras 26 | Conceptos 25 | Conceptos 26 | Conc/slide 25 | Conc/slide 26 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| API de procesos: fork, exec, wait | 12 | 12 | 258 | 230 | 11 | 10 | 2.0 | 1.92 |
| Información del curso (programa, evaluaciones, requisitos) | 14 | 15 | 200 | 186 | 7 | 4 | 0.57 | 0.33 |
| Dispositivos de entrada/salida: polling, interrupciones, DMA, drivers | 28 | 25 | 716 | 633 | 20 | 17 | 2.18 | 2.04 |
| Virtualización de memoria: espacio de direcciones y API de memoria | 19 | 18 | 658 | 567 | 21 | 19 | 2.58 | 2.44 |
| Estructura del SO: abstracciones, protección, system calls, tipos de kernel | 20 | 21 | 419 | 449 | 27 | 25 | 2.45 | 2.0 |
| Archivos y directorios: abstracciones y operaciones POSIX, links | 29 | 25 | 691 | 544 | 19 | 10 | 2.52 | 2.08 |
| Implementación de un sistema de archivos: inodos, bitmaps, superbloque, caching | 37 | 37 | 1183 | 1104 | 16 | 15 | 2.43 | 2.41 |
| Introducción: qué es un sistema operativo | 10 | 15 | 114 | 201 | 5 | 5 | 0.5 | 0.6 |
| Mecanismo: ejecución directa limitada (LDE), modos, traps, timer interrupt | 25 | 12 | 711 | 284 | 17 | 12 | 1.8 | 1.83 |
| Locks: implementaciones, soporte de hardware, spin/ticket locks, colas | 25 | 30 | 387 | 561 | 22 | 23 | 2.04 | 2.2 |
| Planificación: Multi-Level Feedback Queue (MLFQ) | 21 | 31 | 523 | 845 | 9 | 12 | 2.05 | 2.23 |
| Paginación y tablas de páginas | 18 | 19 | 426 | 400 | 19 | 21 | 2.67 | 2.42 |
| Procesos: definición, espacio de direcciones, PCB, estados, context switch | 36 | 31 | 761 | 600 | 30 | 20 | 2.17 | 2.03 |
| Planificación de CPU: métricas, FIFO, SJF, STCF, Round Robin | 38 | 52 | 844 | 1379 | 14 | 13 | 1.34 | 1.71 |
| Segmentación y fragmentación externa | 19 | 21 | 437 | 437 | 21 | 20 | 2.89 | 2.52 |
| Threads, condiciones de carrera y sección crítica | 17 | 23 | 357 | 489 | 18 | 16 | 1.88 | 1.83 |
| Translation Lookaside Buffer (TLB) | 10 | 10 | 167 | 168 | 12 | 12 | 2.4 | 2.4 |
| Traducción de direcciones: base y bounds (reubicación dinámica) | 15 | 17 | 422 | 473 | 17 | 16 | 2.87 | 2.65 |

## Advertencias

- El material complementario es asimétrico: 2025 incluye 4 informes de tareas, 2 pautas de prueba, 1 pauta de repaso (Prueba 2 de 2023-2) y el programa; 2026 sólo el programa. La ausencia de tareas en 2026 es coherente con lo declarado ('Tareas opcionales'), pero la ausencia de pautas 2026 es falta de material, no evidencia de que no existan.
- Las tareas 2025 son informes escritos por estudiantes: miden la carga práctica (qué hubo que implementar), no el material entregado por el profesor.
- S2-2025 tiene 12 decks numerados (Clase_01..Clase_12); S2-2026 tiene 9 decks con numeración no correlativa (000, 001, 003, 010, 011 + decks por tema), por lo que el material 2026 podría estar incompleto o el semestre aún no terminar.
- No se conoce el número de sesiones de 2026: no es posible medir densidad 'por clase'; se mide por slide y por tema.
- Densidad de texto/conceptos es un proxy de carga de contenido, no de dificultad: no mide profundidad de explicaciones orales, tareas, ni pruebas.
- El glosario de conceptos es curado manualmente (data/glossary.txt) y se aplica igual a ambos años.
