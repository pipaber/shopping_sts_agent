"""Pruebas deterministas del grafo con un LLM guionizado (sin GPU ni modelos)."""

import uuid
from pathlib import Path

import pandas as pd
import pytest
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore

from shopping_agent.agent import graph as agent_graph
from shopping_agent.agent import texts, tools
from shopping_agent.agent.graph import build_graph
from shopping_agent.agent.llm import LLMError, ScriptedLLM
from shopping_agent.agent.memory import open_memory
from shopping_agent.agent.search import CatalogSearch
from shopping_agent.agent.session import ShoppingSession
from shopping_agent.store import ops
from shopping_agent.store.db import SCHEMA, connect

CATALOG = pd.DataFrame(
    [
        # id, título, descripción, viñetas, marca, color
        ("P1", "Auriculares Bluetooth inalámbricos Sony WH-CH520", "Auriculares de diadema ligeros.",
         "Hasta 50 horas de batería. Micrófono integrado.", "Sony", "Negro"),
        ("P2", "Auriculares Bluetooth JBL Tune 510BT", None, "Sonido JBL Pure Bass.", "JBL", None),
        ("P3", "Auriculares Bluetooth con cable Philips", None, None, "Philips", "Blanco"),
        ("P4", "Auriculares Bluetooth deportivos Xiaomi", "Resistentes al sudor.", None, None, "Azul"),
        ("P5", "Cafetera italiana Bialetti 6 tazas", None, "Aluminio.", "Bialetti", None),
        ("P6", "Funda rígida para auriculares Bluetooth", None, None, None, "Negro"),
    ],
    columns=["product_id", "product_title", "product_description", "product_bullet_point",
             "product_brand", "product_color"],
)
# producto: (precio en céntimos, stock)
INVENTORY = {"P1": (2000, 10), "P2": (1500, 3), "P3": (900, 0), "P4": (1200, 8), "P5": (2500, 5), "P6": (500, 20)}


def call(tool, **args):
    return {"motivo": "guion de prueba", "herramienta": tool, **args}


def say(text="Hecho."):
    return call(tools.RESPOND, texto=text)


class Shop:
    """Tienda, búsqueda léxica y grafo con un LLM guionizado."""

    def __init__(self, tmp_path: Path, checkpointer=None, store=None):
        self.db_path = tmp_path / "store.sqlite"
        if not self.db_path.exists():
            conn = connect(self.db_path)
            conn.executescript(SCHEMA)
            conn.executemany(
                "INSERT INTO inventory (product_id, price_cents, stock) VALUES (?, ?, ?)",
                [(product_id, price, stock) for product_id, (price, stock) in INVENTORY.items()],
            )
            conn.close()
        self.llm = ScriptedLLM([])
        self.store = store if store is not None else InMemoryStore()
        self.graph = build_graph(
            self.llm, CatalogSearch.from_catalog(CATALOG), self.db_path, checkpointer or InMemorySaver(), self.store
        )

    def session(self, thread_id="hilo-1", user_id="ana") -> ShoppingSession:
        return ShoppingSession(self.graph, thread_id, user_id)

    def sql(self, query, *params):
        conn = connect(self.db_path)
        try:
            return conn.execute(query, params).fetchall()
        finally:
            conn.close()

    def stock(self, product_id):
        return self.sql("SELECT stock FROM inventory WHERE product_id = ?", product_id)[0][0]

    def orders(self):
        return self.sql("SELECT COUNT(*) FROM orders")[0][0]

    def inventory(self):
        return self.sql("SELECT * FROM inventory ORDER BY product_id")


@pytest.fixture
def shop(tmp_path):
    return Shop(tmp_path)


def cart_of(session):
    return {line["product_id"]: line["quantity"] for line in session.state["cart"]}


def codes(operation):
    return [issue["code"] for issue in operation["issues"]]


# --- Compra completa con confirmación ---------------------------------------------


