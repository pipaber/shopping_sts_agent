"""Partición de desarrollo y señales de la primera etapa (sin GPU ni modelos)."""

import numpy as np
import pandas as pd
import pytest

from shopping_agent.retrieval.dev_data import load_dev_data, split_queries
from shopping_agent.retrieval.first_stage import first_stage
from shopping_agent.retrieval.metrics import ndcg, ndcg_by_query
from shopping_agent.retrieval.retrievers import BM25Retriever, rrf


def test_split_is_disjoint_complete_and_reproducible():
    query_ids = list(range(100, 1600))
    fit, validation = split_queries(query_ids)
    assert len(fit) == 1200 and len(validation) == 300
    assert not set(fit) & set(validation) and set(fit) | set(validation) == set(query_ids)
    assert (fit, validation) == split_queries(query_ids[::-1])  # no depende del orden de entrada
    assert validation != split_queries(query_ids, seed=7)[1]


def test_split_rejects_impossible_sizes():
    with pytest.raises(ValueError):
        split_queries([1, 2, 3], validation=3)


def test_dev_data_reads_only_the_train_split(tmp_path, monkeypatch):
    catalog = pd.DataFrame({"product_id": ["p0", "p1"], "product_title": ["taza", "funda"]})
    queries = pd.DataFrame({"query_id": [2, 1], "query": ["funda", "taza"]})
    qrels = pd.DataFrame(
        {"query_id": [2, 1], "product_id": ["p1", "p0"], "esci_label": ["E", "E"], "gain": [1.0, 1.0]}
    )
    catalog.to_parquet(tmp_path / "catalog.parquet")
    queries.to_parquet(tmp_path / "queries_train.parquet")
    qrels.to_parquet(tmp_path / "qrels_train.parquet")
    # La partición de test existe pero está corrupta: leerla haría fallar la prueba.
    (tmp_path / "queries_test.parquet").write_text("no es parquet")
    (tmp_path / "qrels_test.parquet").write_text("no es parquet")

    read = []
    original = pd.read_parquet

    def spy(path):
        read.append(path.name)
        return original(path)

    monkeypatch.setattr(pd, "read_parquet", spy)
    data = load_dev_data(tmp_path)

    assert sorted(read) == ["catalog.parquet", "qrels_train.parquet", "queries_train.parquet"]
    assert data.qrels["query_id"].tolist() == [1, 2]  # ordenadas por consulta


class FakeDense:
    """Embeddings fijos: cada consulta se parece a un producto."""

    def __init__(self):
        self.doc_embeddings = np.eye(3, dtype=np.float32)

    def embed(self, queries):
        return np.stack([self.doc_embeddings[len(query) % 3] for query in queries])


def test_first_stage_features_keep_the_order_of_each_signal():
    docs = ["cafetera italiana", "funda móvil roja", "taza café cerámica"]
    bm25, dense = BM25Retriever(docs), FakeDense()
    queries = ["funda móvil", "taza"]
    stage = first_stage(queries, bm25, dense)

    lexical = bm25.score(queries)
    assert stage.lexical.max(axis=1) == pytest.approx([1.0, 1.0])
    assert (stage.lexical.argmax(axis=1) == lexical.argmax(axis=1)).all()
    fused = rrf([lexical, stage.dense])
    assert (np.argsort(-stage.fused, axis=1, kind="stable") == np.argsort(-fused, axis=1, kind="stable")).all()
    assert stage.top(2).shape == (2, 2) and stage.top(1)[0, 0] == 1

    features = stage.features(np.array([0, 1]), np.array([1, 2]))
    assert features.shape == (2, 3)
    assert features[0] == pytest.approx([stage.dense[0, 1], 1.0, stage.fused[0, 1]])


def test_first_stage_without_lexical_match_has_no_nan():
    stage = first_stage(["zzzz"], BM25Retriever(["cafetera", "funda", "taza"]), FakeDense())
    assert np.isfinite(stage.lexical).all() and not stage.lexical.any()


def test_ndcg_by_query_follows_the_scores_of_each_row():
    qrels = pd.DataFrame(
        {
            "query_id": [1, 1, 1, 2, 2],
            "product_id": ["a", "b", "c", "a", "d"],
            "gain": [0.0, 1.0, 0.1, 1.0, 0.0],
        }
    )
    result = ndcg_by_query(qrels, np.array([0.9, 0.5, 0.1, 0.2, 0.1]))
    assert result.index.tolist() == [1, 2]
    assert result[1] == pytest.approx(ndcg(np.array([0.0, 1.0, 0.1])))
    assert result[2] == pytest.approx(1.0)
