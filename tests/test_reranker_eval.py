"""Comparación del reranker en validación, sobre el grafo sintético."""

import numpy as np
import pytest
from synthetic_graph import ALL, CONTROL, PRODUCTS, QUERIES, VALIDATION, make_data, make_development, make_stage

from shopping_agent.eval import reranker as reranker_eval
from shopping_agent.retrieval.graph import RELATIONS


def test_paired_difference_is_centred_on_the_mean_gap():
    reference = np.linspace(0.2, 0.8, 50)
    same = reranker_eval.paired_difference(reference, reference)
    assert same == {"diff": 0.0, "ci95": [0.0, 0.0]}
    better = reranker_eval.paired_difference(reference + 0.05, reference)
    assert better["diff"] == pytest.approx(0.05) and better["ci95"] == pytest.approx([0.05, 0.05])
    noisy = reranker_eval.paired_difference(reference + np.random.default_rng(0).normal(0, 0.1, 50), reference)
    assert noisy["ci95"][0] < noisy["diff"] < noisy["ci95"][1]


def test_comparison_reports_every_variant_against_the_control(monkeypatch):
    data, stage = make_data(), make_stage()
    development = make_development(data)
    validation = reranker_eval.validation_set(data, development.validation_qrels)
    assert validation.gains.shape == (VALIDATION, PRODUCTS) and (validation.gains > 0).sum() == 4 * VALIDATION
    monkeypatch.setattr(reranker_eval, "VARIANTS", {"control": CONTROL, "sage_exact": ALL})

    result = reranker_eval.compare(development, validation, stage, seeds=2, epochs=1)
    record = {"protocol": reranker_eval.protocol(development, seeds=2, epochs=1), **result}

    assert set(result["baselines"]) == set(reranker_eval.BASELINES)
    assert all(0 <= metrics["ndcg@10"] <= 1 for metrics in result["baselines"].values())
    control, sage = result["rerankers"]["control"], result["rerankers"]["sage_exact"]
    assert len(sage["ndcg@10"]["per_seed"]) == 2 and sage["relations"] == list(RELATIONS)
    assert control["differences"]["ndcg@10_vs_control"] == {"diff": 0.0, "ci95": [0.0, 0.0]}
    assert set(sage["differences"]) == {f"{metric}_vs_{name}" for metric, name in reranker_eval.COMPARISONS}
    assert record["protocol"]["fit_queries"] == QUERIES - VALIDATION
    table = reranker_eval.to_markdown(record)
    assert "| `sage_exact` | candidate, similar, brand, exact |" in table and "| `control` | ninguna |" in table