def test_full_purchase_with_confirmation(shop):
    session = shop.session()
    shop.llm.extend([
        call(tools.SET_BUDGET, importe_eur=50),
        call(tools.SEARCH, consulta="auriculares bluetooth"),
        say("Tengo los Sony por 20 euros y los JBL por 15."),
    ])
    turn = session.send("Busco auriculares bluetooth y tengo 50 euros")
    assert turn.response.startswith("Tengo los Sony")
    assert session.state["budget_cents"] == 5000
    found = [candidate["product_id"] for candidate in session.state["candidates"]]
    assert {"P1", "P2", "P4"} <= set(found) and "P5" not in found
    assert found[-1] == "P3"  # el agotado va detrás de los que se pueden comprar

    shop.llm.extend([call(tools.ADD, product_id="P1", cantidad=2), say("Añadidos.")])
    turn = session.send("Añade dos de los Sony")
    assert cart_of(session) == {"P1": 2}
    # El código añade el contenido exacto del carrito a la respuesta del LLM.
    assert "2 unidades" in turn.response and "40,00 €" in turn.response and "te quedan 10,00 €" in turn.response

    shop.llm.extend([call(tools.QUOTE)])
    turn = session.send("Quiero comprarlo")
    assert turn.awaiting_confirmation
    # Antes de comprar se repiten producto, cantidad e importes.
    for expected in ("2 unidades", "Sony WH-CH520", "20,00 €", "Total: 40,00 €", "¿Lo confirmo?"):
        assert expected in turn.response
    assert shop.orders() == 0 and shop.stock("P1") == 10  # cotizar no compra
    assert session.state["quote"]["total_cents"] == 4000

    calls_before = len(shop.llm.calls)
    turn = session.send("Sí, confirmo")
    assert not turn.awaiting_confirmation
    assert "Pedido número 1 registrado" in turn.response and "40,00 €" in turn.response
    assert shop.orders() == 1 and shop.stock("P1") == 8
    assert cart_of(session) == {} and session.state["quote"] is None
    assert session.state["order"]["total_cents"] == 4000
    assert len(shop.llm.calls) == calls_before  # confirmar y registrar no pasan por el LLM

    # Repetir la confirmación no duplica el pedido ni descuenta otra vez.
    turn = session.send("sí")
    assert "ya estaba registrado" in turn.response
    assert shop.orders() == 1 and shop.stock("P1") == 8
    assert len(shop.llm.calls) == calls_before

    executed = [operation["tool"] for operation in session.state["ops_log"]]
    assert executed == [
        tools.SET_BUDGET, tools.SEARCH, tools.ADD, tools.QUOTE, "confirmar_pedido", "confirmar_pedido",
    ]
    assert [message["role"] for message in session.state["messages"]] == ["user", "assistant"] * 5


def test_order_is_only_registered_after_explicit_yes(shop):
    session = shop.session()
    shop.llm.extend([call(tools.SEARCH, consulta="auriculares"), call(tools.ADD, product_id="P4", cantidad=1), call(tools.QUOTE)])
    assert session.send("Compra unos Xiaomi").awaiting_confirmation

    turn = session.send("No, mejor no")
    assert not turn.awaiting_confirmation and "no registro el pedido" in turn.response
    assert shop.orders() == 0 and cart_of(session) == {"P4": 1}
    assert session.state["quote"] is None

    # Una respuesta que no es un sí limpio se atiende como turno nuevo, sin comprar.
    shop.llm.extend([call(tools.QUOTE)])
    assert session.send("cotiza otra vez").awaiting_confirmation
    shop.llm.extend([call(tools.SET_QUANTITY, product_id="P4", cantidad=2), say("Ahora son dos.")])
    turn = session.send("sí, pero que sean dos")
    assert not turn.awaiting_confirmation
    assert shop.orders() == 0 and cart_of(session) == {"P4": 2}
    assert session.state["quote"] is None  # el cambio invalida la cotización
    assert shop.llm.remaining == 0


# --- Solicitud ambigua que acaba en aclaración ---------------------------------------


