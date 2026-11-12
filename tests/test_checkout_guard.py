"""Guarda del cierre: si el usuario pide cerrar la compra, el turno no acaba sin cotizar."""

import pytest

from shopping_agent.agent import guards, prompt, tools
from test_agent import Shop, call, cart_of, codes, say


@pytest.mark.parametrize(
    "text",
    [
        "Ciérralo.", "Cierra el pedido", "Vale, pues quiero cerrar el pedido.", "Ahora sí, cierra el pedido.",
        "Eso es todo.", "Quiero pagar", "Finaliza la compra", "Ya puedes tramitarlo", "Hazme el pedido", "Quiero comprarlo",
    ],
)
def test_messages_that_ask_to_close_the_purchase(text):
    assert guards.wants_checkout(text)


@pytest.mark.parametrize(
    "text",
    [
        "Quiero comprar un regalo", "Busco una bolsa que cierre bien", "No cierres el pedido todavía", "Espera, no quiero pagar aún",
        "¿Puedo pagar con tarjeta?", "Añade dos del primero", "Mejor que sean cuatro", "Sí", "No, cancélalo.",
    ],
)
def test_messages_that_do_not(text):
    assert not guards.wants_checkout(text)


@pytest.fixture
def with_cart(tmp_path):
    shop = Shop(tmp_path)
    session = shop.session()
    shop.llm.extend([call(tools.SEARCH, consulta="auriculares bluetooth"), say("Tengo varios."), call(tools.ADD, product_id="P1", cantidad=2), say()])
    session.send("Busco auriculares bluetooth")
    session.send("Añade dos de los Sony")
    return shop, session


def test_an_answer_instead_of_a_quote_is_sent_back_to_the_llm(with_cart):
    shop, session = with_cart
    shop.llm.extend([say("Tienes dos unidades en el carrito. ¿Algo más?"), call(tools.QUOTE)])
    turn = session.send("Ciérralo.")
    assert codes(turn.operations[0]) == [guards.MUST_QUOTE] and turn.awaiting_confirmation
    assert "¿Lo confirmo?" in turn.response and shop.orders() == 0
    assert "el paso es cotizar" in next(m["content"] for m in shop.llm.calls[-1][0] if "MENSAJE DEL USUARIO" in m["content"])


def test_the_reminder_is_given_once_and_never_buys(with_cart):
    shop, session = with_cart
    shop.llm.extend([say("Tienes dos unidades en el carrito."), say("¿Quieres cambiar algo antes?")])
    turn = session.send("Eso es todo.")
    assert not turn.awaiting_confirmation and turn.response.startswith("¿Quieres cambiar algo antes?")
    assert shop.orders() == 0 and cart_of(session) == {"P1": 2}


def test_no_reminder_without_a_cart_or_after_a_store_rejection(tmp_path, with_cart):
    folder = tmp_path / "otra"
    folder.mkdir()
    empty = Shop(folder)
    empty.llm.extend([say("El carrito está vacío.")])
    assert empty.session().send("Cierra el pedido").response == "El carrito está vacío."

    shop, session = with_cart
    shop.llm.extend([call(tools.ADD, product_id="P1", cantidad=30), say("No hay tantas unidades.")])
    turn = session.send("Añade treinta más de los Sony y cierra el pedido")
    assert not turn.awaiting_confirmation and turn.response.startswith("No hay tantas unidades.")


def test_hint_only_when_there_is_something_to_close():
    line = {"product_id": "P1", "title": "x", "quantity": 1, "unit_price_cents": 100, "subtotal_cents": 100, "stock": 3}
    assert prompt.checkout_hint("Ciérralo.", [line]) and not prompt.checkout_hint("Ciérralo.", [])
    assert not prompt.checkout_hint("Quiero comprar un regalo", [line])


# --- Oferta pendiente tras rechazarse la confirmación -----------------------------------


def context_seen(shop):
    return next(m["content"] for m in shop.llm.calls[-1][0] if "MENSAJE DEL USUARIO" in m["content"])


def test_after_a_rejected_confirmation_the_llm_sees_what_was_offered(with_cart):
    shop, session = with_cart
    shop.llm.extend([call(tools.QUOTE)])
    session.send("Cierra el pedido")
    shop.sql("UPDATE inventory SET stock = 1 WHERE product_id = 'P1'")
    turn = session.send("Sí")
    assert "Puedo dejarlo en 1" in turn.response and shop.orders() == 0

    shop.llm.extend([call(tools.SET_QUANTITY, product_id="P1", cantidad=1), say()])
    session.send("Vale, déjalo en una")
    offer = context_seen(shop)
    assert "OFERTA PENDIENTE" in offer and "cambiar_cantidad" in offer and "id=P1 en 1 unidad" in offer
    assert "alternativas, que ahora son los CANDIDATOS" in offer
    assert cart_of(session) == {"P1": 1}

    shop.llm.extend([say("Dime.")])
    session.send("Una cosa más")
    assert "OFERTA PENDIENTE" not in context_seen(shop)  # solo vale para el turno siguiente


def test_sold_out_offer_says_the_product_is_still_in_the_cart():
    assert prompt.pending_offer([("P1", 0)], alternatives=False) == "id=P1 está agotado y sigue en el carrito."


