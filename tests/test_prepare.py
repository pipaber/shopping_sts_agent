import pandas as pd
import pytest

from shopping_agent.data.prepare import (
    EXAMPLES_FILE,
    GAINS,
    PRODUCTS_FILE,
    prepare,
    select_queries,
)

N_QUERIES = 400  # por split
PER_QUERY = 10


@pytest.fixture(scope="module")
def raw_dir(tmp_path_factory):
    """ESCI sintético: 400 consultas por split en español, más ruido de otros locales."""
    raw = tmp_path_factory.mktemp("raw")
    labels = list(GAINS)
    examples, products = [], []
    for split_index, split in enumerate(("train", "test")):
        for q in range(N_QUERIES):
            query_id = split_index * N_QUERIES + q
            for k in range(PER_QUERY):
                product_id = f"ES{query_id:04d}{k:02d}"
                examples.append((f"consulta {query_id}", query_id, product_id, "es", labels[k % 4], 1, split))
                products.append((product_id, f"Producto {product_id}", "desc", "viñeta", "marca", "rojo", "es"))
    # Ruido: otro locale y fuera de la versión reducida.
    examples.append(("us query", 9000, "US000001", "us", "E", 1, "train"))
    examples.append(("consulta grande", 9001, "ES000000", "es", "E", 0, "train"))
    products.append(("ES000000", "US title for same id", "d", "b", "brand", "red", "us"))

    pd.DataFrame(
        examples,
        columns=["query", "query_id", "product_id", "product_locale", "esci_label", "small_version", "split"],
    ).to_parquet(raw / EXAMPLES_FILE, index=False)
    pd.DataFrame(
        products,
        columns=[
            "product_id",
            "product_title",
            "product_description",
            "product_bullet_point",
            "product_brand",
            "product_color",
            "product_locale",
        ],
    ).to_parquet(raw / PRODUCTS_FILE, index=False)
    return raw


def read_all(out):
    names = ["catalog", "queries_train", "queries_test", "qrels_train", "qrels_test"]
    return {name: pd.read_parquet(out / f"{name}.parquet") for name in names}


def test_prepare_outputs(raw_dir, tmp_path):
    stats = prepare(raw_dir, tmp_path, n_train=350, n_test=250, seed=1)
    data = read_all(tmp_path)

    assert stats == {"catalog": 6000, "train_queries": 350, "test_queries": 250, "judgments": 6000}
    assert data["catalog"]["product_id"].is_unique
    assert data["catalog"]["product_title"].str.startswith("Producto").all()  # solo locale es

    train_ids, test_ids = set(data["queries_train"]["query_id"]), set(data["queries_test"]["query_id"])
    assert not train_ids & test_ids
    assert max(train_ids) < N_QUERIES <= min(test_ids)  # cada consulta en su split original

    catalog_ids = set(data["catalog"]["product_id"])
    for split in ("train", "test"):
        qrels = data[f"qrels_{split}"]
        assert set(qrels["product_id"]) <= catalog_ids
        assert (qrels["gain"] == qrels["esci_label"].map(GAINS)).all()


def test_prepare_is_deterministic(raw_dir, tmp_path):
    prepare(raw_dir, tmp_path / "a", n_train=350, n_test=250, seed=1)
    prepare(raw_dir, tmp_path / "b", n_train=350, n_test=250, seed=1)
    a, b = read_all(tmp_path / "a"), read_all(tmp_path / "b")
    for name in a:
        pd.testing.assert_frame_equal(a[name], b[name])


def test_prepare_rejects_small_configurations(raw_dir, tmp_path):
    with pytest.raises(ValueError, match="consultas de evaluación"):
        prepare(raw_dir, tmp_path, n_train=350, n_test=100, seed=1)
    with pytest.raises(ValueError, match="catálogo"):
        prepare(raw_dir, tmp_path, n_train=10, n_test=200, seed=1)


def test_queries_with_missing_products_are_not_eligible():
    examples = pd.DataFrame(
        {
            "query_id": [1, 1, 2, 2, 3, 3],
            "query": ["a", "a", "b", "b", "c", "c"],
            "product_id": ["p1", "p2", "p3", "MISSING", "p4", "p5"],
            "esci_label": ["E"] * 6,
            "split": ["train"] * 4 + ["test"] * 2,
        }
    )
    selected = select_queries(examples, {"p1", "p2", "p3", "p4", "p5"}, n_train=1, n_test=1, seed=0)
    assert set(selected["query_id"]) == {1, 3}
    with pytest.raises(ValueError, match="elegibles"):
        select_queries(examples, {"p1", "p2", "p3", "p4", "p5"}, n_train=2, n_test=1, seed=0)