def test_ambiguous_request_ends_in_clarification(shop):
    session = shop.session()
    question = "¿Qué tipo de producto buscas para tu hermano?"
    shop.llm.extend([call(tools.CLARIFY, pregunta=question)])
    turn = session.send("Quiero un regalo para mi hermano")
    assert turn.response == question and not turn.awaiting_confirmation
    assert session.state["pending_clarification"] == question
    assert cart_of(session) == {} and shop.orders() == 0

    def search_after_seeing_pending(messages, schema):
        assert "ACLARACIÓN PENDIENTE" in messages[-1]["content"]
        assert question in messages[-1]["content"]
        return call(tools.SEARCH, consulta="auriculares bluetooth")

    shop.llm.extend([search_after_seeing_pending, say("Tengo varios auriculares.")])
    session.send("Unos auriculares bluetooth")
    assert session.state["pending_clarification"] is None
    assert session.state["candidates"]


def test_unidentified_product_is_rejected_by_code_then_clarified(shop):
    session = shop.session()
    shop.llm.extend([call(tools.SEARCH, consulta="auriculares bluetooth"), say()])
    session.send("Busco auriculares")

    def clarify_after_rejection(messages, schema):
        assert tools.UNIDENTIFIED_PRODUCT in messages[-1]["content"]
        return call(tools.CLARIFY, pregunta="¿A cuál de ellos te refieres?")

    # El LLM "inventa" un producto: el código lo rechaza sin tocar la tienda.
    shop.llm.extend([call(tools.ADD, product_id="B000INVENT", cantidad=1), clarify_after_rejection])
    turn = session.send("Añade el rojo")
    assert turn.response == "¿A cuál de ellos te refieres?"
    assert cart_of(session) == {} and shop.sql("SELECT COUNT(*) FROM cart_items")[0][0] == 0
    rejected = turn.operations[0]
    assert not rejected["ok"] and codes(rejected) == [tools.UNIDENTIFIED_PRODUCT]


# --- Cambio de cantidad que conserva el presupuesto ----------------------------------


def test_quantity_change_keeps_budget(shop):
    session = shop.session()
    shop.llm.extend([
        call(tools.SET_BUDGET, importe_eur=50),
        call(tools.SEARCH, consulta="auriculares bluetooth sony"),
        call(tools.ADD, product_id="P1", cantidad=2),
        say(),
    ])
    session.send("Tengo 50 euros, ponme dos auriculares Sony")
    assert cart_of(session) == {"P1": 2}

    def explain_rejection(messages, schema):
        context = messages[-1]["content"]
        assert ops.BUDGET_EXCEEDED in context and "caben como máximo 2 unidades" in context
        return say("Con tu presupuesto caben dos como mucho.")

    # Tres unidades son 60 €: el código lo rechaza y el carrito no cambia.
    shop.llm.extend([call(tools.SET_QUANTITY, product_id="P1", cantidad=3), explain_rejection])
    turn = session.send("Mejor que sean tres")
    assert cart_of(session) == {"P1": 2} and session.state["budget_cents"] == 5000
    assert codes(turn.operations[0]) == [ops.BUDGET_EXCEEDED]

    # El presupuesto fijado dos turnos antes sigue vigente y se aplica al nuevo cambio.
    shop.llm.extend([call(tools.SET_QUANTITY, product_id="P1", cantidad=1), say("Lo dejo en uno.")])
    turn = session.send("Entonces solo uno")
    assert cart_of(session) == {"P1": 1} and session.state["budget_cents"] == 5000
    assert "te quedan 30,00 €" in turn.response

    shop.llm.extend([call(tools.QUOTE)])
    turn = session.send("Cierra el pedido")
    assert turn.awaiting_confirmation and "Tu presupuesto es de 50,00 €" in turn.response
    assert session.state["quote"]["budget_cents"] == 5000
    session.send("sí")
    assert shop.orders() == 1 and shop.stock("P1") == 9


