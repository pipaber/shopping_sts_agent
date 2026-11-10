"""El reranker ya entrenado y su interruptor en la búsqueda del agente."""

import numpy as np
import pandas as pd
import pytest
from synthetic_graph import ALL, BRANDS, DOC_EMBEDDINGS, PRODUCTS, QUERIES, FakeDense, make_development, trained_like

from shopping_agent.agent import search
from shopping_agent.agent.search import CatalogSearch
from shopping_agent.retrieval import train
from shopping_agent.retrieval.first_stage import first_stage
from shopping_agent.retrieval.gnn import Reranker
from shopping_agent.retrieval.reranker import GraphReranker
from shopping_agent.retrieval.retrievers import BM25Retriever

DOCS = [f"producto {row} azul" if row % 2 else f"producto {row} rojo" for row in range(PRODUCTS)]


def saved_reranker(tmp_path, model: Reranker):
    path = tmp_path / train.WEIGHTS_FILE
    train.save_reranker(path, model, make_development().graph)
    return path


def test_saved_reranker_reorders_the_hybrid_candidates(tmp_path):
    bm25, dense = BM25Retriever(DOCS), FakeDense()
    stage = first_stage(["producto azul"], bm25, dense)
    hybrid = stage.top(6)[0]

    untrained = GraphReranker.load(saved_reranker(tmp_path, Reranker(ALL)), bm25, dense, "cpu")
    rows = untrained.rank("producto azul", top=6)
    assert sorted(rows) == sorted(hybrid)  # los mismos candidatos, en otro orden
    by_cosine = hybrid[np.argsort(-stage.dense[0, hybrid], kind="stable")]
    assert rows.tolist() == by_cosine.tolist()  # sin entrenar ordena por el coseno

    trained = GraphReranker.load(saved_reranker(tmp_path, trained_like(ALL)), bm25, dense, "cpu")
    assert sorted(trained.rank("producto azul", top=6)) == sorted(hybrid)
    assert len(trained.graph.query_x) == QUERIES  # la consulta no se queda en el grafo


def test_reranker_load_explains_what_is_missing(tmp_path):
    bm25, dense = BM25Retriever(DOCS), FakeDense()
    with pytest.raises(FileNotFoundError, match="shopping_agent.retrieval.train"):
        GraphReranker.load(tmp_path / "no_existe.pt", bm25, dense, "cpu")

    path = saved_reranker(tmp_path, Reranker(ALL))
    dense.doc_embeddings = DOC_EMBEDDINGS[:-1]
    with pytest.raises(ValueError, match="otro catálogo"):
        GraphReranker.load(path, bm25, dense, "cpu")


def search_catalog() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "product_id": [f"p{row}" for row in range(PRODUCTS)],
            "product_title": DOCS,
            "product_brand": BRANDS,
            "product_color": None,
            "product_bullet_point": None,
            "product_description": None,
        }
    )


class ReversingReranker:
    """Devuelve los primeros del híbrido en orden inverso."""

    def __init__(self, hybrid: CatalogSearch):
        self.hybrid = hybrid
        self.calls = []

    def rank(self, query, top):
        self.calls.append((query, top))
        rows = [self.hybrid.product_ids.index(product_id) for product_id in self.hybrid.rank(query, top)]
        return np.array(rows[::-1])


def test_search_uses_the_reranker_only_when_it_is_enabled():
    catalog, dense = search_catalog(), FakeDense()
    without = CatalogSearch.from_catalog(catalog, dense)
    reranker = ReversingReranker(without)
    with_reranker = CatalogSearch(catalog, without.bm25, dense, reranker)

    plain = without.rank("Producto Azul", top=5)
    assert without.reranker is None and not reranker.calls
    assert with_reranker.rank("Producto Azul", top=5) == plain[::-1]
    assert reranker.calls == [("producto azul", 5)]  # la consulta le llega en minúsculas
    assert with_reranker.rank("   ") == [] and len(reranker.calls) == 1


def test_search_with_the_real_reranker_keeps_the_hybrid_candidates(tmp_path):
    catalog, dense = search_catalog(), FakeDense()
    without = CatalogSearch.from_catalog(catalog, dense)
    reranker = GraphReranker.load(saved_reranker(tmp_path, trained_like(ALL)), without.bm25, dense, "cpu")
    with_reranker = CatalogSearch(catalog, without.bm25, dense, reranker)

    assert sorted(with_reranker.rank("producto azul", top=6)) == sorted(without.rank("producto azul", top=6))


@pytest.mark.parametrize(("value", "expected"), [("on", True), ("1", True), (" OFF ", False), ("0", False)])
def test_reranker_switch_reads_the_environment(monkeypatch, value, expected):
    monkeypatch.setenv(search.RERANKER_ENV, value)
    assert search.reranker_enabled() is expected


def test_reranker_switch_default_and_invalid_values(monkeypatch):
    monkeypatch.delenv(search.RERANKER_ENV, raising=False)
    assert search.reranker_enabled() is search.RERANKER_DEFAULT
    monkeypatch.setenv(search.RERANKER_ENV, "quizá")
    with pytest.raises(ValueError, match=search.RERANKER_ENV):
        search.reranker_enabled()
