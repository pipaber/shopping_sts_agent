"""Grafo, modelo y entrenamiento del reranker sobre un grafo sintético pequeño."""

from dataclasses import replace

import numpy as np
import pandas as pd
import pytest
import torch
from torch_geometric.data import HeteroData
from torch_geometric.nn import HeteroConv
from synthetic_graph import (
    ALL,
    BRANDS,
    CONTROL,
    DIM,
    DOC_EMBEDDINGS,
    GAIN,
    PRODUCTS,
    QUERIES,
    VALIDATION,
    FakeDense,
    fit_and_validation_nodes,
    make_data,
    make_development,
    trained_like,
    unit,
)

from shopping_agent.retrieval import train
from shopping_agent.retrieval.dev_data import split_queries
from shopping_agent.retrieval.gnn import Reranker, pairwise_gain_loss
from shopping_agent.retrieval.graph import (
    EDGE_TYPES,
    PRODUCT,
    QUERY,
    RELATIONS,
    brand_edges,
    candidate_edges,
    edges_by_relation,
    exact_edges,
    hetero_graph,
    similar_edges,
    with_query,
    without_labels_of,
)


def edges(graph: HeteroData, relation: str) -> torch.Tensor:
    return graph[EDGE_TYPES[relation]].edge_index


# --- Construcción del grafo --------------------------------------------------------


def test_similar_edges_link_each_product_to_its_nearest_neighbours():
    embeddings = torch.tensor([[1.0, 0.0], [0.9, 0.1], [0.0, 1.0], [0.1, 0.9]])
    edges = similar_edges(embeddings, k=1)
    assert edges.tolist() == [[1, 0, 3, 2], [0, 1, 2, 3]]  # origen (vecino) → destino

    edges = similar_edges(torch.as_tensor(DOC_EMBEDDINGS), k=3, chunk=5)
    assert edges.shape == (2, PRODUCTS * 3)
    assert (edges[0] != edges[1]).all()  # nadie es vecino de sí mismo, tampoco entre trozos
    assert edges[1].bincount().tolist() == [3] * PRODUCTS
    assert similar_edges(embeddings[:1], k=3).shape == (2, 0)


def test_brand_edges_stay_inside_each_brand():
    edges = brand_edges(BRANDS, torch.as_tensor(DOC_EMBEDDINGS), k=5)
    names = [str(brand or "").strip().lower() for brand in BRANDS]
    assert all(names[source] == names[target] != "" for source, target in edges.T.tolist())
    connected = set(edges[1].tolist())
    assert connected == {0, 1, 7, 2, 4, 8, 10, 11}  # sin marca o con marca única: sin aristas
    assert edges[1].bincount(minlength=PRODUCTS)[0] == 2  # los otros dos Sony, sin distinguir mayúsculas


def test_candidate_edges_go_from_products_to_their_query():
    edges = candidate_edges(np.array([[4, 2], [0, 5]]))
    assert edges.tolist() == [[4, 2, 0, 5], [0, 0, 1, 1]]


def test_exact_edges_only_use_exact_labels():
    qrels = pd.DataFrame(
        {"query_id": [10, 10, 11], "product_id": ["p1", "p2", "p2"], "esci_label": ["E", "S", "E"]}
    )
    edges = exact_edges(qrels, {10: 0, 11: 1}, {"p1": 1, "p2": 2})
    assert edges.tolist() == [[0, 1], [1, 2]]


def test_graph_has_every_dev_query_but_labels_only_from_fit_queries():
    data = make_data()
    graph = make_development(data).graph
    fit, validation = fit_and_validation_nodes(data)

    assert isinstance(graph, HeteroData) and graph.node_types == [PRODUCT, QUERY]
    assert graph[QUERY].x.shape == (QUERIES, DIM) and graph[PRODUCT].x.shape == (PRODUCTS, DIM)
    assert set(graph.edge_types) == set(EDGE_TYPES.values())
    graph.validate()  # los índices de las aristas caben en sus tipos de nodo
    assert set(edges(graph, "candidate")[1].tolist()) == fit | validation
    assert set(edges(graph, "exact")[0].tolist()) == fit
    assert edges(graph, "exact").shape[1] == 2 * len(fit)  # dos exactos por consulta de ajuste


