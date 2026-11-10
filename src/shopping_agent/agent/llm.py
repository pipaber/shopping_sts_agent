"""LLM del agente: una decisión estructurada por llamada.

El grafo solo necesita ``decide(messages, schema) -> dict``. :class:`LocalLLM` lo
resuelve con un GGUF servido por ``llama-cpp-python``; el esquema JSON se
convierte en una gramática, de modo que el modelo no puede emitir una llamada a
herramienta mal formada. :class:`ScriptedLLM` devuelve decisiones escritas de
antemano para probar el grafo sin GPU.
"""

from __future__ import annotations

import json
import os
import re
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol, cast

# Modelo por defecto (ver documentation/PLAN.md). Se cambia con variables de entorno.
DEFAULT_REPO = "Qwen/Qwen2.5-7B-Instruct-GGUF"
DEFAULT_FILE = "qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf"
REPO_ENV = "SHOPPING_AGENT_LLM_REPO"
FILE_ENV = "SHOPPING_AGENT_LLM_FILE"
PATH_ENV = "SHOPPING_AGENT_LLM_PATH"

_SPLIT = re.compile(r"-(\d{5})-of-(\d{5})\.gguf$")

Messages = list[dict[str, str]]


class LLMError(RuntimeError):
    """El modelo no devolvió una decisión utilizable."""


class DecisionLLM(Protocol):
    def decide(self, messages: Messages, schema: dict[str, Any]) -> dict[str, Any]: ...


def resolve_model_path() -> Path:
    """Ruta local del GGUF: la indicada en el entorno o la descarga de Hugging Face.

    Si el fichero está partido (``-00001-of-0000N``) se descargan todas las partes;
    llama.cpp las carga a partir de la primera.
    """
    local = os.environ.get(PATH_ENV)
    if local:
        return Path(local)

    from huggingface_hub import hf_hub_download

    repo = os.environ.get(REPO_ENV, DEFAULT_REPO)
    filename = os.environ.get(FILE_ENV, DEFAULT_FILE)
    match = _SPLIT.search(filename)
    parts = [filename]
    if match:
        total = int(match.group(2))
        parts = [_SPLIT.sub(f"-{part:05d}-of-{total:05d}.gguf", filename) for part in range(1, total + 1)]
    paths = [Path(hf_hub_download(repo, part)) for part in parts]
    return paths[0]


class LocalLLM:
    """Qwen en GGUF con todas las capas en la GPU y salida restringida por gramática."""

    def __init__(
        self,
        model_path: Path | str | None = None,
        n_ctx: int = 8192,
        n_gpu_layers: int = -1,
        max_tokens: int = 400,
        seed: int = 0,
        verbose: bool = False,
    ) -> None:
        from llama_cpp import Llama

        self.model_path = Path(model_path) if model_path else resolve_model_path()
        self.max_tokens = max_tokens
        start = time.perf_counter()
        self.llm = Llama(
            model_path=str(self.model_path),
            n_ctx=n_ctx,
            n_gpu_layers=n_gpu_layers,
            seed=seed,
            verbose=verbose,
        )
        self.load_seconds = time.perf_counter() - start
        self.calls: list[dict[str, Any]] = []  # tiempos y tokens de cada decisión

    def decide(self, messages: Messages, schema: dict[str, Any]) -> dict[str, Any]:
        start = time.perf_counter()
        # llama-cpp tipa los mensajes y la respuesta con sus propias clases; aquí se
        # usan como los diccionarios que son (sin ``stream`` la respuesta es una sola).
        output = cast(
            dict[str, Any],
            self.llm.create_chat_completion(
                messages=cast(Any, messages),
                response_format={"type": "json_object", "schema": schema},
                temperature=0.0,
                max_tokens=self.max_tokens,
            ),
        )
        elapsed = time.perf_counter() - start
        choice = output["choices"][0]
        usage = output.get("usage", {})
        self.calls.append(
            {
                "seconds": elapsed,
                "prompt_tokens": usage.get("prompt_tokens"),
                "completion_tokens": usage.get("completion_tokens"),
            }
        )
        text = choice["message"]["content"] or ""
        try:
            decision = json.loads(text)
        except json.JSONDecodeError as error:
            raise LLMError(f"JSON incompleto (finish_reason={choice.get('finish_reason')}): {text[:200]}") from error
        if not isinstance(decision, dict):
            raise LLMError(f"Se esperaba un objeto JSON: {text[:200]}")
        return decision


Scripted = dict[str, Any] | Callable[[Messages, dict[str, Any]], dict[str, Any]]


class ScriptedLLM:
    """Devuelve, en orden, las decisiones de un guion. Guarda lo que recibió."""

    def __init__(self, script: list[Scripted]) -> None:
        self.script = list(script)
        self.calls: list[tuple[Messages, dict[str, Any]]] = []

    def extend(self, script: list[Scripted]) -> None:
        self.script.extend(script)

    @property
    def remaining(self) -> int:
        return len(self.script)

    def decide(self, messages: Messages, schema: dict[str, Any]) -> dict[str, Any]:
        self.calls.append((messages, schema))
        if not self.script:
            raise AssertionError("El guion del LLM se quedó sin decisiones")
        step = self.script.pop(0)
        return step(messages, schema) if callable(step) else dict(step)
