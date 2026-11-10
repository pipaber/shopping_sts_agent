"""Evaluación final en test, sobre el grafo sintético (sin GPU ni modelos)."""

import json
import sys

import numpy as np
import pandas as pd
import pytest
import torch
from synthetic_graph import ALL, CONTROL, DOC_EMBEDDINGS, GAIN, PRODUCTS, make_development, trained_like, unit

from shopping_agent.eval import retrieval_test as final
from shopping_agent.retrieval.first_stage import FirstStage
from shopping_agent.retrieval.graph import with_query
from shopping_agent.retrieval.train import annotated_scores

NEW_QUERIES = 3


def new_stage() -> FirstStage:
    embeddings = unit(NEW_QUERIES, seed=7)
    dense = embeddings @ DOC_EMBEDDINGS.T
    lexical = np.random.default_rng(8).random((NEW_QUERIES, PRODUCTS)).astype(np.float32)
    return FirstStage(embeddings, dense, lexical, fused=(dense + lexical) / 2)


def new_set() -> final.EvalSet:
    """Tres consultas que el entrenamiento no ha visto, con cuatro productos anotados cada una."""
    queries = pd.DataFrame({"query_id": [303, 101, 202]})  # sin ordenar, como puede venir el archivo
    rows = [(query_id, f"p{start + step}", label) for query_id, start in ((303, 0), (101, 4), (202, 8)) for step, label in enumerate("ESCI")]
    qrels = pd.DataFrame(rows, columns=["query_id", "product_id", "esci_label"])
    qrels = qrels.assign(gain=qrels["esci_label"].map(GAIN))
    return final.make_eval_set(queries, qrels, [f"p{row}" for row in range(PRODUCTS)], new_stage())


def test_new_queries_are_scored_as_the_agent_scores_one():
    development, test, model = make_development(), new_set(), trained_like(ALL)
    graph, offset = final.with_new_queries(development.graph, test.stage)
    together = annotated_scores(model, graph, final.lists_for(test, offset, "cpu"))

    query_rows, product_rows = test.pairs
    one_by_one = []
    for row in sorted(set(query_rows), key=lambda row: test.qrels["query_id"][query_rows == row].iloc[0]):
        candidates = torch.as_tensor(test.stage.top(final.CANDIDATES)[row])
        alone, node = with_query(development.graph, torch.as_tensor(test.stage.query_embeddings[row]), candidates)
        products = torch.as_tensor(product_rows[query_rows == row])
        features = torch.as_tensor(test.stage.features(np.full(len(products), row), products.numpy()))
        with torch.no_grad():
            one_by_one += model.score(model.encode(alone), torch.full_like(products, node), products, features).tolist()
    assert together == pytest.approx(one_by_one, abs=1e-5)
    assert graph["query"].num_nodes == development.graph["query"].num_nodes + NEW_QUERIES


def test_recall_counts_exact_products_in_the_top():
    test = new_set()
    scores = np.zeros((NEW_QUERIES, PRODUCTS), dtype=np.float32)
    scores[0, 0] = scores[1, 5] = 1.0  # la consulta 303 tiene su exacto (p0) arriba; la 101 (exacto p4), no
    scores[2, 8] = 1.0
    assert final.recall_by_query(scores, test, depth=1).tolist() == [1.0, 0.0, 1.0]


def test_summary_compares_every_system_with_hybrid_and_control():
    test = new_set()
    baselines = final.baseline_scores(test, depth=3)
    development = make_development()
    rerankers = {}
    for variant, config in (("control", CONTROL), ("sage", ALL)):
        graph, offset = final.with_new_queries(development.graph, test.stage)
        scores = annotated_scores(trained_like(config), graph, final.lists_for(test, offset, "cpu"))
        rerankers[variant] = [final.ndcg_by_query(test.qrels, scores).to_numpy()] * 2
    systems = final.summarize(baselines, rerankers)
    assert list(systems) == [*final.BASELINES, *final.RERANKERS.values()]
    control, sage = (systems[label] for label in final.RERANKERS.values())
    assert control["vs_control"] == {"diff": 0.0, "ci95": [0.0, 0.0]} and len(sage["per_seed"]) == 2
    assert sage[final.RECALL] == systems[final.HYBRID][final.RECALL]
    assert systems[final.HYBRID]["vs_hybrid"]["diff"] == 0.0
    low, high = systems[final.HYBRID][final.NDCG]["ci95"]
    assert low <= systems[final.HYBRID][final.NDCG]["mean"] <= high

    record = {
        "date": "2026-11-10", "commit": "abc", "test_queries": NEW_QUERIES, "systems": systems,
        "protocol": {"fit_queries": 4, "seeds": [0, 1]}, "validation_ndcg@10": {final.HYBRID: 0.7403},
    }
    table = final.to_markdown(record)
    assert "| Híbrido + GraphSAGE |" in table and "0,7403" in table and "commit `abc`" in table


def test_it_refuses_to_run_twice(tmp_path, monkeypatch):
    (tmp_path / f"{final.OUT_NAME}.json").write_text(json.dumps({}), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["retrieval_test", "--out", str(tmp_path)])
    with pytest.raises(SystemExit, match="una sola vez"):
        final.main()