def test_invalid_quantity_never_reaches_the_store(shop):
    session = shop.session()
    shop.llm.extend([
        call(tools.SEARCH, consulta="auriculares bluetooth"),
        call(tools.ADD, product_id="P1", cantidad=0),
        call(tools.ADD, product_id="P1", cantidad=-2),
        call(tools.ADD, product_id="P1", cantidad=1.5),
        say("Necesito una cantidad válida."),
    ])
    turn = session.send("Añade cero auriculares")
    assert cart_of(session) == {} and shop.sql("SELECT COUNT(*) FROM cart_items")[0][0] == 0
    assert [codes(operation) for operation in turn.operations[1:]] == [[ops.INVALID_QUANTITY]] * 3


def test_out_of_stock_product_is_rejected(shop):
    session = shop.session()
    shop.llm.extend([
        call(tools.SEARCH, consulta="auriculares bluetooth philips"),
        call(tools.ADD, product_id="P3", cantidad=1),
        say("Está agotado."),
    ])
    turn = session.send("Quiero los Philips")
    assert cart_of(session) == {} and codes(turn.operations[1]) == [ops.OUT_OF_STOCK]


# --- Stock que cambia antes de confirmar ---------------------------------------------


def quote_three_jbl(shop, session):
    shop.llm.extend([
        call(tools.SEARCH, consulta="auriculares bluetooth jbl"),
        call(tools.ADD, product_id="P2", cantidad=3),
        call(tools.QUOTE),
    ])
    turn = session.send("Quiero tres JBL, ciérralo")
    assert turn.awaiting_confirmation and session.state["quote"]["items"][0]["stock"] == 3


def test_stock_drops_before_confirmation(shop):
    session = shop.session()
    quote_three_jbl(shop, session)
    shop.sql("UPDATE inventory SET stock = 1 WHERE product_id = 'P2'")  # otro cliente compra dos
    before = shop.inventory()

    turn = session.send("sí")
    assert not turn.awaiting_confirmation
    assert shop.orders() == 0 and shop.inventory() == before  # ni pedido ni inventario tocado
    assert session.state.get("order") is None and session.state["quote"] is None
    assert codes(turn.operations[-1]) == [ops.INSUFFICIENT_STOCK]
    # El agente lo detecta, lo explica y propone alternativas con existencias suficientes.
    assert "No he registrado el pedido" in turn.response
    assert "solo queda 1 unidad" in turn.response and "Puedo dejarlo en 1" in turn.response
    alternatives = [candidate["product_id"] for candidate in session.state["candidates"]]
    assert alternatives and "P2" not in alternatives
    assert all(candidate["stock"] >= 3 for candidate in session.state["candidates"])
    assert cart_of(session) == {"P2": 3}  # la decisión es del usuario

    shop.llm.extend([call(tools.SET_QUANTITY, product_id="P2", cantidad=1), call(tools.QUOTE)])
    assert session.send("Déjalo en uno y ciérralo").awaiting_confirmation
    turn = session.send("sí")
    assert "Pedido número 1 registrado" in turn.response
    assert shop.orders() == 1 and shop.stock("P2") == 0


def test_product_sells_out_before_confirmation(shop):
    session = shop.session()
    quote_three_jbl(shop, session)
    shop.sql("UPDATE inventory SET stock = 0 WHERE product_id = 'P2'")

    turn = session.send("sí, confirmo")
    assert shop.orders() == 0 and shop.stock("P2") == 0
    assert "se ha agotado" in turn.response and "Como alternativa tengo" in turn.response
    assert codes(turn.operations[-1]) == [ops.OUT_OF_STOCK]

    # La alternativa propuesta se puede comprar a continuación.
    option = session.state["candidates"][0]["product_id"]
    shop.llm.extend([
        call(tools.REMOVE, product_id="P2"),
        call(tools.ADD, product_id=option, cantidad=3),
        call(tools.QUOTE),
    ])
    assert session.send("Vale, cámbialo por el primero").awaiting_confirmation
    session.send("sí")
    assert shop.orders() == 1 and shop.stock(option) == INVENTORY[option][1] - 3


# --- Reglas que impone el código --------------------------------------------------------


