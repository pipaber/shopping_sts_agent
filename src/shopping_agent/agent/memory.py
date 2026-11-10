"""Memoria del agente: checkpoints (corto plazo) y Store (entre conversaciones).

Se guardan en Postgres: ``PostgresSaver`` y ``PostgresStore`` sobre un mismo pool
de conexiones, con la URL de ``SHOPPING_AGENT_PG_URL``; las tablas se crean la
primera vez. Sin esa variable no se abre nada: quedarse sin persistencia sin
notarlo sería peor que un error. La memoria volátil (se pierde al cerrar el
proceso) existe para pruebas y hay que pedirla de forma explícita.

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

from typing import TYPE_CHECKING

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.store.base import BaseStore

if TYPE_CHECKING:  # psycopg solo hace falta si de verdad se usa Postgres
    from psycopg import Connection
    from psycopg.rows import DictRow
    from psycopg_pool import ConnectionPool

PG_URL_ENV = "SHOPPING_AGENT_PG_URL"
POSTGRES, VOLATILE = "postgres", "memoria volátil"
MISSING_URL_MESSAGE = (
    f"Falta la variable {PG_URL_ENV}: el agente guarda sus checkpoints y su Store en Postgres. "
    "Defínela en el .env (el README explica cómo levantar Postgres en «Memoria del agente (Postgres)»). "
    "Si quieres trabajar a propósito sin persistencia, pide la memoria volátil: la opción "
    "--volatile-memory de los comandos o open_memory(volatile=True)."
)

log = logging.getLogger(__name__)


class MemoryNotConfigured(RuntimeError):
    """No hay URL de Postgres y no se ha pedido la memoria volátil."""


@dataclass(frozen=True)
class Memory:
    checkpointer: BaseCheckpointSaver
    store: BaseStore
    backend: str  # POSTGRES o VOLATILE; queda anotado en las transcripciones


@contextmanager
def open_memory(url: str | None = None, *, volatile: bool = False, pool_size: int = 4) -> Iterator[Memory]:
    """Abre la memoria del agente y la cierra al salir del bloque.

    ``url`` tiene prioridad sobre la variable de entorno. Sin URL se lanza
    :class:`MemoryNotConfigured`, y si hay URL pero Postgres no responde se lanza
    el error de conexión. ``volatile=True`` pide a propósito la memoria en proceso,
    haya o no URL.
    """
    if volatile:
        from langgraph.checkpoint.memory import InMemorySaver
        from langgraph.store.memory import InMemoryStore

        log.warning("Memoria volátil pedida de forma explícita: nada se conserva al cerrar el proceso.")
        yield Memory(InMemorySaver(), InMemoryStore(), VOLATILE)
        return

    url = url or os.environ.get(PG_URL_ENV)
    if not url:
        raise MemoryNotConfigured(MISSING_URL_MESSAGE)

    from langgraph.checkpoint.postgres import PostgresSaver
    from langgraph.store.postgres import PostgresStore

    pool = _open_pool(url, pool_size)
    try:
        checkpointer = PostgresSaver(pool)
        checkpointer.setup()
        store = PostgresStore(pool)
        store.setup()
        yield Memory(checkpointer, store, POSTGRES)
    finally:
        pool.close()


def _open_pool(url: str, pool_size: int) -> ConnectionPool[Connection[DictRow]]:
    """Pool compartido por los checkpoints y el Store, con los parámetros de conexión
    que piden ``PostgresSaver`` y ``PostgresStore``."""
    from psycopg.rows import dict_row
    from psycopg_pool import ConnectionPool

    pool: ConnectionPool[Connection[DictRow]] = ConnectionPool(
        url,
        min_size=1,
        max_size=pool_size,
        kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row},
        open=False,
    )
    pool.open(wait=True, timeout=10)
    return pool
