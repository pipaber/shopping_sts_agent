"""Conversación por texto con el agente y el LLM local.

Uso::

    python -m shopping_agent.agent.chat                       # interactivo
    python -m shopping_agent.agent.chat --script turnos.txt --restore --out results/compra

``--script`` lee un mensaje de usuario por línea; ``--out`` guarda la transcripción
(``.json`` y ``.md``) con las operaciones ejecutadas y el estado final de la tienda.
La memoria del agente va en Postgres (``SHOPPING_AGENT_PG_URL``); ``--volatile-memory``
la sustituye a propósito por una que se pierde al terminar.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from shopping_agent.agent.graph import build_graph
from shopping_agent.agent.llm import LocalLLM
from shopping_agent.agent.memory import MemoryNotConfigured, open_memory
from shopping_agent.agent.report import operation_lines, operation_records, store_lines, store_snapshot
from shopping_agent.agent.search import DEFAULT_DATA_DIR, CatalogSearch
from shopping_agent.agent.session import ShoppingSession, TurnResult
from shopping_agent.gpu import process_vram_mib
from shopping_agent.store.db import restore

EXIT_WORDS = ("salir", "exit", "quit")
FINAL_STATE_FIELDS = ("budget_cents", "preferences", "cart", "quote", "order")


@dataclass
class Models:
    """El recuperador y el LLM ya cargados, con lo que costó cargarlos."""

    search: CatalogSearch
    llm: LocalLLM
    search_seconds: float
    vram_search_mib: int | None
    vram_total_mib: int | None


def check_memory(volatile: bool) -> None:
    """Termina con el mensaje de error si falta Postgres, antes de cargar ningún modelo."""
    try:
        with open_memory(volatile=volatile):
            pass
    except MemoryNotConfigured as error:
        sys.exit(str(error))


def load_models(data_dir: Path, n_ctx: int) -> Models:
    start = time.perf_counter()
    search = CatalogSearch.from_dir(data_dir)
    search.rank("calentamiento")  # la primera consulta carga el modelo denso en la GPU
    search_seconds = time.perf_counter() - start
    vram_search = process_vram_mib()
    llm = LocalLLM(n_ctx=n_ctx)
    return Models(search, llm, search_seconds, vram_search, process_vram_mib())


def model_size_gb(model_path: Path) -> float:
    """Tamaño en disco del GGUF, sumando las partes si está partido."""
    parts = model_path.parent.glob(model_path.name.split("-0000")[0] + "*")
    return round(sum(part.stat().st_size for part in parts) / 1e9, 2)


def user_messages(script: Path | None) -> Iterator[str]:
    """Los mensajes del usuario: las líneas del guion o, sin guion, lo que escriba."""
    return _scripted(script) if script is not None else _typed()


def _scripted(script: Path) -> Iterator[str]:
    for line in filter(None, map(str.strip, script.read_text(encoding="utf-8").splitlines())):
        print(f"tú> {line}")
        yield line


def _typed() -> Iterator[str]:
    while True:
        try:
            text = input("tú> ").strip()
        except (EOFError, KeyboardInterrupt):
            return
        if text.lower() in EXIT_WORDS:
            return
        yield text


def turn_record(turn: TurnResult, llm_calls: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "user": turn.user,
        "assistant": turn.response,
        "awaiting_confirmation": turn.awaiting_confirmation,
        "seconds": round(turn.seconds, 2),
        "llm_calls": len(llm_calls),
        "llm_seconds": round(sum(call["seconds"] for call in llm_calls), 2),
        "prompt_tokens": sum(call["prompt_tokens"] or 0 for call in llm_calls),
        "completion_tokens": sum(call["completion_tokens"] or 0 for call in llm_calls),
        "operations": operation_records(turn.operations),
    }


def converse(session: ShoppingSession, llm: LocalLLM, messages: Iterator[str]) -> list[dict[str, Any]]:
    """Envía cada mensaje al agente, muestra la respuesta y devuelve los turnos."""
    turns = []
    for text in messages:
        done = len(llm.calls)
        turn = session.send(text)
        turns.append(turn_record(turn, llm.calls[done:]))
        print(f"agente> {turn.response}\n   [{turn.seconds:.1f} s, {len(llm.calls) - done} llamadas al LLM]")
    return turns


def conversation_record(models: Models, n_ctx: int, session: ShoppingSession, turns: list[dict[str, Any]]) -> dict[str, Any]:
    """Todo lo que se guarda de la conversación, salvo la memoria usada y la tienda."""
    final = session.state
    return {
        "date": datetime.now().isoformat(timespec="seconds"),
        "model": {
            "file": models.llm.model_path.name,
            "size_gb": model_size_gb(models.llm.model_path),
            "n_ctx": n_ctx,
            "load_seconds": round(models.llm.load_seconds, 1),
        },
        "load": {
            "reranker": models.search.reranker_name,
            "search_seconds": round(models.search_seconds, 1),
            "vram_search_mib": models.vram_search_mib,
            "vram_total_mib": models.vram_total_mib,
        },
        "thread_id": session.thread_id,
        "turns": turns,
        "final_state": {key: final.get(key) for key in FINAL_STATE_FIELDS},
    }


def to_markdown(record: dict[str, Any]) -> str:
    model, load = record["model"], record["load"]
    lines = [
        "# Transcripción de una compra por texto",
        "",
        f"- Fecha: {record['date']}",
        f"- Modelo: `{model['file']}` ({model['size_gb']} GB), contexto {model['n_ctx']} tokens",
        f"- Búsqueda: híbrido BM25 + denso, {'con reranker `%s`' % load['reranker'] if load['reranker'] else 'sin reranker'}",
        f"- Carga: catálogo y recuperadores {load['search_seconds']} s, LLM {model['load_seconds']} s",
        f"- VRAM del proceso: {load['vram_search_mib']} MiB con el recuperador denso, "
        f"{load['vram_total_mib']} MiB con el LLM cargado",
        f"- Memoria del agente: {record['memory_backend']}; hilo `{record['thread_id']}`",
        "",
    ]
    for number, turn in enumerate(record["turns"], 1):
        waiting = " *(esperando confirmación)*" if turn["awaiting_confirmation"] else ""
        lines += [f"## Turno {number} ({turn['seconds']} s, {turn['llm_calls']} llamadas al LLM)", ""]
        lines += [f"**Usuario:** {turn['user']}", ""]
        lines += operation_lines(turn["operations"])
        lines += [f"**Agente:** {turn['assistant']}{waiting}", ""]
    return "\n".join(lines + store_lines(record["store"])) + "\n"


def save(out: Path, record: dict[str, Any]) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.with_suffix(".json").write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    out.with_suffix(".md").write_text(to_markdown(record), encoding="utf-8")
    print(f"[transcripción en {out.with_suffix('.json')} y {out.with_suffix('.md')}]", file=sys.stderr)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Conversación por texto con el agente de compras.")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--db", type=Path, default=None, help="tienda SQLite (por defecto, data/store.sqlite)")
    parser.add_argument("--thread", default=None, help="hilo de conversación; se reanuda si ya existe")
    parser.add_argument("--user", default="anonimo")
    parser.add_argument("--script", type=Path, default=None, help="archivo con un mensaje de usuario por línea")
    parser.add_argument("--out", type=Path, default=None, help="prefijo de la transcripción (.json y .md)")
    parser.add_argument("--restore", action="store_true", help="devuelve la tienda a su estado inicial antes de empezar")
    parser.add_argument("--n-ctx", type=int, default=8192)
    parser.add_argument(
        "--volatile-memory", action="store_true",
        help="no usa Postgres: los checkpoints y el Store se pierden al terminar",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    check_memory(args.volatile_memory)
    db_path = args.db or args.data / "store.sqlite"
    seed_path = args.data / "store_seed.sqlite"
    if args.restore:
        restore(seed_path, db_path)
    thread_id = args.thread or f"chat-{uuid.uuid4().hex[:8]}"

    models = load_models(args.data, args.n_ctx)
    llm = models.llm
    print(
        f"[modelo {llm.model_path.name} cargado en {llm.load_seconds:.1f} s; VRAM del proceso: {models.vram_total_mib} MiB]",
        file=sys.stderr,
    )
    with open_memory(volatile=args.volatile_memory) as memory:
        graph = build_graph(llm, models.search, db_path, memory.checkpointer, memory.store)
        session = ShoppingSession(graph, thread_id, args.user)
        print(f"[hilo {thread_id}; memoria: {memory.backend}; escribe 'salir' para terminar]", file=sys.stderr)
        turns = converse(session, llm, user_messages(args.script))
        if args.out:
            record = conversation_record(models, args.n_ctx, session, turns)
            record.update(memory_backend=memory.backend, store=store_snapshot(db_path, seed_path))
            save(args.out, record)


if __name__ == "__main__":
    main()
