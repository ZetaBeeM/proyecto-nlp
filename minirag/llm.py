"""Cliente mínimo para la API REST de Ollama (sin dependencias extra)."""
from __future__ import annotations

import requests

from . import config


class OllamaError(RuntimeError):
    pass


def _post(path: str, payload: dict, timeout=300) -> dict:
    try:
        r = requests.post(f"{config.OLLAMA_URL}{path}", json=payload, timeout=timeout)
    except requests.ConnectionError as e:
        raise OllamaError(f"No se pudo conectar a Ollama en {config.OLLAMA_URL}. "
                          "¿Está corriendo `ollama serve`?") from e
    if r.status_code != 200:
        raise OllamaError(f"Ollama {path} -> {r.status_code}: {r.text[:300]}")
    return r.json()


def embed(texts: list[str], model: str | None = None) -> list[list[float]]:
    return _post("/api/embed", {"model": model or config.EMBED_MODEL, "input": texts})["embeddings"]


def chat(system: str, user: str, model: str | None = None) -> str:
    model = model or config.LLM_MODEL
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "stream": False,
        "options": {"temperature": config.LLM_TEMPERATURE, "num_ctx": config.LLM_NUM_CTX, "seed": 0},
    }
    if model.startswith("qwen3") and "instruct" not in model:
        # qwen3:4b (2507) es un modelo "thinking-only": no se puede desactivar el razonamiento.
        # Con think=True Ollama lo separa en message.thinking y `content` queda limpio.
        payload["think"] = True
    content = _post("/api/chat", payload)["message"]["content"]
    # defensa extra: algunos modelos devuelven el razonamiento inline terminado en </think>
    return content.split("</think>")[-1].strip()