def test_validation_labels_do_not_reach_the_graph():
    data, other = make_data(seed=0), make_data(seed=5)
    _, validation_ids = split_queries(data.queries["query_id"].tolist(), VALIDATION)
    is_validation = data.qrels["query_id"].isin(validation_ids)
    assert (data.qrels[is_validation]["esci_label"] != other.qrels[is_validation]["esci_label"]).any()
    # Mismas etiquetas de ajuste, otras de validación: el grafo no cambia.
    changed = replace(data, qrels=pd.concat([data.qrels[~is_validation], other.qrels[is_validation]]).sort_index())

    graph, changed_graph = make_development(data).graph, make_development(changed).graph
    assert all(torch.equal(edges(graph, relation), edges(changed_graph, relation)) for relation in RELATIONS)


def test_no_query_receives_messages_through_labels():
    assert EDGE_TYPES["exact"] == (QUERY, "exact", PRODUCT)  # las etiquetas solo van hacia el producto
    assert [relation for relation, (_, _, target) in EDGE_TYPES.items() if target == QUERY] == ["candidate"]


# --- Fuga de etiquetas -------------------------------------------------------------


def test_without_labels_of_removes_only_the_edges_of_those_queries():
    graph = make_development().graph
    query = edges(graph, "exact")[0, 0]
    masked = without_labels_of(graph, query.unsqueeze(0))

    assert query not in edges(masked, "exact")[0]
    assert edges(masked, "exact").shape[1] == edges(graph, "exact").shape[1] - 2
    assert all(torch.equal(edges(masked, relation), edges(graph, relation)) for relation in RELATIONS if relation != "exact")
    assert query in edges(graph, "exact")[0]  # el grafo original no se modifica


def test_a_fit_query_does_not_see_its_own_labels_when_training():
    """Con las etiquetas de la consulta cambiadas, sus puntuaciones no cambian: no le
    llegan por el grafo. Sin la máscara sí cambiarían, que es la fuga que se evita."""
    data = make_data()
    fit, _ = fit_and_validation_nodes(data)
    node = min(fit)
    query_id = data.queries["query_id"][node]
    own = data.qrels["query_id"] == query_id
    flipped = data.qrels["esci_label"].where(~own, data.qrels["esci_label"].map({"E": "I", "S": "E", "C": "E", "I": "S"}))
    changed = replace(data, qrels=data.qrels.assign(esci_label=flipped, gain=flipped.map(GAIN)))

    model = trained_like(ALL)
    scores = {}
    for name, development in (("original", make_development(data)), ("changed", make_development(changed))):
        batch = development.fit.batch((development.fit.queries == node).nonzero().squeeze(1))
        with torch.no_grad():
            scores[name, "masked"] = train.score_lists(model, without_labels_of(development.graph, batch.queries), batch)
            scores[name, "leaky"] = train.score_lists(model, development.graph, batch)

    assert torch.equal(scores["original", "masked"], scores["changed", "masked"])
    assert not torch.allclose(scores["original", "leaky"], scores["changed", "leaky"])


def test_train_step_hides_the_labels_of_the_queries_in_the_batch(monkeypatch):
    development = make_development()
    seen = []
    original = train.score_lists

    def spy(model, graph, lists):
        seen.append((graph, lists))
        return original(model, graph, lists)

    monkeypatch.setattr(train, "score_lists", spy)
    model = Reranker(ALL)
    optimizer = torch.optim.AdamW(model.parameters())
    batch = development.fit.batch(torch.tensor([0, 2]))
    loss = train.train_step(model, optimizer, development.graph, batch)

    (graph, lists), = seen
    assert np.isfinite(loss) and lists is batch
    assert not torch.isin(edges(graph, "exact")[0], batch.queries).any()
    assert edges(graph, "exact").shape[1] == edges(development.graph, "exact").shape[1] - 4


# --- Modelo ------------------------------------------------------------------------