def test_after_a_rejected_quantity_the_llm_sees_how_many_fit(with_cart):
    shop, session = with_cart  # dos Sony (P1) en el carrito; quedan 10 y cuestan 20 €
    shop.llm.extend([call(tools.ADD, product_id="P1", cantidad=20), say("No hay tantas.")])
    session.send("Añade veinte más de los Sony")
    shop.llm.extend([call(tools.ADD, product_id="P1", cantidad=8), say()])
    session.send("Pues ponme las que queden")
    offer = context_seen(shop)
    assert "OFERTA PENDIENTE" in offer and "agregar_al_carrito de id=P1 por falta de existencias; caben 8 unidades" in offer
    assert cart_of(session) == {"P1": 10}

    shop.llm.extend([call(tools.SET_BUDGET, importe_eur=250), call(tools.SET_QUANTITY, product_id="P2", cantidad=1), say("No está en el carrito.")])
    session.send("Tengo 250 euros; deja uno de los JBL")
    shop.llm.extend([say("Dime.")])
    session.send("Vale")
    assert "OFERTA PENDIENTE" not in context_seen(shop)  # ese rechazo no dice cuántas caben


def test_budget_rejection_offers_the_quantity_that_fits(tmp_path):
    shop = Shop(tmp_path)
    session = shop.session()
    shop.llm.extend([call(tools.SET_BUDGET, importe_eur=50), call(tools.SEARCH, consulta="auriculares bluetooth"), say("Tengo varios.")])
    session.send("Busco auriculares bluetooth y tengo 50 euros")
    shop.llm.extend([call(tools.ADD, product_id="P1", cantidad=3), say("No cabe en tu presupuesto.")])
    session.send("Añade tres de los Sony")
    shop.llm.extend([call(tools.ADD, product_id="P1", cantidad=2), say()])
    session.send("Pues los que quepan")
    assert "porque no cabe en el presupuesto; caben 2 unidades" in context_seen(shop) and cart_of(session) == {"P1": 2}


@pytest.mark.parametrize("text", ["Tengo 40 euros.", "Mi presupuesto es de sesenta", "No quiero gastar más de 50", "Mi tope son 30", "Hasta 20 €"])
def test_messages_that_speak_of_money(text):
    assert guards.mentions_money(text)


@pytest.mark.parametrize("text", ["No, espera, he dicho 12, no 2.", "Perdona, eran 14, no 4.", "Mejor que sean 3", "Añade 2 del primero", "Sí"])
def test_messages_with_bare_numbers_do_not(text):
    assert not guards.mentions_money(text)


def test_a_bare_number_with_a_cart_is_not_taken_for_a_budget(with_cart):
    shop, session = with_cart
    shop.llm.extend([call(tools.SET_BUDGET, importe_eur=8), call(tools.SET_QUANTITY, product_id="P1", cantidad=8), say()])
    turn = session.send("No, espera, he dicho 8, no 2.")
    assert codes(turn.operations[0]) == [guards.UNSTATED_BUDGET] and session.state.get("budget_cents") is None
    assert cart_of(session) == {"P1": 8} and "presupuesto" not in turn.response.lower()


def test_a_budget_goes_through_when_money_is_mentioned_or_was_asked_about(with_cart):
    shop, session = with_cart
    shop.llm.extend([call(tools.SET_BUDGET, importe_eur=500), say()])
    session.send("Por cierto, no quiero gastar más de 500 euros.")
    assert session.state["budget_cents"] == 50000
    shop.llm.extend([call(tools.CLARIFY, pregunta="¿Cuál es tu presupuesto ahora?"), call(tools.SET_BUDGET, importe_eur=600), say()])
    session.send("Cámbialo.")
    session.send("600")
    assert session.state["budget_cents"] == 60000


def test_without_a_cart_a_bare_number_can_be_a_budget(tmp_path):
    shop = Shop(tmp_path)
    session = shop.session()
    shop.llm.extend([call(tools.SET_BUDGET, importe_eur=40), say()])
    session.send("Busco una mochila, como mucho 40.")
    assert session.state["budget_cents"] == 4000


LINE = {"product_id": "P1", "title": "Auriculares", "quantity": 2, "unit_price_cents": 2000, "subtotal_cents": 4000, "stock": 10}


def test_hint_says_bare_numbers_are_not_an_amount_when_there_is_a_cart():
    hint = prompt.units_hint("No, espera, he dicho 12, no 2.", [LINE], None)
    assert "(12, 2)" in hint and "cambiar_cantidad" in hint
    assert prompt.units_hint("No, espera, he dicho 12, no 2.", [], None) == ""
    assert prompt.units_hint("No, espera, he dicho doce, no dos.", [LINE], None) == ""
    assert prompt.units_hint("Mejor baja mi presupuesto a 25 euros.", [LINE], None) == ""
    assert prompt.units_hint("600", [LINE], "¿Cuál es tu presupuesto ahora?") == ""


@pytest.mark.parametrize("text", ["Añade dos del producto con código ZX-999.", "¿El de 2.4G tiene USB 3.0?", "¿Cuesta 19,99?"])
def test_codes_models_and_decimals_are_not_bare_numbers(text):
    assert prompt.units_hint(text, [LINE], None) == ""


def test_the_llm_sees_the_hint_in_its_turn_context(with_cart):
    shop, session = with_cart
    shop.llm.extend([call(tools.SET_QUANTITY, product_id="P1", cantidad=8), say()])
    session.send("No, espera, he dicho 8, no 2.")
    assert "no son un importe" in context_seen(shop) and cart_of(session) == {"P1": 8}
