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


VARIANT = "sage_exact"


def save_weights(data_dir, model: Reranker) -> None:
    train.save_reranker(train.weights_path(data_dir, VARIANT), model, make_development().graph)


def load_reranker(data_dir, bm25, dense) -> GraphReranker:
    return GraphReranker.load(data_dir, VARIANT, bm25, dense, "cpu")


def test_saved_reranker_reorders_the_hybrid_candidates(tmp_path):
    bm25, dense = BM25Retriever(DOCS), FakeDense()
    stage = first_stage(["producto azul"], bm25, dense)
    hybrid = stage.top(6)[0]

    save_weights(tmp_path, Reranker(ALL))
    untrained = load_reranker(tmp_path, bm25, dense)
    rows = untrained.rank("producto azul", top=6)
    assert untrained.variant == VARIANT
    assert sorted(rows) == sorted(hybrid)  # los mismos candidatos, en otro orden
    by_cosine = hybrid[np.argsort(-stage.dense[0, hybrid], kind="stable")]
    assert rows.tolist() == by_cosine.tolist()  # sin entrenar ordena por el coseno

    save_weights(tmp_path, trained_like(ALL))
    trained = load_reranker(tmp_path, bm25, dense)
    assert sorted(trained.rank("producto azul", top=6)) == sorted(hybrid)
    assert trained.graph["query"].num_nodes == QUERIES  # la consulta no se queda en el grafo


def test_reranker_load_explains_what_is_missing(tmp_path):
    bm25, dense = BM25Retriever(DOCS), FakeDense()
    with pytest.raises(FileNotFoundError, match=f"shopping_agent.retrieval.train --variant {VARIANT}"):
        load_reranker(tmp_path, bm25, dense)

    save_weights(tmp_path, Reranker(ALL))
    dense.doc_embeddings = DOC_EMBEDDINGS[:-1]
    with pytest.raises(ValueError, match="otro catálogo"):
        load_reranker(tmp_path, bm25, dense)


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

    variant = "inverso"

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
    assert without.reranker_name is None and with_reranker.reranker_name == "inverso" and not reranker.calls
    assert with_reranker.rank("Producto Azul", top=5) == plain[::-1]
    assert reranker.calls == [("producto azul", 5)]  # la consulta le llega en minúsculas
    assert with_reranker.rank("   ") == [] and len(reranker.calls) == 1


def test_search_with_the_real_reranker_keeps_the_hybrid_candidates(tmp_path):
    catalog, dense = search_catalog(), FakeDense()
    without = CatalogSearch.from_catalog(catalog, dense)
    save_weights(tmp_path, trained_like(ALL))
    reranker = load_reranker(tmp_path, without.bm25, dense)
    with_reranker = CatalogSearch(catalog, without.bm25, dense, reranker)

    assert sorted(with_reranker.rank("producto azul", top=6)) == sorted(without.rank("producto azul", top=6))


@pytest.mark.parametrize(("value", "expected"), [("sage", "sage"), (" OFF ", "off"), ("Control", "control")])
def test_reranker_choice_reads_the_environment(monkeypatch, value, expected):
    monkeypatch.setenv(search.RERANKER_ENV, value)
    assert search.reranker_choice() == expected


def test_reranker_choice_defaults_to_the_control_without_graph(monkeypatch):
    monkeypatch.delenv(search.RERANKER_ENV, raising=False)
    assert search.reranker_choice() == search.RERANKER_DEFAULT == train.DEFAULT_VARIANT == "control"
    assert train.VARIANTS[train.DEFAULT_VARIANT].relations == ()
    monkeypatch.setenv(search.RERANKER_ENV, "")
    assert search.reranker_choice() == "control"


def test_search_rejects_an_unknown_reranker_before_loading_anything(tmp_path):
    with pytest.raises(ValueError, match="off, control"):
        CatalogSearch.from_dir(tmp_path, reranker="quizá")
