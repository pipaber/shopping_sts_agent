"""Compara BM25, denso e híbrido (RRF) con nDCG@10 sobre los candidatos anotados.

Uso::

    python -m shopping_agent.eval.retrieval --split train

``--split test`` es solo para la evaluación final: no se ajusta nada con test.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import pandas as pd

from shopping_agent.retrieval.metrics import evaluate
from shopping_agent.retrieval.retrievers import DEFAULT_DENSE_MODEL, BM25Retriever, DenseRetriever, rrf
from shopping_agent.retrieval.text import ALL_FIELDS, SHORT_FIELDS, product_texts


def run(data_dir: Path, split: str, model_name: str, out_dir: Path) -> pd.DataFrame:
    catalog = pd.read_parquet(data_dir / "catalog.parquet")
    queries = pd.read_parquet(data_dir / f"queries_{split}.parquet")
    qrels = pd.read_parquet(data_dir / f"qrels_{split}.parquet")
    query_texts, query_ids = queries["query"].tolist(), queries["query_id"].tolist()
    product_ids = catalog["product_id"].tolist()

    timings = {}

    start = time.perf_counter()
    bm25 = BM25Retriever(product_texts(catalog, ALL_FIELDS))
    timings["bm25_index_s"] = time.perf_counter() - start
    start = time.perf_counter()
    bm25_scores = bm25.score(query_texts)
    timings["bm25_ms_per_query"] = 1000 * (time.perf_counter() - start) / len(query_texts)

    cache = data_dir / f"emb_{model_name.replace('/', '__')}.npy"
    start = time.perf_counter()
    dense = DenseRetriever(product_texts(catalog, SHORT_FIELDS), model_name, cache_path=cache)
    timings["dense_index_s"] = time.perf_counter() - start
    start = time.perf_counter()
    dense_scores = dense.score(query_texts)
    timings["dense_ms_per_query"] = 1000 * (time.perf_counter() - start) / len(query_texts)

    systems = {
        "BM25 (base léxica)": bm25_scores,
        f"Denso ({model_name.split('/')[-1]})": dense_scores,
        "Híbrido RRF": rrf([bm25_scores, dense_scores]),
    }
    table = pd.DataFrame(
        {name: evaluate(scores, query_ids, product_ids, qrels) for name, scores in systems.items()}
    ).T

    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {"split": split, "model": model_name, "metrics": table.to_dict("index"), "timings": timings}
    (out_dir / f"retrieval_{split}.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(table.round(4).to_string())
    print({key: round(value, 2) for key, value in timings.items()})
    return table


def main() -> None:
    parser = argparse.ArgumentParser(description="Evalúa los recuperadores con las qrels de ESCI.")
    parser.add_argument("--data", type=Path, default=Path("datasets/processed"))
    parser.add_argument("--split", choices=["train", "test"], default="train")
    parser.add_argument("--model", default=DEFAULT_DENSE_MODEL)
    parser.add_argument("--out", type=Path, default=Path("results"))
    args = parser.parse_args()
    run(args.data, args.split, args.model, args.out)


if __name__ == "__main__":
    main()
