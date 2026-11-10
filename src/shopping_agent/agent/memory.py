"""Memoria del agente: checkpoints (corto plazo) y Store (entre conversaciones).

Con ``SHOPPING_AGENT_PG_URL`` definida se usan ``PostgresSaver`` y
``PostgresStore`` sobre un mismo pool de conexiones; las tablas se crean la
primera vez. Sin la variable se devuelven los equivalentes en memoria, que sirven
para pruebas y para trabajar sin Postgres, pero se pierden al cerrar el proceso.

Uso::

    with open_memory() as memory:
        graph = builder.compile(checkpointer=memory.checkpointer, store=memory.store)
"""

from __future__ import annotations

import logging
import os
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.store.base import BaseStore

PG_URL_ENV = "SHOPPING_AGENT_PG_URL"

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Memory:
    checkpointer: BaseCheckpointSaver
    store: BaseStore
    backend: str  # "postgres" o "memoria"


@contextmanager
def open_memory(url: str | None = None, *, pool_size: int = 4) -> Iterator[Memory]:
    """Abre la memoria del agente y la cierra al salir del bloque.

    ``url`` tiene prioridad sobre la variable de entorno. Si hay URL y Postgres no
    responde, se lanza el error: perder la persistencia en silencio sería peor.
    """
    url = url or os.environ.get(PG_URL_ENV)
    if not url:
        from langgraph.checkpoint.memory import InMemorySaver
        from langgraph.store.memory import InMemoryStore

        log.warning("%s no está definida: la memoria del agente es volátil.", PG_URL_ENV)
        yield Memory(InMemorySaver(), InMemoryStore(), "memoria")
        return

    from langgraph.checkpoint.postgres import PostgresSaver
    from langgraph.store.postgres import PostgresStore
    from psycopg.rows import dict_row
    from psycopg_pool import ConnectionPool

    # Los parámetros de conexión son los que piden PostgresSaver y PostgresStore.
    pool = ConnectionPool(
        url,
        min_size=1,
        max_size=pool_size,
        kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row},
        open=False,
    )
    pool.open(wait=True, timeout=10)
    try:
        checkpointer = PostgresSaver(pool)
        checkpointer.setup()
        store = PostgresStore(pool)
        store.setup()
        yield Memory(checkpointer, store, "postgres")
    finally:
        pool.close()