def test_missing_catalog_fields_are_shown_as_unknown(shop):
    session = shop.session()
    seen = {}

    def remember(messages, schema):
        seen["context"], seen["schema"] = messages[-1]["content"], schema
        return say()

    shop.llm.extend([call(tools.SEARCH, consulta="auriculares bluetooth jbl"), remember])
    session.send("Busco unos JBL")
    jbl = next(c for c in session.state["candidates"] if c["product_id"] == "P2")
    assert jbl["color"] is None and jbl["description"] is None and jbl["brand"] == "JBL"
    line = next(row for row in seen["context"].splitlines() if "id=P2" in row)
    assert "color: desconocido" in line and "descripción: desconocido" in line and "marca: JBL" in line
    assert "precio: 15,00 €" in line and "existencias: 3" in line

    # El esquema solo deja nombrar productos conocidos.
    ids = [candidate["product_id"] for candidate in session.state["candidates"]]
    add = next(o for o in seen["schema"]["anyOf"] if o["properties"]["herramienta"]["const"] == tools.ADD)
    assert add["properties"]["product_id"] == {"enum": ids}


def test_response_with_invented_number_is_rejected_by_code(shop):
    session = shop.session()
    shop.llm.extend([call(tools.SEARCH, consulta="auriculares bluetooth sony"), say("Tengo los Sony por 20 euros.")])
    session.send("Busco auriculares Sony")

    def corrected(messages, schema):
        assert tools.UNGROUNDED_NUMBER in messages[-1]["content"] and "(30)" in messages[-1]["content"]
        return say("Según el catálogo, hasta 50 horas de batería.")

    # "30 horas" no aparece en ningún dato; "50 horas" sí está en las características.
    shop.llm.extend([say("Los Sony tienen 30 horas de batería."), corrected])
    turn = session.send("¿Cuánta batería tienen los Sony?")
    assert turn.response == "Según el catálogo, hasta 50 horas de batería."
    assert codes(turn.operations[0]) == [tools.UNGROUNDED_NUMBER]

    # Si insiste, el turno acaba con la respuesta de respaldo, nunca con la cifra inventada.
    shop.llm.extend([say("Pesan 250 gramos."), say("Pesan 250 gramos.")])
    assert session.send("¿Cuánto pesan?").response == texts.FALLBACK


def test_llm_cannot_claim_an_order_that_does_not_exist(shop):
    session = shop.session()
    shop.llm.extend([call(tools.SEARCH, consulta="auriculares xiaomi"), call(tools.ADD, product_id="P4", cantidad=1), say()])
    session.send("Añade unos Xiaomi")

    # El LLM "cierra" la compra de palabra: el código lo rechaza y le exige cotizar.
    shop.llm.extend([say("Perfecto, tu pedido está listo. ¡Gracias por tu compra!"), call(tools.QUOTE)])
    turn = session.send("Ciérralo")
    assert codes(turn.operations[0]) == [tools.FALSE_ORDER_CLAIM]
    assert turn.awaiting_confirmation and "¿Lo confirmo?" in turn.response
    assert shop.orders() == 0

    session.send("sí")
    shop.llm.extend([say("Sí, tu pedido número 1 está registrado.")])
    assert session.send("¿Está hecho mi pedido?").response.startswith("Sí, tu pedido número 1")


def test_numbers_in_ignores_identifiers_and_normalizes_formats():
    assert tools.numbers_in("id=B08K91F1M4 a 45,70 € (45.7), Bluetooth 5.0, IP7, 500ml, 3 unidades") == {
        "45.7", "5", "500", "3",
    }


def test_schema_without_known_products_has_no_product_tools():
    names = {option["properties"]["herramienta"]["const"] for option in tools.decision_schema([])["anyOf"]}
    assert names == {tools.SEARCH, tools.SET_BUDGET, tools.SAVE_PREFERENCE, tools.QUOTE, tools.CLARIFY, tools.RESPOND}
    assert "confirmar_pedido" not in names  # el LLM no tiene forma de registrar un pedido


