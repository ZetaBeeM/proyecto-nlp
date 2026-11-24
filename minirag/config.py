"""Configuración central. Todo parámetro ajustable vive aquí (o en variables de entorno)."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS_DIRS = {"2025": ROOT / "S2-2025", "2026": ROOT / "S2-2026"}
TOPICS_FILE = ROOT / "data" / "topics.json"
INDEX_DIR = ROOT / "index"
RESULTS_DIR = ROOT / "results"
EVAL_FILE = ROOT / "eval" / "questions.json"

# --- Modelos (Ollama local) ---
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
# qwen3:4b-instruct = Qwen3-4B (2507) sin modo thinking: rápido y determinista.
# Alternativas probadas: "qwen3:4b" (thinking, ~10x más lento) y "gemma3:4b".
LLM_MODEL = os.environ.get("MINIRAG_LLM", "qwen3:4b-instruct")
EMBED_MODEL = os.environ.get("MINIRAG_EMBED", "bge-m3")  # multilingüe (es/en)
LLM_TEMPERATURE = 0.0
LLM_NUM_CTX = 8192

# --- Chunking ---
CHUNK_MAX_WORDS = 180  # las slides son cortas: se agrupan slides consecutivas
CHUNK_OVERLAP_SLIDES = 1

# --- Retrieval ---
TOP_K = 6
RRF_K = 60
# Si el mejor fragmento no supera este umbral (similitud coseno del retriever denso),
# el sistema se abstiene sin llamar al LLM. Calibrado con eval/questions.json.
MIN_DENSE_SCORE = 0.45
