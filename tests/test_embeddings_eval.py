"""Comparación de modelos de embedding: las piezas que no necesitan modelo ni GPU."""

from __future__ import annotations

import numpy as np
import pandas as pd

from shopping_agent.eval.embeddings import bootstrap_difference, encode, prefixes, to_markdown
from shopping_agent.retrieval.retrievers import DEFAULT_DENSE_MODEL


class FakeModel:
    """Devuelve vectores en media precisión y sin normalizar, como un modelo con ``half()``."""

    def encode(self, sentences: list[str], **options: object) -> np.ndarray:
        return np.array([[3.0, 4.0]] * len(sentences), dtype=np.float16)


def test_only_e5_models_get_prefixes() -> None:
    assert prefixes("intfloat/multilingual-e5-base") == ("query: ", "passage: ")
    assert prefixes("BAAI/bge-m3") == ("", "")


def test_encode_returns_normalized_single_precision() -> None:
    vectors = encode(FakeModel(), ["a", "b"])

    assert vectors.dtype == np.float32
    np.testing.assert_allclose(np.linalg.norm(vectors, axis=1), 1.0, rtol=1e-6)


def test_bootstrap_difference_of_a_constant_shift() -> None:
    reference = pd.Series([0.2, 0.5, 0.9], index=[1, 2, 3])

    result = bootstrap_difference(reference + 0.1, reference, resamples=50)

    assert np.isclose(result["mean"], 0.1)
    np.testing.assert_allclose(result["ci95"], [0.1, 0.1])


def test_bootstrap_interval_contains_the_mean() -> None:
    rng = np.random.default_rng(1)
    reference = pd.Series(rng.random(200))
    system = reference + rng.normal(0.02, 0.1, size=200)

    result = bootstrap_difference(system, reference)

    low, high = result["ci95"]
    assert low < result["mean"] < high


def _system(ndcg: float, difference: float | None = None) -> dict[str, object]:
    metrics: dict[str, object] = {"ndcg@10": ndcg, "recall@50": 0.5, "queries": 4, "ndcg@10_validation": ndcg}
    if difference is not None:
        shift = {"mean": difference, "ci95": [difference - 0.01, difference + 0.01]}
        metrics |= {"vs_baseline_train": shift, "vs_baseline_validation": shift}
    return metrics


def _entry(half: bool, difference: float | None = None) -> dict[str, object]:
    cost = {
        "dimension": 8,
        "catalog_seconds": 12.4 if half else 0.0,
        "query_ms": 0.5,
        "peak_vram_mib": 100,
        "half_precision": half,
    }
    return {"cost": cost, "dense": _system(0.7, difference), "hybrid": _system(0.6, difference)}


def test_markdown_has_a_row_per_model_and_system_with_decimal_commas() -> None:
    report = {DEFAULT_DENSE_MODEL: _entry(half=False), "otro/modelo": _entry(half=True, difference=-0.02)}

    text = to_markdown(report)

    assert text.count(f"| `{DEFAULT_DENSE_MODEL}` |") == 3  # denso, híbrido y coste
    assert text.count("| `otro/modelo` |") == 3
    assert "0,7000" in text
    assert "−0,0200 [−0,0300; −0,0100]" in text
    assert "ya guardado" in text
    assert "media" in text
