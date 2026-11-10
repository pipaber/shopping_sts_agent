"""Lo que los nodos necesitan de fuera del grafo: el LLM, la búsqueda en el
catálogo, la tienda y el Store de preferencias.

Se construye una vez en ``build_graph`` y se le pasa a cada nodo, de modo que un
nodo se puede probar por separado con dependencias de prueba.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore

from shopping_agent.agent.llm import DecisionLLM
from shopping_agent.agent.search import CatalogSearch
from shopping_agent.agent.state import Candidate, CartLine, PricedLine
from shopping_agent.store import ops
from shopping_agent.store.db import connect

PROFILE_NAMESPACE = "usuarios"
PROFILE_KEY = "perfil"


def cart_id(config: RunnableConfig) -> str:
    """El carrito es el del hilo de conversación."""
    return str(config.get("configurable", {})["thread_id"])


def user_id(config: RunnableConfig) -> str:
    return str(config.get("configurable", {}).get("user_id", "anonimo"))


@dataclass(frozen=True)
class Deps:
    llm: DecisionLLM
    search: CatalogSearch
    db_path: Path | str  # tienda SQLite
    store: BaseStore | None = None  # memoria entre conversaciones

    @contextmanager
    def shop(self) -> Iterator[sqlite3.Connection]:
        conn = connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    # --- Tienda y catálogo juntos: precios y existencias con su título o evidencia ---

    def priced_line(self, item: Mapping[str, Any]) -> PricedLine:
        return PricedLine(
            product_id=item["product_id"],
            title=self.search.title(item["product_id"]),
            quantity=item["quantity"],
            unit_price_cents=item["unit_price_cents"],
            subtotal_cents=item["subtotal_cents"],
        )

    def cart_line(self, item: Mapping[str, Any]) -> CartLine:
        return CartLine(**self.priced_line(item), stock=item["stock"])

    def cart(self, conn: sqlite3.Connection, cart: str) -> list[CartLine]:
        return [self.cart_line(item) for item in ops.get_cart(conn, cart).data["items"]]

    def priced(self, conn: sqlite3.Connection, product_id: str, *chars: int) -> Candidate:
        """Evidencia del catálogo con el precio y las existencias de ahora. ``chars``
        son los límites de viñetas y descripción (por defecto, los de la búsqueda)."""
        offer = ops.price_and_stock(conn, product_id).data
        evidence = self.search.evidence(product_id, *chars)
        return Candidate(**evidence, price_cents=offer["price_cents"], stock=offer["stock"])

    def candidate(self, conn: sqlite3.Connection, product_id: str) -> Candidate | None:
        """``None`` si el producto no está en el catálogo o no está en la tienda."""
        if product_id not in self.search or not ops.price_and_stock(conn, product_id).ok:
            return None
        return self.priced(conn, product_id)

    # --- Preferencias del usuario ---

    def saved_preferences(self, user: str) -> list[str] | None:
        if self.store is None:
            return None
        profile = self.store.get((PROFILE_NAMESPACE, user), PROFILE_KEY)
        return None if profile is None else list(profile.value.get("preferencias", []))

    def save_preferences(self, user: str, preferences: list[str]) -> None:
        if self.store is not None:
            self.store.put((PROFILE_NAMESPACE, user), PROFILE_KEY, {"preferencias": preferences})
