import uuid
from typing import TypedDict

import pytest
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.store.memory import InMemoryStore

from shopping_agent.agent.memory import PG_URL_ENV, open_memory


class Counter(TypedDict):
    count: int


def counter_graph(memory):
    builder = StateGraph(Counter)
    builder.add_node("sumar", lambda state: {"count": state.get("count", 0) + 1})
    builder.add_edge(START, "sumar")
    builder.add_edge("sumar", END)
    return builder.compile(checkpointer=memory.checkpointer, store=memory.store)


def test_without_url_memory_is_volatile(monkeypatch):
    monkeypatch.delenv(PG_URL_ENV, raising=False)
    with open_memory() as memory:
        assert memory.backend == "memoria"
        assert isinstance(memory.checkpointer, InMemorySaver)
        assert isinstance(memory.store, InMemoryStore)
        config = {"configurable": {"thread_id": "t"}}
        graph = counter_graph(memory)
        graph.invoke({}, config)
        assert graph.invoke({}, config)["count"] == 2


def test_postgres_checkpoints_survive_reopening(pg_url):
    thread_id = f"test-{uuid.uuid4().hex}"
    config = {"configurable": {"thread_id": thread_id}}
    try:
        with open_memory(pg_url) as memory:
            assert memory.backend == "postgres"
            assert counter_graph(memory).invoke({}, config)["count"] == 1
        # Otra "sesión": pool y grafo nuevos, mismo hilo de conversación.
        with open_memory(pg_url) as memory:
            graph = counter_graph(memory)
            assert graph.get_state(config).values["count"] == 1
            assert graph.invoke({}, config)["count"] == 2
    finally:
        with open_memory(pg_url) as memory:
            memory.checkpointer.delete_thread(thread_id)
            assert counter_graph(memory).get_state(config).values == {}


def test_postgres_store_survives_reopening(pg_url):
    namespace = ("test", uuid.uuid4().hex)
    try:
        with open_memory(pg_url) as memory:
            memory.store.put(namespace, "perfil", {"preferencias": ["color negro"]})
        with open_memory(pg_url) as memory:
            item = memory.store.get(namespace, "perfil")
            assert item is not None and item.value == {"preferencias": ["color negro"]}
    finally:
        with open_memory(pg_url) as memory:
            memory.store.delete(namespace, "perfil")
            assert memory.store.get(namespace, "perfil") is None


def test_unreachable_postgres_raises():
    with pytest.raises(Exception):
        with open_memory("postgresql://nadie:nada@127.0.0.1:9/nada?connect_timeout=1"):
            pass
