"""Compara modelos de embedding para el recuperador denso, con las consultas de train.

Uso::

    python -m shopping_agent.eval.embeddings

No entrena nada y no lee test. Mide el denso y el híbrido con BM25 de cada modelo
candidato frente al modelo en uso, consulta a consulta, y escribe
``results/embedding_comparison.json`` y ``.md``.

Los candidatos se codifican en media precisión y en lotes pequeños, para poder
medir con la GPU ocupada por el agente; eso mueve el nDCG en el cuarto decimal.
El modelo en uso reutiliza sus embeddings de catálogo ya guardados.
"""

from __future__ import annotations

import argparse
import json
import re
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import numpy as np
import pandas as pd

from shopping_agent.retrieval.dev_data import load_dev_data, split_queries
from shopping_agent.retrieval.metrics import evaluate, ndcg_by_query
from shopping_agent.retrieval.retrievers import DEFAULT_DENSE_MODEL, BM25Retriever, rrf
from shopping_agent.retrieval.text import ALL_FIELDS, SHORT_FIELDS, product_texts

CANDIDATES = ("intfloat/multilingual-e5-base", "BAAI/bge-m3")
SYSTEMS = {"dense": "Denso", "hybrid": "Híbrido RRF"}
MAX_TOKENS = 256
BATCH = 16
RESAMPLES = 2000
REPORT_NAME = "embedding_comparison"


class Encoder(Protocol):
    def encode(self, sentences: list[str], **options: Any) -> np.ndarray: ...


@dataclass(frozen=True)
class Benchmark:
    """Lo que comparten todos los modelos: textos, etiquetas de train y BM25."""

    docs: list[str]
    query_texts: list[str]
    query_ids: list[int]
    product_ids: list[str]
    qrels: pd.DataFrame
    bm25_scores: np.ndarray
    validation_ids: list[int]


def load_benchmark(data_dir: Path) -> Benchmark:
    data = load_dev_data(data_dir)
    query_texts, query_ids = data.queries["query"].tolist(), data.queries["query_id"].tolist()
    _, validation_ids = split_queries(query_ids)
    return Benchmark(
        docs=product_texts(data.catalog, SHORT_FIELDS),
        query_texts=query_texts,
        query_ids=query_ids,
        product_ids=data.catalog["product_id"].tolist(),
        qrels=data.qrels,
        bm25_scores=BM25Retriever(product_texts(data.catalog, ALL_FIELDS)).score(query_texts),
        validation_ids=validation_ids,
    )


def prefixes(model_name: str) -> tuple[str, str]:
    """Prefijos de consulta y de documento: los modelos E5 los esperan; el resto, no."""
    return ("query: ", "passage: ") if "e5" in model_name.lower() else ("", "")


def encode(model: Encoder, texts: list[str]) -> np.ndarray:
    """Vectores normalizados en precisión simple, venga el modelo en la que venga."""
    vectors = model.encode(texts, batch_size=BATCH, normalize_embeddings=True, convert_to_numpy=True)
    vectors = vectors.astype(np.float32)
    return vectors / np.linalg.norm(vectors, axis=1, keepdims=True)


def catalog_cache(data_dir: Path, model_name: str) -> Path:
    """El modelo en uso comparte la caché del agente; los candidatos llevan su marca
    de media precisión para que nadie los tome por los embeddings definitivos."""
    suffix = "" if model_name == DEFAULT_DENSE_MODEL else ".fp16"
    return data_dir / f"emb_{model_name.replace('/', '__')}{suffix}.npy"


def catalog_vectors(model: Encoder, model_name: str, docs: list[str], data_dir: Path) -> np.ndarray:
    cache = catalog_cache(data_dir, model_name)
    if cache.exists():
        return np.load(cache)
    vectors = encode(model, [prefixes(model_name)[1] + doc for doc in docs])
    np.save(cache, vectors)
    return vectors


