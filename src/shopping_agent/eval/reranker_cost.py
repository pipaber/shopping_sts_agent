"""Coste del reranker en el agente: tiempo añadido por consulta y memoria de GPU.

Uso::

    python -m shopping_agent.eval.reranker_cost --variant control

Busca las mismas consultas de train con y sin reranker (aquí solo importa el
texto de las consultas, no sus etiquetas) y escribe
``results/reranker_cost_<variante>.json``.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from shopping_agent.agent.search import DEFAULT_DATA_DIR, RERANKER_OFF, CatalogSearch
from shopping_agent.gpu import process_vram_mib
from shopping_agent.retrieval.reranker import GraphReranker
from shopping_agent.retrieval.retrievers import DenseRetriever
from shopping_agent.retrieval.train import DEFAULT_VARIANT, VARIANTS

TOP = 50


def milliseconds_per_query(search: CatalogSearch, queries: list[str]) -> dict[str, float]:
    search.rank(queries[0], TOP)  # la primera llamada carga cosas en la GPU y no cuenta
    times = []
    for query in queries:
        start = time.perf_counter()
        search.rank(query, TOP)
        times.append(1000 * (time.perf_counter() - start))
    return {"mean": round(float(np.mean(times)), 2), "median": round(float(np.median(times)), 2)}


def with_reranker(search: CatalogSearch, data_dir: Path, variant: str, device: str) -> CatalogSearch:
    """La misma búsqueda, con los mismos recuperadores ya cargados, más el reranker."""
    if not isinstance(search.dense, DenseRetriever):
        raise TypeError("El reranker necesita el recuperador denso.")
    reranker = GraphReranker.load(data_dir, variant, search.bm25, search.dense, device)
    return CatalogSearch(search.catalog, search.bm25, search.dense, reranker)


def measure(data_dir: Path, variant: str, queries: list[str]) -> dict[str, object]:
    plain = CatalogSearch.from_dir(data_dir, reranker=RERANKER_OFF)
    record: dict[str, object] = {"variant": variant, "queries": len(queries), "top": TOP}
    record["hybrid_ms"] = milliseconds_per_query(plain, queries)
    vram_before = process_vram_mib()
    devices = ["cuda", "cpu"] if torch.cuda.is_available() else ["cpu"]
    for device in devices:
        reranked = with_reranker(plain, data_dir, variant, device)
        record[f"reranked_ms_{device}"] = milliseconds_per_query(reranked, queries)
        if device == "cuda" and vram_before is not None:
            record["vram_mib"] = {"hybrid": vram_before, "with_reranker": process_vram_mib()}
            record["torch_peak_mib"] = round(torch.cuda.max_memory_allocated() / 2**20)
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description="Mide el coste del reranker por consulta.")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--queries", type=int, default=200)
    parser.add_argument("--variant", choices=sorted(VARIANTS), default=DEFAULT_VARIANT)
    parser.add_argument("--out", type=Path, default=None, help="por defecto, results/reranker_cost_<variante>.json")
    args = parser.parse_args()
    queries = pd.read_parquet(args.data / "queries_train.parquet")["query"].tolist()[: args.queries]
    record = measure(args.data, args.variant, queries)
    out = args.out or Path(f"results/reranker_cost_{args.variant}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(record, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
