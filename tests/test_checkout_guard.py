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