def dense_scores(model_name: str, bench: Benchmark, data_dir: Path) -> tuple[np.ndarray, dict[str, Any]]:
    """Cosenos consulta–producto de un modelo y lo que costó calcularlos."""
    import torch
    from sentence_transformers import SentenceTransformer

    on_gpu = torch.cuda.is_available()
    if on_gpu:
        torch.cuda.reset_peak_memory_stats()
    model = SentenceTransformer(model_name)
    model.max_seq_length = MAX_TOKENS
    half = model_name != DEFAULT_DENSE_MODEL
    if half:
        model.half()
    start = time.perf_counter()
    doc_vectors = catalog_vectors(model, model_name, bench.docs, data_dir)
    catalog_seconds = time.perf_counter() - start
    start = time.perf_counter()
    query_vectors = encode(model, [prefixes(model_name)[0] + query for query in bench.query_texts])
    cost = {
        "dimension": int(doc_vectors.shape[1]),
        "catalog_seconds": round(catalog_seconds, 1),  # 0 si ya estaban guardados
        "query_ms": round(1000 * (time.perf_counter() - start) / len(bench.query_texts), 2),
        "peak_vram_mib": int(torch.cuda.max_memory_allocated() / 2**20) if on_gpu else None,
        "half_precision": half,
    }
    return query_vectors @ doc_vectors.T, cost


def qrels_cells(bench: Benchmark) -> tuple[np.ndarray, np.ndarray]:
    """Fila y columna, en una matriz de puntuaciones, de cada par anotado."""
    row = {query_id: index for index, query_id in enumerate(bench.query_ids)}
    column = {product_id: index for index, product_id in enumerate(bench.product_ids)}
    queries = np.array([row[query_id] for query_id in bench.qrels["query_id"]])
    products = np.array([column[product_id] for product_id in bench.qrels["product_id"]])
    return queries, products


def measure(scores: np.ndarray, bench: Benchmark) -> tuple[dict[str, Any], pd.Series]:
    """Métricas de un sistema y su nDCG@10 consulta a consulta."""
    by_query = ndcg_by_query(bench.qrels, scores[qrels_cells(bench)])
    metrics: dict[str, Any] = evaluate(scores, bench.query_ids, bench.product_ids, bench.qrels)
    metrics["ndcg@10_validation"] = float(by_query.loc[bench.validation_ids].mean())
    return metrics, by_query


def bootstrap_difference(system: pd.Series, reference: pd.Series, resamples: int = RESAMPLES) -> dict[str, Any]:
    """Diferencia media consulta a consulta, con intervalo del 95 % por bootstrap de consultas."""
    difference = (system - reference).to_numpy()
    picks = np.random.default_rng(0).integers(0, len(difference), size=(resamples, len(difference)))
    low, high = np.percentile(difference[picks].mean(axis=1), [2.5, 97.5])
    return {"mean": float(difference.mean()), "ci95": [float(low), float(high)]}


def compare(data_dir: Path, candidates: Sequence[str] = CANDIDATES) -> dict[str, Any]:
    """Informe por modelo: coste, métricas de cada sistema y diferencia con el modelo en uso."""
    bench = load_benchmark(data_dir)
    report: dict[str, Any] = {}
    by_query: dict[str, dict[str, pd.Series]] = {}
    for model_name in (DEFAULT_DENSE_MODEL, *candidates):
        scores, cost = dense_scores(model_name, bench, data_dir)
        systems = {"dense": scores, "hybrid": rrf([bench.bm25_scores, scores])}
        measured = {name: measure(matrix, bench) for name, matrix in systems.items()}
        report[model_name] = {"cost": cost, **{name: metrics for name, (metrics, _) in measured.items()}}
        by_query[model_name] = {name: series for name, (_, series) in measured.items()}
    for model_name in candidates:
        for name in SYSTEMS:
            system, reference = by_query[model_name][name], by_query[DEFAULT_DENSE_MODEL][name]
            validation = bench.validation_ids
            report[model_name][name]["vs_baseline_train"] = bootstrap_difference(system, reference)
            report[model_name][name]["vs_baseline_validation"] = bootstrap_difference(
                system.loc[validation], reference.loc[validation]
            )
    return report


def _number(value: float, signed: bool = False) -> str:
    return f"{value:+.4f}" if signed else f"{value:.4f}"


