"""Reranker sobre el grafo heterogéneo consulta–producto (GraphSAGE o GATv2) y su pérdida.

Cada capa es un ``HeteroConv`` de PyTorch Geometric con una convolución por tipo
de arista. Con ``relations=()`` no hay paso de mensajes y el modelo se queda en
una red por nodo con la misma cabeza de puntuación: es el control sin grafo de la
ablación.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass

import torch
import torch.nn.functional as F
from torch import nn
from torch_geometric.data import HeteroData
from torch_geometric.nn import GATv2Conv, HeteroConv, MessagePassing, SAGEConv

from shopping_agent.retrieval.first_stage import FEATURES
from shopping_agent.retrieval.graph import EDGE_TYPES, NODE_TYPES, PRODUCT, QUERY


@dataclass(frozen=True)
class RerankerConfig:
    relations: tuple[str, ...]
    conv: str = "sage"  # capa de paso de mensajes; ver ``message_passing``
    input_dim: int = 384
    hidden: int = 64
    layers: int = 2
    dropout: float = 0.5


def make_conv(kind: str, hidden: int) -> MessagePassing:
    """Capa que agrega los mensajes de una relación (sin el término del propio nodo)."""
    if kind == "sage":
        return SAGEConv((hidden, hidden), hidden, root_weight=False)
    if kind == "gatv2":
        return GATv2Conv((hidden, hidden), hidden, heads=4, concat=False, add_self_loops=False)
    raise ValueError(f"Capa desconocida: {kind}")


def message_passing(config: RerankerConfig) -> HeteroConv:
    """Paso de mensajes de una capa: una convolución por cada relación de la
    variante; lo que llega a un nodo por varias relaciones se suma.

    ``config.conv`` elige la capa. Otra capa heterogénea de PyG que se llame igual,
    ``capa(x_dict, edge_index_dict)``, entraría aquí como un valor más.
    """
    convs = {EDGE_TYPES[relation]: make_conv(config.conv, config.hidden) for relation in config.relations}
    with warnings.catch_warnings():
        # HeteroConv avisa de los tipos de nodo que no reciben mensajes. Aquí no es un
        # problema: cada nodo se actualiza además con su propia transformación.
        warnings.simplefilter("ignore", UserWarning)
        return HeteroConv(convs, aggr="sum")


class RerankLayer(nn.Module):
    """Estado nuevo de cada nodo: su propia transformación más lo que recibe por cada relación."""

    def __init__(self, config: RerankerConfig) -> None:
        super().__init__()
        self.own = nn.ModuleDict({node: nn.Linear(config.hidden, config.hidden) for node in NODE_TYPES})
        self.messages = message_passing(config)

    def forward(
        self, x_dict: dict[str, torch.Tensor], edge_index_dict: dict[tuple[str, str, str], torch.Tensor]
    ) -> dict[str, torch.Tensor]:
        received = self.messages(x_dict, edge_index_dict)
        new = {node: self.own[node](x) for node, x in x_dict.items()}
        return {node: F.relu(x + received[node] if node in received else x) for node, x in new.items()}


class Reranker(nn.Module):
    """Puntuación = combinación lineal de las señales de la primera etapa más una
    corrección que sale de los estados de la consulta y del producto.

    La corrección empieza en cero y la parte lineal en el coseno denso, así que
    antes de entrenar el modelo ordena igual que el recuperador denso y el
    entrenamiento solo puede alejarlo de ahí si la pérdida mejora.
    """

    def __init__(self, config: RerankerConfig) -> None:
        super().__init__()
        self.config = config
        self.inputs = nn.ModuleDict({node: nn.Linear(config.input_dim, config.hidden) for node in NODE_TYPES})
        self.layers = nn.ModuleList(RerankLayer(config) for _ in range(config.layers))
        self.dropout = nn.Dropout(config.dropout)
        self.base = nn.Linear(len(FEATURES), 1, bias=False)
        self.correction = nn.Sequential(
            nn.Linear(3 * config.hidden + len(FEATURES), config.hidden),
            nn.ReLU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.hidden, 1),
        )
        # Media y desviación de las características en los pares de ajuste.
        self.register_buffer("feature_mean", torch.zeros(len(FEATURES)))
        self.register_buffer("feature_std", torch.ones(len(FEATURES)))
        self._start_from_dense()

    def _start_from_dense(self) -> None:
        with torch.no_grad():
            self.base.weight.copy_(torch.eye(len(FEATURES))[:1])  # solo el coseno, que es la primera
            last = self.correction[-1]
            last.weight.zero_()
            last.bias.zero_()

    def set_feature_scale(self, features: torch.Tensor) -> None:
        """Fija la escala con las características de los pares de ajuste, ``(n, señales)``."""
        self.feature_mean.copy_(features.mean(dim=0))
        self.feature_std.copy_(features.std(dim=0).clamp(min=1e-6))

    def encode(self, graph: HeteroData) -> dict[str, torch.Tensor]:
        """Estado final de todos los nodos, por tipo, tras el paso de mensajes."""
        states = {node: self.dropout(F.relu(self.inputs[node](x))) for node, x in graph.x_dict.items()}
        for layer in self.layers:
            states = {node: self.dropout(state) for node, state in layer(states, graph.edge_index_dict).items()}
        return states

    def score(
        self,
        states: dict[str, torch.Tensor],
        queries: torch.Tensor,
        products: torch.Tensor,
        features: torch.Tensor,
    ) -> torch.Tensor:
        """Puntuación de cada par. ``queries`` y ``products`` son índices de nodo y
        ``features`` las señales de la primera etapa de cada par."""
        query, product = states[QUERY][queries], states[PRODUCT][products]
        scaled = (features - self.feature_mean) / self.feature_std
        correction = self.correction(torch.cat([query, product, query * product, scaled], dim=-1))
        return (self.base(scaled) + correction).squeeze(-1)


def pairwise_gain_loss(scores: torch.Tensor, gains: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
    """Pérdida por pares dentro de cada consulta, ponderada por la diferencia de ganancia.

    Para cada par de candidatos anotados en que uno gana más que el otro, penaliza
    que no quede por delante (logística, como RankNet) con un peso igual a la
    diferencia entre sus ganancias: equivocarse entre un exacto y un irrelevante
    cuesta diez veces más que entre un sustituto y un irrelevante, como en el nDCG.
    Cada consulta pesa lo mismo. Las entradas son ``(consultas, candidatos)``.
    """
    valid = mask.unsqueeze(2) & mask.unsqueeze(1)
    weight = (gains.unsqueeze(2) - gains.unsqueeze(1)).clamp(min=0) * valid
    wrong_order = F.softplus(scores.unsqueeze(1) - scores.unsqueeze(2))
    total = weight.sum(dim=(1, 2))
    per_query = (weight * wrong_order).sum(dim=(1, 2)) / total.clamp(min=1e-9)
    return per_query[total > 0].mean()
