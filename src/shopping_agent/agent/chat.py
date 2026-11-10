"""Conversación por texto con el agente y el LLM local.

Uso::

    python -m shopping_agent.agent.chat                       # interactivo
    python -m shopping_agent.agent.chat --script turnos.txt --restore --out results/compra

``--script`` lee un mensaje de usuario por línea; ``--out`` guarda la transcripción
(``.json`` y ``.md``) con las operaciones ejecutadas y el estado final de la tienda.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from shopping_agent.agent.graph import build_graph
from shopping_agent.agent.llm import LocalLLM
from shopping_agent.agent.memory import open_memory
from shopping_agent.agent.search import DEFAULT_DATA_DIR, CatalogSearch
from shopping_agent.agent.session import ShoppingSession, TurnResult
from shopping_agent.gpu import process_vram_mib
from shopping_agent.store.db import connect, restore
from shopping_agent.store.ops import format_eur


def store_snapshot(db_path: Path, seed_path: Path) -> dict[str, Any]:
    """Pedidos, carritos y cambios de inventario respecto a la tienda inicial."""
    conn = connect(db_path)
    try:
        snapshot: dict[str, Any] = {
            "orders": [
                {"order_id": order_id, "quote_id": quote_id, "total_cents": total}
                for order_id, quote_id, total in conn.execute("SELECT order_id, quote_id, total_cents FROM orders")
            ],
            "order_items": [
                {"order_id": order_id, "product_id": product_id, "quantity": quantity, "unit_price_cents": price}
                for order_id, product_id, quantity, price in conn.execute(
                    "SELECT order_id, product_id, quantity, unit_price_cents FROM order_items"
                )
            ],
            "cart_items": [
                {"cart_id": cart_id, "product_id": product_id, "quantity": quantity}
                for cart_id, product_id, quantity in conn.execute("SELECT cart_id, product_id, quantity FROM cart_items")
            ],
        }
        if seed_path.exists():
            conn.execute("ATTACH DATABASE ? AS seed", (str(seed_path),))
            snapshot["inventory_changes"] = [
                {"product_id": product_id, "initial_stock": initial, "stock": stock}
                for product_id, initial, stock in conn.execute(
                    "SELECT inv.product_id, seed.inventory.stock, inv.stock FROM inventory AS inv "
                    "JOIN seed.inventory USING (product_id) WHERE inv.stock != seed.inventory.stock"
                )
            ]
        return snapshot
    finally:
        conn.close()


def _turn_record(turn: TurnResult, llm_calls: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "user": turn.user,
        "assistant": turn.response,
        "awaiting_confirmation": turn.awaiting_confirmation,
        "seconds": round(turn.seconds, 2),
        "llm_calls": len(llm_calls),
        "llm_seconds": round(sum(call["seconds"] for call in llm_calls), 2),
        "prompt_tokens": sum(call["prompt_tokens"] or 0 for call in llm_calls),
        "completion_tokens": sum(call["completion_tokens"] or 0 for call in llm_calls),
        "operations": [
            {key: operation.get(key) for key in ("tool", "args", "reason", "ok", "summary", "issues")}
            for operation in turn.operations
        ],
    }


def to_markdown(record: dict[str, Any]) -> str:
    model = record["model"]
    lines = [
        "# Transcripción de una compra por texto",
        "",
        f"- Fecha: {record['date']}",
        f"- Modelo: `{model['file']}` ({model['size_gb']} GB), contexto {model['n_ctx']} tokens",
        f"- Carga: catálogo y recuperadores {record['load']['search_seconds']} s, LLM {model['load_seconds']} s",
        f"- VRAM del proceso: {record['load']['vram_search_mib']} MiB con el recuperador denso, "
        f"{record['load']['vram_total_mib']} MiB con el LLM cargado",
        f"- Memoria del agente: {record['memory_backend']}; hilo `{record['thread_id']}`",
        "",
    ]
    for number, turn in enumerate(record["turns"], 1):
        lines += [f"## Turno {number} ({turn['seconds']} s, {turn['llm_calls']} llamadas al LLM)", ""]
        lines += [f"**Usuario:** {turn['user']}", ""]
        for operation in turn["operations"]:
            args = ", ".join(f"{key}={json.dumps(value, ensure_ascii=False)}" for key, value in operation["args"].items())
            status = "OK" if operation["ok"] else "RECHAZADO"
            summary = " ".join(str(operation["summary"]).split())
            if len(summary) > 300:
                summary = summary[:300] + "…"
            lines.append(f"- `{operation['tool']}({args})` → {status}: {summary}")
        if turn["operations"]:
            lines.append("")
        waiting = " *(esperando confirmación)*" if turn["awaiting_confirmation"] else ""
        lines += [f"**Agente:** {turn['assistant']}{waiting}", ""]
    store = record["store"]
    lines += ["## Estado final de la tienda", ""]
    for order in store["orders"]:
        lines.append(f"- Pedido {order['order_id']}: total {format_eur(order['total_cents'])}")
    for item in store["order_items"]:
        lines.append(
            f"  - pedido {item['order_id']}: {item['quantity']} × `{item['product_id']}` a {format_eur(item['unit_price_cents'])}"
        )
    for change in store.get("inventory_changes", []):
        lines.append(f"- Inventario `{change['product_id']}`: {change['initial_stock']} → {change['stock']}")
    lines.append(f"- Líneas de carrito pendientes: {len(store['cart_items'])}")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Conversación por texto con el agente de compras.")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--db", type=Path, default=None, help="tienda SQLite (por defecto, data/store.sqlite)")
    parser.add_argument("--thread", default=None, help="hilo de conversación; se reanuda si ya existe")
    parser.add_argument("--user", default="anonimo")
    parser.add_argument("--script", type=Path, default=None, help="archivo con un mensaje de usuario por línea")
    parser.add_argument("--out", type=Path, default=None, help="prefijo de la transcripción (.json y .md)")
    parser.add_argument("--restore", action="store_true", help="devuelve la tienda a su estado inicial antes de empezar")
    parser.add_argument("--n-ctx", type=int, default=8192)
    args = parser.parse_args()

    db_path = args.db or args.data / "store.sqlite"
    seed_path = args.data / "store_seed.sqlite"
    if args.restore:
        restore(seed_path, db_path)
    thread_id = args.thread or f"chat-{uuid.uuid4().hex[:8]}"

    start = time.perf_counter()
    search = CatalogSearch.from_dir(args.data)
    search.rank("calentamiento")  # la primera consulta carga el modelo denso en la GPU
    search_seconds = time.perf_counter() - start
    vram_search = process_vram_mib()
    llm = LocalLLM(n_ctx=args.n_ctx)
    vram_total = process_vram_mib()
    print(
        f"[modelo {llm.model_path.name} cargado en {llm.load_seconds:.1f} s; VRAM del proceso: {vram_total} MiB]",
        file=sys.stderr,
    )

    scripted = None
    if args.script:
        scripted = [line.strip() for line in args.script.read_text(encoding="utf-8").splitlines() if line.strip()]

    turns: list[dict[str, Any]] = []
    with open_memory() as memory:
        graph = build_graph(llm, search, db_path, memory.checkpointer, memory.store)
        session = ShoppingSession(graph, thread_id, args.user)
        print(f"[hilo {thread_id}; memoria: {memory.backend}; escribe 'salir' para terminar]", file=sys.stderr)
        while True:
            if scripted is not None:
                if not scripted:
                    break
                text = scripted.pop(0)
                print(f"tú> {text}")
            else:
                try:
                    text = input("tú> ").strip()
                except (EOFError, KeyboardInterrupt):
                    break
                if text.lower() in ("salir", "exit", "quit"):
                    break
            done = len(llm.calls)
            turn = session.send(text)
            turns.append(_turn_record(turn, llm.calls[done:]))
            print(f"agente> {turn.response}\n   [{turn.seconds:.1f} s, {len(llm.calls) - done} llamadas al LLM]")
        final = session.state

        if args.out:
            sizes = [path.stat().st_size for path in llm.model_path.parent.glob(llm.model_path.name.split("-0000")[0] + "*")]
            record = {
                "date": datetime.now().isoformat(timespec="seconds"),
                "model": {
                    "file": llm.model_path.name,
                    "size_gb": round(sum(sizes) / 1e9, 2),
                    "n_ctx": args.n_ctx,
                    "load_seconds": round(llm.load_seconds, 1),
                },
                "load": {
                    "search_seconds": round(search_seconds, 1),
                    "vram_search_mib": vram_search,
                    "vram_total_mib": vram_total,
                },
                "memory_backend": memory.backend,
                "thread_id": thread_id,
                "turns": turns,
                "final_state": {
                    key: final.get(key) for key in ("budget_cents", "preferences", "cart", "quote", "order")
                },
                "store": store_snapshot(db_path, seed_path),
            }
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.with_suffix(".json").write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
            args.out.with_suffix(".md").write_text(to_markdown(record), encoding="utf-8")
            print(f"[transcripción en {args.out.with_suffix('.json')} y {args.out.with_suffix('.md')}]", file=sys.stderr)


if __name__ == "__main__":
    main()
