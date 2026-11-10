"""Búsqueda en el catálogo para el agente: recuperación híbrida y evidencia textual.

Envuelve los recuperadores existentes (BM25 + denso con fusión RRF) y, si está
activado, el reranker que reordena sus primeros resultados. Solo lee el catálogo:
las etiquetas de relevancia de ESCI no se cargan aquí ni en ningún módulo del
agente. El reranker se entrenó con las de ajuste, pero al agente solo le llegan
sus pesos y su grafo ya construidos.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Protocol, TypedDict

import numpy as np
import pandas as pd

from shopping_agent.retrieval.retrievers import DEFAULT_DENSE_MODEL, BM25Retriever, DenseRetriever, rrf
from shopping_agent.retrieval.text import ALL_FIELDS, SHORT_FIELDS, clean, product_texts

DEFAULT_DATA_DIR = Path("datasets/processed")

# Interruptor del reranker: "on" u "off". Sirve para la ablación con y sin GNN.
# Activado por defecto: en validación mejora al híbrido en la métrica del enunciado
# y en la lista sobre todo el catálogo (results/reranker_validation.md).
RERANKER_ENV = "SHOPPING_AGENT_RERANKER"
RERANKER_DEFAULT = True
SWITCH = {"on": True, "1": True, "off": False, "0": False}

# Campos del catálogo que forman la evidencia de un producto.
EVIDENCE_FIELDS = {
    "title": "product_title",
    "brand": "product_brand",
    "color": "product_color",
    "bullets": "product_bullet_point",
    "description": "product_description",
}


class Evidence(TypedDict):
    """Texto del catálogo para un producto. ``None`` significa que el catálogo no
    trae ese dato (desconocido)."""

    product_id: str
    title: str
    brand: str | None
    color: str | None
    bullets: str | None
    description: str | None


class Scorer(Protocol):
    def score(self, queries: list[str]) -> np.ndarray: ...


class Reranker(Protocol):
    def rank(self, query: str, top: int) -> np.ndarray:
        """Filas del catálogo de los ``top`` primeros del híbrido, ya reordenadas."""
        ...


def reranker_enabled() -> bool:
    """Lo que diga ``SHOPPING_AGENT_RERANKER``; sin la variable, el valor por defecto."""
    value = os.environ.get(RERANKER_ENV, "").strip().lower()
    if not value:
        return RERANKER_DEFAULT
    if value not in SWITCH:
        raise ValueError(f"{RERANKER_ENV} debe ser 'on' u 'off', no {value!r}.")
    return SWITCH[value]


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0].rstrip(" ,.;:") + "…"


class CatalogSearch:
    """Ordena el catálogo para una consulta y devuelve los campos tal cual están."""

    def __init__(
        self,
        catalog: pd.DataFrame,
        bm25: Scorer,
        dense: Scorer | None = None,
        reranker: Reranker | None = None,
    ) -> None:
        self.catalog = catalog.reset_index(drop=True)
        self.product_ids: list[str] = self.catalog["product_id"].tolist()
        self._row = {product_id: row for row, product_id in enumerate(self.product_ids)}
        self.bm25 = bm25
        self.dense = dense
        self.reranker = reranker

    @classmethod
    def from_catalog(cls, catalog: pd.DataFrame, dense: Scorer | None = None) -> CatalogSearch:
        return cls(catalog, BM25Retriever(product_texts(catalog, ALL_FIELDS)), dense)

    @classmethod
    def from_dir(
        cls,
        data_dir: Path = DEFAULT_DATA_DIR,
        model_name: str = DEFAULT_DENSE_MODEL,
        rerank: bool | None = None,
    ) -> CatalogSearch:
        """Misma configuración que la evaluación: BM25 con todo el texto y denso con
        los campos cortos, reutilizando los embeddings ya calculados.

        ``rerank`` activa o desactiva el reranker; si no se indica, decide
        ``SHOPPING_AGENT_RERANKER``. Sus pesos se leen de ``data_dir``.
        """
        catalog = pd.read_parquet(data_dir / "catalog.parquet")
        cache = data_dir / f"emb_{model_name.replace('/', '__')}.npy"
        dense = DenseRetriever(product_texts(catalog, SHORT_FIELDS), model_name, cache_path=cache)
        bm25 = BM25Retriever(product_texts(catalog, ALL_FIELDS))
        if not (reranker_enabled() if rerank is None else rerank):
            return cls(catalog, bm25, dense)
        from shopping_agent.retrieval.reranker import GraphReranker
        from shopping_agent.retrieval.train import WEIGHTS_FILE, default_device

        reranker = GraphReranker.load(data_dir / WEIGHTS_FILE, bm25, dense, default_device())
        return cls(catalog, bm25, dense, reranker)

    def __contains__(self, product_id: object) -> bool:
        return product_id in self._row

    def rank(self, query: str, top: int = 50) -> list[str]:
        """Identificadores de los ``top`` productos por fusión RRF de BM25 y denso,
        reordenados por el reranker si está activado.

        La consulta se pasa a minúsculas, como vienen todas las de ESCI con las que se
        midió el recuperador. BM25 ya las ignora, pero el modelo denso no: sin esto,
        "Bluetooth" y "bluetooth" ordenan distinto los candidatos, y "el segundo" pasa a
        ser otro producto según cómo escriba la palabra el LLM o el ASR.
        """
        query = query.lower()
        if not query.strip():
            return []
        if self.reranker is not None:
            return [self.product_ids[row] for row in self.reranker.rank(query, top)]
        lexical = self.bm25.score([query])
        if self.dense is None:
            # Sin modelo denso (pruebas): solo cuentan los productos con algún término.
            order = np.argsort(-lexical[0], kind="stable")[:top]
            return [self.product_ids[row] for row in order if lexical[0, row] > 0]
        fused = rrf([lexical, self.dense.score([query])])[0]
        return [self.product_ids[row] for row in np.argsort(-fused, kind="stable")[:top]]

    def evidence(self, product_id: str, bullets_chars: int = 240, description_chars: int = 200) -> Evidence:
        """Texto del catálogo para un producto, recortado para caber en el contexto.

        Los campos que el catálogo no trae quedan en ``None`` (desconocidos).
        """
        record = self.catalog.iloc[self._row[product_id]]
        fields = {name: clean(record[column]) or None for name, column in EVIDENCE_FIELDS.items()}
        bullets, description = fields["bullets"], fields["description"]
        return Evidence(
            product_id=product_id,
            title=fields["title"] or product_id,
            brand=fields["brand"],
            color=fields["color"],
            bullets=_truncate(bullets, bullets_chars) if bullets else None,
            description=_truncate(description, description_chars) if description else None,
        )

    def title(self, product_id: str) -> str:
        if product_id not in self._row:
            return product_id
        return clean(self.catalog.at[self._row[product_id], "product_title"]) or product_id
