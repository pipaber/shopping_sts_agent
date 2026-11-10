import numpy as np
import pandas as pd
import pytest

from shopping_agent.retrieval.metrics import evaluate, ndcg, ndcg_of_rankings
from shopping_agent.retrieval.retrievers import BM25Retriever, rrf
from shopping_agent.retrieval.text import clean, product_texts, tokenize


def test_clean_removes_html_and_broken_entities():
    assert clean("<b>Taza</b>&nbsp;de caf&eacute;<br>s & # xFFFD; lida") == "Taza de café s lida"
    assert clean(None) == "" and clean(float("nan")) == ""


def test_tokenize_folds_accents_and_drops_stopwords():
    assert tokenize("Cafetera de Cápsulas, 19 bar") == ["cafetera", "capsulas", "19", "bar"]


def test_product_texts_skips_missing_fields():
    catalog = pd.DataFrame({"product_title": ["Taza"], "product_brand": [None], "product_color": ["rojo"]})
    assert product_texts(catalog, ["product_title", "product_brand", "product_color"]) == ["Taza . rojo"]


def test_ndcg_known_values():
    assert ndcg(np.array([1.0, 0.1, 0.0])) == pytest.approx(1.0)
    assert ndcg(np.array([0.0, 0.0])) == 0.0
    # Un exacto en la posición 2 en lugar de la 1: 1/log2(3).
    assert ndcg(np.array([0.0, 1.0])) == pytest.approx(1 / np.log2(3))
    # Solo cuentan las k primeras posiciones.
    assert ndcg(np.array([0.0, 0.0, 1.0]), k=2) == 0.0


def test_bm25_ranks_matching_document_first():
    docs = ["cafetera italiana de aluminio", "funda para móvil roja", "taza de café de cerámica"]
    scores = BM25Retriever(docs).score(["funda móvil", "", "zzzz"])
    assert scores.shape == (3, 3)
    assert scores[0].argmax() == 1
    assert not scores[1].any() and not scores[2].any()


def test_rrf_rewards_agreement():
    a = np.array([[3.0, 2.0, 1.0, 0.0]])
    b = np.array([[0.0, 3.0, 2.0, 1.0]])
    fused = rrf([a, b])
    assert fused[0].argmax() == 1  # segundo y primero: el mejor rango combinado
    assert fused[0, 0] == pytest.approx(1 / 61 + 1 / 64)


def test_evaluate_uses_only_annotated_candidates():
    product_ids = ["p0", "p1", "p2", "p3"]
    qrels = pd.DataFrame(
        {
            "query_id": [7, 7],
            "product_id": ["p1", "p3"],
            "esci_label": ["I", "E"],
            "gain": [0.0, 1.0],
        }
    )
    # p0 y p2 puntúan más alto pero no están anotados: no afectan al nDCG.
    scores = np.array([[9.0, 1.0, 8.0, 2.0]])
    result = evaluate(scores, [7], product_ids, qrels, recall_depth=2)
    assert result["ndcg@10"] == pytest.approx(1.0)
    assert result["recall@2"] == 0.0  # el exacto queda tercero en el catálogo completo


def test_ndcg_of_rankings_counts_unannotated_products_as_irrelevant():
    gains = np.array([[1.0, 0.0, 0.1, 0.0], [0.0, 0.0, 0.0, 0.0]])
    ranked = np.array([[0, 2, 1], [1, 2, 3]])
    assert ndcg_of_rankings(ranked, gains, k=3).tolist() == pytest.approx([1.0, 0.0])
    # El exacto queda segundo, detrás de un producto sin anotar.
    second = ndcg_of_rankings(np.array([[3, 0, 2]]), gains[:1], k=3)
    ideal = 1.0 + 0.1 / np.log2(3)
    assert second[0] == pytest.approx((1.0 / np.log2(3) + 0.1 / 2) / ideal)
    # Solo cuentan las k primeras posiciones.
    assert ndcg_of_rankings(np.array([[1, 3, 0]]), gains[:1], k=2)[0] == 0.0