def test_quote_with_empty_cart_is_rejected(shop):
    session = shop.session()
    shop.llm.extend([call(tools.QUOTE), say("No hay nada en el carrito.")])
    turn = session.send("Cierra el pedido")
    assert not turn.awaiting_confirmation and codes(turn.operations[0]) == [ops.EMPTY_CART]


def test_turn_ends_after_step_limit_or_llm_failure(shop):
    session = shop.session()
    shop.llm.extend([call(tools.SEARCH, consulta=f"auriculares {n}") for n in range(agent_graph.MAX_STEPS + 3)])
    turn = session.send("Busca sin parar")
    assert turn.response == texts.FALLBACK
    assert len(shop.llm.calls) == agent_graph.MAX_STEPS

    def broken(messages, schema):
        raise LLMError("JSON incompleto")

    shop.llm.script = [broken]
    assert session.send("hola").response == texts.FALLBACK
    assert session.send("   ").response == texts.EMPTY_INPUT


def test_preferences_follow_the_user_across_conversations(shop):
    first = shop.session("hilo-a", "ana")
    shop.llm.extend([call(tools.SAVE_PREFERENCE, preferencia="color negro"), say()])
    first.send("Me gustan las cosas negras")
    assert first.state["preferences"] == ["color negro"]

    def sees_preference(messages, schema):
        assert "PREFERENCIAS: color negro" in messages[-1]["content"]
        return say()

    shop.llm.extend([sees_preference])
    second = shop.session("hilo-b", "ana")
    second.send("hola")
    assert second.state["preferences"] == ["color negro"]
    assert second.state.get("budget_cents") is None  # el presupuesto es de cada compra

    shop.llm.extend([say()])
    other = shop.session("hilo-c", "luis")
    other.send("hola")
    assert not other.state.get("preferences")


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("sí", "si"), ("Sí, confirmo.", "si"), ("vale, adelante", "si"), ("Sí, confirma el pedido por favor", "si"),
        ("de acuerdo", "si"), ("ok", "si"),
        ("no", "no"), ("No, cancela", "no"), ("mejor no", "no"), ("todavía no", "no"),
        ("sí, pero que sean tres", "otro"), ("no, cambia la cantidad a dos", "otro"), ("¿cuánto cuesta?", "otro"),
        ("", "otro"), ("sí no", "otro"), ("el pedido", "otro"),
    ],
)
def test_classify_confirmation(text, expected):
    assert tools.classify_confirmation(text) == expected


def test_agent_never_reads_relevance_labels():
    sources = Path(agent_graph.__file__).parent.glob("*.py")
    assert not [path.name for path in sources if "qrels" in path.read_text(encoding="utf-8")]


# --- Persistencia en Postgres ------------------------------------------------------------


def test_pending_confirmation_survives_restart_with_postgres(tmp_path, pg_url):
    thread_id, user_id = f"test-{uuid.uuid4().hex}", f"test-{uuid.uuid4().hex}"
    try:
        with open_memory(pg_url) as memory:
            shop = Shop(tmp_path, memory.checkpointer, memory.store)
            session = shop.session(thread_id, user_id)
            shop.llm.extend([
                call(tools.SET_BUDGET, importe_eur=50),
                call(tools.SEARCH, consulta="auriculares bluetooth"),
                call(tools.ADD, product_id="P1", cantidad=2),
                call(tools.QUOTE),
            ])
            assert session.send("Dos Sony con 50 euros, ciérralo").awaiting_confirmation

        # Proceso "nuevo": otro pool, otro grafo y un LLM sin guion.
        with open_memory(pg_url) as memory:
            shop = Shop(tmp_path, memory.checkpointer, memory.store)
            session = shop.session(thread_id, user_id)
            assert session.awaiting_confirmation
            assert session.state["budget_cents"] == 5000 and cart_of(session) == {"P1": 2}
            turn = session.send("sí")
            assert "Pedido número 1 registrado" in turn.response
            assert shop.orders() == 1 and shop.stock("P1") == 8
    finally:
        with open_memory(pg_url) as memory:
            memory.checkpointer.delete_thread(thread_id)
