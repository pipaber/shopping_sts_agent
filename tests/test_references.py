"""Referencias a un candidato por su posición: lo que nombra el mensaje y la guarda
que impide al LLM añadir otro producto. Con el LLM guionizado, sin GPU."""

import pytest

from shopping_agent.agent import references, tools
from test_agent import Shop, call, cart_of, codes, say


@pytest.fixture
def searched(tmp_path):
    """Una conversación con candidatos ya buscados: (tienda, sesión, ids en orden)."""
    shop = Shop(tmp_path)
    session = shop.session()
    shop.llm.extend([call(tools.SEARCH, consulta="auriculares bluetooth"), say("Tengo varios.")])
    session.send("Busco auriculares bluetooth")
    return shop, session, [candidate["product_id"] for candidate in session.state["candidates"]]


def context_seen(shop):
    """El estado del turno tal como lo recibió el LLM en su última llamada."""
    return next(message["content"] for message in shop.llm.calls[-1][0] if "MENSAJE DEL USUARIO" in message["content"])


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Añade dos del primero", [1]),
        ("Ponme una de la Segunda.", [2]),
        ("Compárame el primero con el tercero", [1, 3]),
        ("Añade dos del séptimo.", [7]),
        ("¿Y el último está disponible?", [5]),
        ("el primer resultado y la primera opción", [1]),
        ("Primero busca auriculares y luego ya veremos", []),
        ("Añade dos más", []),
    ],
)
def test_positions_named_in_a_message(text, expected):
    assert references.positions(text, listed=5) == expected


def test_position_beyond_the_list_ends_in_a_question_not_in_another_product(searched):
    shop, session, ids = searched
    shop.llm.extend([
        call(tools.ADD, product_id=ids[0], cantidad=2),
        call(tools.CLARIFY, pregunta="Solo hay cinco. ¿Cuál quieres?"),
    ])
    turn = session.send("Añade dos del séptimo.")
    assert codes(turn.operations[0]) == [references.NO_SUCH_POSITION] and "pedir_aclaracion" in turn.operations[0]["summary"]
    assert cart_of(session) == {} and turn.response.startswith("Solo hay cinco")
    # El LLM ve el aviso antes de decidir.
    assert "el mensaje nombra el séptimo" in context_seen(shop)


def test_adding_a_candidate_the_user_did_not_point_at_is_rejected(searched):
    shop, session, ids = searched
    shop.llm.extend([call(tools.ADD, product_id=ids[1], cantidad=1), call(tools.ADD, product_id=ids[0], cantidad=1), say()])
    turn = session.send("Ponme uno del primero.")
    assert codes(turn.operations[0]) == [references.OTHER_PRODUCT] and turn.operations[1]["ok"]
    assert cart_of(session) == {ids[0]: 1}
    assert f"el primero es [1] id={ids[0]}" in context_seen(shop)


def test_after_a_rejection_the_agent_cannot_swap_the_product_on_its_own(searched):
    shop, session, ids = searched
    shop.sql("UPDATE inventory SET stock = 0 WHERE product_id = ?", ids[0])
    shop.llm.extend([
        call(tools.ADD, product_id=ids[0], cantidad=1),  # la tienda: agotado
        call(tools.ADD, product_id=ids[1], cantidad=1),  # el LLM intenta colar el segundo
        say("Ese está agotado. ¿Te vale otro?"),
    ])
    turn = session.send("Ponme uno del primero.")
    assert [codes(operation) for operation in turn.operations[:2]] == [["agotado"], [references.OTHER_PRODUCT]]
    assert cart_of(session) == {}


def test_a_product_named_by_brand_can_be_added_next_to_a_pointed_one(searched):
    shop, session, ids = searched
    sony = next(c["product_id"] for c in session.state["candidates"] if c["brand"] == "Sony")
    first = ids[0] if ids[0] != sony else ids[1]
    position = "primero" if first == ids[0] else "segundo"
    shop.llm.extend([call(tools.ADD, product_id=first, cantidad=1), call(tools.ADD, product_id=sony, cantidad=1), say()])
    session.send(f"Añade uno del {position} y otro de los Sony.")
    assert cart_of(session) == {first: 1, sony: 1}


def test_questions_and_cart_changes_are_not_tied_to_the_position(searched):
    shop, session, ids = searched
    shop.llm.extend([call(tools.ADD, product_id=ids[0], cantidad=1), call(tools.ADD, product_id=ids[1], cantidad=1), say()])
    session.send("Añade uno del primero y uno del segundo.")
    shop.llm.extend([call(tools.REMOVE, product_id=ids[1]), say()])
    session.send("Quita el primero.")  # qué quitar del carrito lo decide el LLM: aquí no hay guarda
    assert cart_of(session) == {ids[0]: 1}
    shop.llm.extend([call(tools.PRICE_STOCK, product_id=ids[2]), say("Sí, quedan.")])
    turn = session.send("¿El segundo está disponible?")
    assert turn.operations[0]["ok"]  # consultar otro candidato no se rechaza; añadirlo, sí


def test_internal_rejections_are_not_read_to_the_user(searched):
    shop, session, ids = searched
    shop.llm.extend([call(tools.ADD, product_id=ids[0], cantidad=2)] * 2)  # insiste: el turno acaba con el respaldo
    turn = session.send("Añade dos del séptimo.")
    assert "pedir_aclaracion" not in turn.response and cart_of(session) == {}


# --- Búsqueda repetida ------------------------------------------------------------------


def test_a_search_that_returns_the_same_candidates_is_sent_back(searched):
    shop, session, ids = searched
    shop.llm.extend([call(tools.SEARCH, consulta="auriculares bluetooth"), say("El catálogo no indica ese dato.")])
    turn = session.send("¿Qué valoración le dan los clientes al segundo?")
    assert codes(turn.operations[0]) == [tools.REPEATED_SEARCH] and "detalle_producto" in turn.operations[0]["summary"]
    assert turn.response == "El catálogo no indica ese dato."
    assert [candidate["product_id"] for candidate in session.state["candidates"]] == ids


def test_a_search_with_other_results_goes_through(searched):
    shop, session, ids = searched
    shop.llm.extend([call(tools.SEARCH, consulta="cafetera italiana"), say("Tengo una Bialetti.")])
    turn = session.send("Mejor busca una cafetera italiana")
    assert turn.operations[0]["ok"] and session.state["candidates"][0]["product_id"] == "P5"
    shop.sql("UPDATE inventory SET stock = 0 WHERE product_id = 'P5'")
    shop.llm.extend([call(tools.SEARCH, consulta="auriculares bluetooth"), say("Estos son.")])
    assert session.send("Vuelve a los auriculares").operations[0]["ok"]