def _difference(metrics: dict[str, Any], key: str) -> str:
    """«+0,0123 [−0,0010; +0,0250]», o vacío para el modelo en uso."""
    if key not in metrics:
        return ""
    low, high = metrics[key]["ci95"]
    text = f"{_number(metrics[key]['mean'], True)} [{_number(low, True)}; {_number(high, True)}]"
    return text.replace("-", "−")


def _metric_rows(report: dict[str, Any]) -> list[str]:
    rows = []
    for model_name, entry in report.items():
        for name, label in SYSTEMS.items():
            metrics = entry[name]
            cells = [
                f"`{model_name}`",
                label,
                _number(metrics["ndcg@10"]),
                _difference(metrics, "vs_baseline_train"),
                _number(metrics["recall@50"]),
                _number(metrics["ndcg@10_validation"]),
                _difference(metrics, "vs_baseline_validation"),
            ]
            rows.append("| " + " | ".join(cells) + " |")
    return rows


def _cost_rows(report: dict[str, Any]) -> list[str]:
    rows = []
    for model_name, entry in report.items():
        cost = entry["cost"]
        seconds = f"{cost['catalog_seconds']:.0f}" if cost["catalog_seconds"] else "ya guardado"
        precision = "media" if cost["half_precision"] else "simple"
        cells = [f"`{model_name}`", cost["dimension"], seconds, cost["query_ms"], cost["peak_vram_mib"], precision]
        rows.append("| " + " | ".join(str(cell) for cell in cells) + " |")
    return rows


def to_markdown(report: dict[str, Any]) -> str:
    queries = next(iter(report.values()))["dense"]["queries"]
    lines = [
        "# Modelos de embedding: comparación con las consultas de train",
        "",
        f"{queries} consultas de train, de las que 300 son las de validación del reranker "
        "(semilla 42). Nada se entrena y las consultas de test no se han usado.",
        "",
        "- **nDCG@10**: la métrica del enunciado, sobre los candidatos anotados de cada consulta.",
        "- **recall@50**: fracción de productos exactos entre los 50 primeros de todo el catálogo.",
        f"- **Diferencias**: frente a `{DEFAULT_DENSE_MODEL}`, el modelo en uso, consulta a consulta, "
        "con intervalo del 95 % por bootstrap de consultas.",
        f"- Mismo texto para todos: título, marca, color y viñetas, cortado a {MAX_TOKENS} tokens.",
        "- Los candidatos se codificaron en media precisión, que mueve el nDCG en el cuarto decimal.",
        "",
        "| Modelo | Sistema | nDCG@10 | Dif. en train | recall@50 | nDCG@10 validación | Dif. en validación |",
        "|---|---|---|---|---|---|---|",
        *_metric_rows(report),
        "",
        "| Modelo | Dimensión | Catálogo (s) | Consulta (ms) | VRAM pico (MiB) | Precisión |",
        "|---|---|---|---|---|---|",
        *_cost_rows(report),
        "",
        "Se reproduce con `python -m shopping_agent.eval.embeddings`.",
        "",
    ]
    return _decimal_commas("\n".join(lines))


def _decimal_commas(text: str) -> str:
    """Coma decimal en las cifras, sin tocar los puntos de las frases ni de los nombres."""
    return re.sub(r"(?<=\d)\.(?=\d)", ",", text)


def write_report(report: dict[str, Any], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{REPORT_NAME}.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / f"{REPORT_NAME}.md").write_text(to_markdown(report), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compara modelos de embedding con las consultas de train.")
    parser.add_argument("--data", type=Path, default=Path("datasets/processed"))
    parser.add_argument("--out", type=Path, default=Path("results"))
    parser.add_argument("--from-json", action="store_true", help="solo rehace el Markdown desde el JSON guardado")
    args = parser.parse_args()
    if args.from_json:
        report = json.loads((args.out / f"{REPORT_NAME}.json").read_text(encoding="utf-8"))
    else:
        report = compare(args.data)
    write_report(report, args.out)
    print(f"Informe en {args.out / REPORT_NAME}.md y .json")


if __name__ == "__main__":
    main()