@pytest.mark.parametrize("conv", ["sage", "gatv2"])
def test_scores_have_one_value_per_candidate(conv):
    development = make_development()
    model = trained_like(replace(ALL, conv=conv))
    with torch.no_grad():
        scores = train.score_lists(model, development.graph, development.validation)
    assert scores.shape == development.validation.products.shape == (VALIDATION, 5)
    assert torch.isfinite(scores).all()
    flat = train.annotated_scores(model, development.graph, development.validation)
    assert flat.shape == (len(development.validation_qrels),)
    assert flat == pytest.approx(scores.reshape(-1).numpy())  # en el orden de las filas de las qrels


def test_untrained_model_ranks_like_the_dense_retriever():
    development = make_development()
    lists = development.validation
    model = Reranker(ALL).eval()
    with torch.no_grad():
        scores = train.score_lists(model, development.graph, lists)
    cosine = lists.features[..., 0]
    assert torch.equal(scores.argsort(dim=1), cosine.argsort(dim=1))


def test_control_has_no_message_passing():
    development = make_development()
    graph = development.graph
    empty = {relation: index[:, :0] for relation, index in edges_by_relation(graph).items()}
    no_edges = hetero_graph(graph[PRODUCT].x, graph[QUERY].x, empty)
    control, sage = trained_like(CONTROL), trained_like(ALL)
    with torch.no_grad():
        assert torch.equal(
            train.score_lists(control, graph, development.fit), train.score_lists(control, no_edges, development.fit)
        )
        assert not torch.allclose(
            train.score_lists(sage, graph, development.fit), train.score_lists(sage, no_edges, development.fit)
        )
    assert not any("messages" in name for name, _ in control.named_parameters())


def test_each_layer_is_a_hetero_conv_over_the_relations_of_the_variant():
    layer = Reranker(ALL).layers[0]
    assert isinstance(layer.messages, HeteroConv) and layer.messages.aggr == "sum"
    assert list(layer.messages.convs.keys()) == [EDGE_TYPES[relation] for relation in RELATIONS]
    assert len(Reranker(CONTROL).layers[0].messages.convs) == 0


def test_new_query_joins_the_graph_through_its_candidates_only():
    development = make_development()
    graph, lists = development.graph, development.fit
    model = trained_like(ALL)
    candidates = torch.tensor([3, 7, 9])
    extended, node = with_query(graph, torch.as_tensor(unit(1, seed=9)[0]), candidates)

    assert node == QUERIES and extended[QUERY].num_nodes == QUERIES + 1 and graph[QUERY].num_nodes == QUERIES
    assert edges(graph, "candidate").shape[1] == edges(extended, "candidate").shape[1] - 3  # el original no cambia
    new_edges = edges(extended, "candidate")[:, edges(extended, "candidate")[1] == node]
    assert new_edges[0].tolist() == [3, 7, 9]
    assert all(edges(extended, relation) is edges(graph, relation) for relation in ("similar", "brand", "exact"))
    with torch.no_grad():
        states = model.encode(extended)
        scores = model.score(states, torch.full((3,), node), candidates, torch.zeros(3, 3))
        # Los productos no reciben nada de la consulta nueva: el resto no cambia.
        assert torch.equal(train.score_lists(model, extended, lists), train.score_lists(model, graph, lists))
    assert scores.shape == (3,)


# --- Pérdida -----------------------------------------------------------------------


def test_loss_is_lower_when_higher_gains_rank_first():
    gains = torch.tensor([[1.0, 0.1, 0.0]])
    mask = torch.ones(1, 3, dtype=torch.bool)
    good = pairwise_gain_loss(torch.tensor([[3.0, 2.0, 1.0]]), gains, mask)
    bad = pairwise_gain_loss(torch.tensor([[1.0, 2.0, 3.0]]), gains, mask)
    assert good < bad


