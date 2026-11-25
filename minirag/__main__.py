"""CLI del Mini-RAG.

  python -m minirag index                 # PDF -> documentos -> chunks -> embeddings + métricas
  python -m minirag ask "pregunta"        # una pregunta (con fuentes)
  python -m minirag chat                  # modo interactivo
  python -m minirag density               # reporte de densidad 2025 vs 2026
  python -m minirag eval --retrieval      # compara retrievers (sin LLM)
  python -m minirag eval                  # evaluación end-to-end (LLM)
  python -m minirag report                # tabla consolidada de evaluaciones
  python -m minirag titles 2025 Clase_04  # utilidad para segmentar decks
"""
import argparse
import json
import sys

from . import config


def cmd_index(_):
    from . import density, ingest
    from .retrieval import load_or_build_embeddings
    docs = ingest.build_documents()
    chunks = ingest.chunk_documents(docs)
    ingest.save_corpus(docs, chunks)
    files = {(d.year, d.deck) for d in docs}
    print(f"{len(files)} archivos, {len(docs)} documentos, {len(chunks)} chunks "
          f"({sum(d.year == '2025' for d in docs)} de 2025, {sum(d.year == '2026' for d in docs)} de 2026)")
    density.save(density.compute(docs))
    print(f"métricas de densidad -> {config.RESULTS_DIR / 'densidad.md'}")
    load_or_build_embeddings(chunks)
    print(f"embeddings ({config.EMBED_MODEL}) listos en {config.INDEX_DIR}")


def print_answer(ans, show_context=False):
    print(f"\n{ans.answer}\n")
    if ans.abstained and not ans.hits:
        return
    print("Fuentes recuperadas" + (" (citadas marcadas con *)" if ans.cited else "") + ":")
    for i, h in enumerate(ans.hits, 1):
        c = h.chunk
        mark = "*" if i in ans.cited else " "
        print(f" {mark}[{i}] {c.year} | {c.deck} págs. {c.pages[0]}-{c.pages[-1]} | {c.topic_label}")
    for w in ans.warnings:
        print(f" ⚠ {w}")
    if show_context:
        print("\n--- CONTEXTO ENVIADO AL LLM ---\n" + ans.context)


def cmd_ask(a):
    from .rag import MiniRAG
    rag = MiniRAG(retriever=a.retriever, model=a.model, k=a.k)
    print_answer(rag.ask(a.question), a.show_context)


def cmd_chat(a):
    from .rag import MiniRAG
    rag = MiniRAG(retriever=a.retriever, model=a.model, k=a.k)
    print(f"Mini-RAG Sistemas Operativos (modelo {rag.model}, retriever {a.retriever}). 'salir' para terminar.")
    while True:
        try:
            q = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if q.lower() in {"salir", "exit", "quit"}:
            break
        if q:
            print_answer(rag.ask(q), a.show_context)


def cmd_density(_):
    from . import density, ingest
    r = density.compute(ingest.load_documents())
    density.save(r)
    print(density.to_markdown(r))


def cmd_eval(a):
    from . import evaluate
    if a.retrieval:
        summary, per_q = evaluate.eval_retrieval(k=a.k)
        print(json.dumps(summary, indent=1, ensure_ascii=False))
        print("->", evaluate.save("eval_retrieval", {"summary": summary, "per_question": per_q}))
        return
    only = set(a.only.split(",")) if a.only else None
    summary, rows = evaluate.eval_answers(retriever=a.retriever, model=a.model, k=a.k, only=only)
    print(json.dumps(summary, indent=1, ensure_ascii=False))
    name = f"eval_answers_{a.retriever}_{summary['model'].replace(':', '_')}"
    print("->", evaluate.save(name, {"summary": summary, "per_question": rows}))


def cmd_report(_):
    from . import evaluate
    print(evaluate.report())


def cmd_titles(a):
    from .ingest import print_titles
    print_titles(a.year, a.deck)


def main(argv=None):
    p = argparse.ArgumentParser(prog="minirag", description="Mini-RAG Sistemas Operativos UAI")
    sub = p.add_subparsers(dest="cmd", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--retriever", default="hybrid", choices=["tfidf", "bm25", "dense", "hybrid"])
    common.add_argument("--model", default=None, help=f"modelo Ollama (default {config.LLM_MODEL})")
    common.add_argument("-k", type=int, default=config.TOP_K)
    common.add_argument("--show-context", action="store_true", help="muestra el contexto enviado al LLM")
    sub.add_parser("index").set_defaults(f=cmd_index)
    s = sub.add_parser("ask", parents=[common]); s.add_argument("question"); s.set_defaults(f=cmd_ask)
    sub.add_parser("chat", parents=[common]).set_defaults(f=cmd_chat)
    sub.add_parser("density").set_defaults(f=cmd_density)
    s = sub.add_parser("eval", parents=[common])
    s.add_argument("--retrieval", action="store_true", help="sólo retrieval, compara los 4 retrievers")
    s.add_argument("--only", help="ids separados por coma, p.ej. q01,q11")
    s.set_defaults(f=cmd_eval)
    sub.add_parser("report").set_defaults(f=cmd_report)
    s = sub.add_parser("titles"); s.add_argument("year"); s.add_argument("deck"); s.set_defaults(f=cmd_titles)
    a = p.parse_args(argv)
    a.f(a)


if __name__ == "__main__":
    sys.exit(main())
