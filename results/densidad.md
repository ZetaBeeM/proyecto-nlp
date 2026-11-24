# Densidad de contenidos: Sistemas Operativos S2-2025 vs S2-2026

Métricas calculadas de forma determinista (`python -m minirag density`).

## Totales por año

| Métrica | 2025 | 2026 | Δ |
|---|---:|---:|---:|
| Decks (PDF) | 12 | 9 | -25% |
| Páginas PDF | 631 | 477 | -24% |
| Slides repetidas (excluidas) | 39 | 32 | -18% |
| Slides únicas | 567 | 414 | -27% |
| Palabras | 13279 | 9599 | -28% |
| Palabras/slide | 23.4 | 23.2 | -1% |
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
| Virtualización de CPU | 204 | 138 | 23.6 | 24.3 | 1.81 | 1.93 |
| Concurrencia | 82 | 53 | 18.9 | 19.8 | 1.94 | 2.04 |
| Virtualización de memoria | 143 | 85 | 24.7 | 24.1 | 2.38 | 2.49 |
| Persistencia | 94 | 87 | 28.0 | 26.5 | 2.38 | 2.21 |

## Temas presentes en ambos años

| Tema | Slides 25 | Slides 26 | Palabras 25 | Palabras 26 | Conceptos 25 | Conceptos 26 | Conc/slide 25 | Conc/slide 26 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| API de procesos: fork, exec, wait | 12 | 12 | 258 | 230 | 11 | 10 | 2.0 | 1.92 |
| Información del curso (programa, evaluaciones, requisitos) | 14 | 15 | 200 | 186 | 7 | 4 | 0.57 | 0.33 |
| Dispositivos de entrada/salida: polling, interrupciones, DMA, drivers | 28 | 25 | 737 | 651 | 20 | 17 | 2.18 | 2.04 |
| Virtualización de memoria: espacio de direcciones y API de memoria | 19 | 18 | 658 | 567 | 21 | 19 | 2.58 | 2.44 |
| Estructura del SO: abstracciones, protección, system calls, tipos de kernel | 20 | 21 | 419 | 449 | 27 | 25 | 2.45 | 2.0 |
| Archivos y directorios: abstracciones y operaciones POSIX, links | 29 | 25 | 691 | 544 | 19 | 10 | 2.52 | 2.08 |
| Implementación de un sistema de archivos: inodos, bitmaps, superbloque, caching | 37 | 37 | 1208 | 1114 | 16 | 15 | 2.43 | 2.41 |
| Introducción: qué es un sistema operativo | 10 | 15 | 114 | 201 | 5 | 5 | 0.5 | 0.6 |
| Mecanismo: ejecución directa limitada (LDE), modos, traps, timer interrupt | 25 | 12 | 714 | 284 | 17 | 12 | 1.8 | 1.83 |
| Locks: implementaciones, soporte de hardware, spin/ticket locks, colas | 25 | 30 | 389 | 563 | 22 | 23 | 2.04 | 2.2 |
| Planificación: Multi-Level Feedback Queue (MLFQ) | 21 | 31 | 528 | 845 | 9 | 12 | 2.05 | 2.23 |
| Paginación y tablas de páginas | 18 | 19 | 426 | 400 | 19 | 21 | 2.67 | 2.42 |
| Procesos: definición, espacio de direcciones, PCB, estados, context switch | 36 | 31 | 761 | 600 | 30 | 20 | 2.17 | 2.03 |
| Planificación de CPU: métricas, FIFO, SJF, STCF, Round Robin | 38 | 52 | 847 | 1397 | 14 | 13 | 1.34 | 1.71 |
| Segmentación y fragmentación externa | 19 | 21 | 437 | 437 | 21 | 20 | 2.89 | 2.52 |
| Threads, condiciones de carrera y sección crítica | 17 | 23 | 357 | 489 | 18 | 16 | 1.88 | 1.83 |
| Translation Lookaside Buffer (TLB) | 10 | 10 | 167 | 168 | 12 | 12 | 2.4 | 2.4 |
| Traducción de direcciones: base y bounds (reubicación dinámica) | 15 | 17 | 423 | 474 | 17 | 16 | 2.87 | 2.65 |

## Advertencias

- S2-2025 tiene 12 decks numerados (Clase_01..Clase_12); S2-2026 tiene 9 decks con numeración no correlativa (000, 001, 003, 010, 011 + decks por tema), por lo que el material 2026 podría estar incompleto o el semestre aún no terminar.
- No se conoce el número de sesiones de 2026: no es posible medir densidad 'por clase'; se mide por slide y por tema.
- Densidad de texto/conceptos es un proxy de carga de contenido, no de dificultad: no mide profundidad de explicaciones orales, tareas, ni pruebas.
- El glosario de conceptos es curado manualmente (data/glossary.txt) y se aplica igual a ambos años.