def test_loss_weights_pairs_by_gain_difference_and_ignores_padding():
    scores = torch.zeros(2, 3)
    gains = torch.tensor([[1.0, 0.0, 1.0], [0.1, 0.1, 0.0]])
    mask = torch.tensor([[True, True, False], [True, True, False]])
    # Primera consulta: un solo par (exacto frente a irrelevante) con puntuaciones iguales.
    # Segunda: sus dos candidatos válidos empatan en ganancia y no aporta nada.
    assert pairwise_gain_loss(scores, gains, mask).item() == pytest.approx(np.log(2))

    scores = torch.tensor([[0.0, 2.0, 0.0]])
    gains, mask = torch.tensor([[1.0, 0.1, 0.0]]), torch.ones(1, 3, dtype=torch.bool)
    softplus = torch.nn.functional.softplus
    expected = (0.9 * softplus(torch.tensor(2.0)) + 1.0 * np.log(2) + 0.1 * softplus(torch.tensor(-2.0))) / 2.0
    assert pairwise_gain_loss(scores, gains, mask).item() == pytest.approx(expected.item())


# --- Entrenamiento -----------------------------------------------------------------


def write_dev_files(data_dir):
    data = make_data()
    catalog = data.catalog.assign(
        product_title=[f"producto {row} azul" for row in range(PRODUCTS)],
        product_color=None, product_bullet_point=None, product_description=None,
    )
    catalog.to_parquet(data_dir / "catalog.parquet")
    data.queries.assign(query=[f"producto {row}" for row in range(QUERIES)]).to_parquet(data_dir / "queries_train.parquet")
    data.qrels.to_parquet(data_dir / "qrels_train.parquet")


def test_training_never_reads_the_test_split(tmp_path, monkeypatch):
    """En la carpeta solo están el catálogo y la partición de train, y aun así se
    prepara todo, se entrena y se guardan los pesos."""
    write_dev_files(tmp_path)
    read = []
    original = pd.read_parquet

    def spy(path):
        read.append(path.name)
        return original(path)

    monkeypatch.setattr(pd, "read_parquet", spy)
    development = train.prepare(tmp_path, FakeDense(), VALIDATION, "cpu")
    model = train.train_reranker(ALL, train.TrainConfig(epochs=2, batch_size=2), development.graph, development.fit)
    train.save_reranker(tmp_path / "reranker.pt", model, development.graph)

    assert sorted(read) == ["catalog.parquet", "qrels_train.parquet", "queries_train.parquet"]
    assert not any("test" in path.name for path in tmp_path.iterdir())
    assert len(development.fit.queries) == QUERIES - VALIDATION
    assert development.validation_qrels["query_id"].nunique() == VALIDATION


def test_training_is_reproducible_and_changes_the_model():
    development = make_development()
    config = train.TrainConfig(epochs=3, batch_size=2, seed=4)
    first = train.train_reranker(ALL, config, development.graph, development.fit)
    second = train.train_reranker(ALL, config, development.graph, development.fit)

    assert not first.training
    for name, value in first.state_dict().items():
        assert torch.equal(value, second.state_dict()[name]), name
    assert first.correction[-1].weight.abs().sum() > 0  # la corrección dejó de ser cero
    scale = development.fit.features[development.fit.mask]
    assert torch.allclose(first.feature_mean, scale.mean(dim=0))


def test_random_negatives_are_unjudged_irrelevant_and_reproducible():
    data = make_data()
    product_ids = data.catalog["product_id"].to_numpy()
    extended = train.add_random_negatives(data.qrels, product_ids, per_query=4, seed=0)
    added = extended[extended["esci_label"] == train.RANDOM_LABEL]

    assert extended["query_id"].is_monotonic_increasing and (added["gain"] == 0).all()
    assert len(extended) - len(added) == len(data.qrels) and 0 < len(added) <= 4 * QUERIES
    assert not extended.duplicated(["query_id", "product_id"]).any()  # ninguno estaba ya anotado
    assert extended.equals(train.add_random_negatives(data.qrels, product_ids, per_query=4, seed=0))


def test_random_negatives_only_reach_the_fit_lists():
    data = make_data()
    development = make_development(data)
    fit, _ = split_queries(data.queries["query_id"].tolist(), VALIDATION)
    annotated = data.qrels["query_id"].isin(fit).sum()

    assert development.fit.mask.sum() > annotated  # anotados más los irrelevantes al azar
    assert development.validation.mask.sum() == len(development.validation_qrels) == 5 * VALIDATION
    assert edges(development.graph, "exact").shape[1] == 2 * len(fit)  # no añaden aristas
