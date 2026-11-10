"""Los nodos y las herramientas, uno a uno: sin compilar el grafo ni usar LLM."""

from typing import Literal, get_args, get_type_hints

import numpy as np
import pytest
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from langgraph.types import Command

from shopping_agent.agent import graph as agent_graph
from shopping_agent.agent import guards, texts, tools
from shopping_agent.agent.deps import Deps
from shopping_agent.agent.llm import LLMError, ScriptedLLM
from shopping_agent.agent.nodes import actions, checkout, turn
from shopping_agent.agent.search import CatalogSearch
from shopping_agent.agent.state import AgentState, IssueRecord, Message, Order, new_turn
from shopping_agent.store import ops
from test_agent import CATALOG, Shop, call, say

CONFIG = {"configurable": {"thread_id": "hilo-nodos", "user_id": "ana"}}


@pytest.fixture
def shop(tmp_path):
    return Shop(tmp_path)


@pytest.fixture
def deps(shop):
    return Deps(shop.llm, shop.search, shop.db_path, InMemoryStore())


def candidates(deps, *product_ids):
    with deps.shop() as conn:
        return [deps.candidate(conn, product_id) for product_id in product_ids]


def searched(deps, **fields):
    """Estado tras una búsqueda de auriculares: P1 a P4 como candidatos."""
    return AgentState(candidates=candidates(deps, "P1", "P2", "P3", "P4"), turn=1, **fields)


# --- Estado -------------------------------------------------------------------------


def test_state_has_a_default_for_every_field():
    state = AgentState()
    assert state.cart == [] and state.candidates == [] and state.steps == [] and state.messages == []
    assert state.budget_cents is None and state.quote is None and state.order is None
    assert state.decision == {} and state.response == "" and state.turn == 0
    assert AgentState().cart is not state.cart  # cada estado tiene sus propias listas


def test_new_turn_clears_the_work_of_the_previous_one():
    state = AgentState(turn=3, steps=[{"tool": "x"}], cart_changed=True, response="antes", decision=say())
    update = new_turn(state, "hola")
    assert update["messages"] == [{"role": "user", "content": "hola"}]
    assert update["turn"] == 4 and update["steps"] == [] and update["decision"] == {}
    assert update["cart_changed"] is False and update["response"] == "" and update["confirm_issues"] == []


# --- Registro de herramientas -----------------------------------------------------


def test_every_tool_is_declared_once_with_everything_it_needs():
    assert len(tools.TOOLS) == 12
    for name, tool in tools.TOOLS.items():
        assert tool.name == name and tool.doc.startswith("(")
        if tool.node == "validar":  # pasa por validar → ejecutar_herramienta
            assert tool.validate is not None and tool.run is not None
        else:  # la atiende su propio nodo del grafo
            assert tool.validate is None and tool.run is None
            assert tool.node in agent_graph.BRANCHES["interpretar"]
    assert all(f"- {name} {tool.doc}" in tools.SYSTEM_PROMPT for name, tool in tools.TOOLS.items())


def test_schema_offers_product_tools_only_with_known_products():
    def names(known_ids):
        return [option["properties"]["herramienta"]["const"] for option in tools.decision_schema(known_ids)["anyOf"]]

    without = [tools.SEARCH, tools.SET_BUDGET, tools.SAVE_PREFERENCE, tools.QUOTE, tools.CLARIFY, tools.RESPOND]
    with_one = [tools.DETAIL, tools.PRICE_STOCK, tools.ADD, tools.SET_QUANTITY, tools.REMOVE]
    assert names([]) == without
    assert names(["P1"]) == without + with_one
    assert names(["P1", "P2"]) == without + with_one + [tools.COMPARE]
    add = next(o for o in tools.decision_schema(["P1"])["anyOf"] if o["properties"]["herramienta"]["const"] == tools.ADD)
    assert add["properties"]["product_id"] == {"enum": ["P1"]} and add["required"][-1] == "cantidad"


@pytest.mark.parametrize(
    "name, args, codes",
    [
        (tools.ADD, {"product_id": "P1", "cantidad": 2}, []),
        (tools.ADD, {"product_id": "P9", "cantidad": 0}, [tools.UNIDENTIFIED_PRODUCT, ops.INVALID_QUANTITY]),
        (tools.COMPARE, {"product_ids": ["P1", "P1"]}, [tools.INVALID_ARGS]),
        (tools.COMPARE, {"product_ids": ["P1", "P9"]}, [tools.UNIDENTIFIED_PRODUCT]),
        (tools.SET_BUDGET, {"importe_eur": -5}, [ops.INVALID_BUDGET]),
        (tools.SAVE_PREFERENCE, {"preferencia": "  "}, [tools.INVALID_ARGS]),
        (tools.QUOTE, {}, [tools.UNKNOWN_TOOL]),  # no pasa por validar: tiene su propio nodo
        ("borrar_tienda", {}, [tools.UNKNOWN_TOOL]),
    ],
)
def test_validate_call(deps, name, args, codes):
    state = searched(deps)
    assert [issue.code for issue in tools.validate_call(name, args, state)] == codes


def run_tool(deps, state, name, **args):
    with deps.shop() as conn:
        return tools.TOOLS[name].run(tools.ToolCall(args, state, deps, conn, "hilo-nodos", "ana"))


def test_cart_tools_report_the_cart_and_invalidate_the_quote(deps, shop):
    outcome = run_tool(deps, searched(deps, budget_cents=5000), tools.ADD, product_id="P1", cantidad=2)
    assert outcome.ok and outcome.result == {"total_cents": 4000}
    assert outcome.update["cart_changed"] is True and outcome.update["quote"] is None
    assert [(line["product_id"], line["quantity"]) for line in outcome.update["cart"]] == [("P1", 2)]
    assert "Así queda el carrito" in outcome.summary

    over = run_tool(deps, searched(deps, budget_cents=5000), tools.SET_QUANTITY, product_id="P1", cantidad=3)
    assert not over.ok and [issue.code for issue in over.issues] == [ops.BUDGET_EXCEEDED]
    assert "cart_changed" not in over.update and over.update["cart"][0]["quantity"] == 2  # el carrito no cambió
    assert shop.sql("SELECT quantity FROM cart_items") == [(2,)]


def test_budget_and_preference_tools_only_touch_the_conversation(deps, shop):
    outcome = run_tool(deps, AgentState(), tools.SET_BUDGET, importe_eur=45.5)
    assert outcome.update == {"budget_cents": 4550, "quote": None, "budget_changed": True}
    saved = run_tool(deps, AgentState(preferences=["color negro"]), tools.SAVE_PREFERENCE, preferencia=" marca Sony ")
    assert saved.update == {"preferences": ["color negro", "marca Sony"]}
    assert deps.saved_preferences("ana") == ["color negro", "marca Sony"]
    assert shop.sql("SELECT COUNT(*) FROM cart_items") == [(0,)]


def test_detail_shows_more_text_than_compare(deps):
    detail = run_tool(deps, searched(deps), tools.DETAIL, product_id="P1")
    compare = run_tool(deps, searched(deps), tools.COMPARE, product_ids=["P1", "P2", "P1"])
    assert detail.result == ["P1"] and compare.result == ["P1", "P2"]  # sin repetir
    assert "Hasta 50 horas de batería" in detail.summary and "color: desconocido" in compare.summary


# --- Búsqueda -----------------------------------------------------------------------


class CaseSensitiveScorer:
    """Como el modelo denso: da otra puntuación si cambia una mayúscula."""

    def __init__(self, products):
        self.products = products
        self.queries = []

    def score(self, queries):
        self.queries += queries
        return np.array([[hash((query, product)) % 1000 for product in range(self.products)] for query in queries], dtype=float)


def test_search_does_not_depend_on_the_case_of_the_query():
    dense = CaseSensitiveScorer(len(CATALOG))
    search = CatalogSearch.from_catalog(CATALOG, dense)
    lower = search.rank("auriculares bluetooth deporte")
    assert search.rank("Auriculares Bluetooth deporte") == search.rank("AURICULARES BLUETOOTH DEPORTE") == lower
    assert lower and set(dense.queries) == {"auriculares bluetooth deporte"}  # al denso le llega en minúsculas
    assert search.rank("   ") == []


# --- Nodos de la conversación -------------------------------------------------------


def test_iniciar_turno_syncs_with_the_shop_and_routes(deps, shop):
    with deps.shop() as conn:
        ops.add_to_cart(conn, "hilo-nodos", "P1", 1)
    state = AgentState(user_input="  ¿cuánto cuesta el primero?  ", candidates=candidates(deps, "P2"))
    shop.sql("UPDATE inventory SET stock = 1 WHERE product_id = 'P2'")

    command = turn.iniciar_turno(state, CONFIG, deps=deps)
    assert command.goto == "interpretar"
    assert command.update["messages"] == [{"role": "user", "content": "¿cuánto cuesta el primero?"}]
    assert command.update["cart"][0]["product_id"] == "P1"
    assert command.update["candidates"][0]["stock"] == 1  # existencias de ahora, no las de la búsqueda
    assert "CARRITO:" in command.update["turn_context"] and "id=P2" in command.update["turn_context"]

    empty = turn.iniciar_turno(AgentState(user_input="   "), CONFIG, deps=deps)
    assert empty.goto == "responder" and empty.update["response"] == texts.EMPTY_INPUT


def test_iniciar_turno_sends_a_repeated_yes_straight_to_the_order(deps):
    order = Order(order_id=1, quote_id="q1", items=[], total_cents=2000, message="Pedido número 1 registrado.")
    history = [Message(role="assistant", content=order["message"])]
    repeated = AgentState(user_input="sí", order=order, messages=history)
    assert turn.iniciar_turno(repeated, CONFIG, deps=deps).goto == "registrar_pedido"
    other = AgentState(user_input="sí, y busca una funda", order=order, messages=history)
    assert turn.iniciar_turno(other, CONFIG, deps=deps).goto == "interpretar"


@pytest.mark.parametrize(
    "decision, goto",
    [
        (call(tools.SEARCH, consulta="auriculares"), "recuperar"),
        (call(tools.ADD, product_id="P1", cantidad=1), "validar"),
        (call(tools.QUOTE), "cotizar"),
        (call(tools.CLARIFY, pregunta="¿Cuál?"), "pedir_aclaracion"),
        (say("Hecho."), "validar_respuesta"),
        (say("   "), "responder"),  # sin texto no hay nada que validar: respuesta de respaldo
        (call("borrar_tienda"), "validar"),  # una herramienta inventada la rechaza validar
    ],
)
def test_interpretar_routes_each_decision_to_its_node(deps, shop, decision, goto):
    shop.llm.extend([decision])
    command = turn.interpretar(searched(deps, turn_context="CANDIDATOS"), deps=deps)
    assert command.goto == goto and command.update["decision"] == decision
    assert goto in agent_graph.BRANCHES["interpretar"]


def test_interpretar_falls_back_when_the_llm_cannot_decide(deps, shop):
    rejection = IssueRecord(code=ops.OUT_OF_STOCK, message="No quedan unidades.", product_id="P3", details={})
    previous = {"turn": 1, "tool": tools.ADD, "args": {"product_id": "P3", "cantidad": 1}, "reason": "", "ok": False,
                "summary": "", "result": None, "issues": [rejection]}

    def broken(messages, schema):
        raise LLMError("JSON incompleto")

    for scripted in (broken, call(tools.ADD, product_id="P3", cantidad=1)):  # el LLM falla / repite el paso
        shop.llm.extend([scripted])
        command = turn.interpretar(searched(deps, steps=[previous]), deps=deps)
        assert command.goto == "responder"
        assert command.update["response"] == texts.could_not_complete(["No quedan unidades."])

    exhausted = searched(deps, steps=[{**previous, "issues": []}] * turn.MAX_STEPS)
    assert turn.interpretar(exhausted, deps=deps).update["response"] == texts.FALLBACK
    assert shop.llm.remaining == 0  # agotados los pasos, ni se le pregunta


def test_validar_respuesta_sends_unsupported_claims_back_to_the_llm():
    context = "CANDIDATOS:\n[1] id=P1 | precio: 20,00 €"
    grounded = AgentState(response="Cuesta 20 euros.", turn_context=context, decision=say("Cuesta 20 euros."))
    assert turn.validar_respuesta(grounded).goto == "responder"

    invented = AgentState(response="Dura 30 horas.", turn_context=context, decision=say("Dura 30 horas."))
    command = turn.validar_respuesta(invented)
    assert command.goto == "interpretar"
    assert command.update["steps"][0]["issues"][0]["code"] == guards.UNGROUNDED_NUMBER
    assert command.update["ops_log"] == command.update["steps"]


def test_pedir_aclaracion_and_responder_close_the_turn(deps):
    asked = turn.pedir_aclaracion(AgentState(decision=call(tools.CLARIFY, pregunta="¿Cuántas\nunidades?")))
    assert asked["response"] == asked["pending_clarification"] == "¿Cuántas unidades?"
    assert asked["messages"] == [{"role": "assistant", "content": "¿Cuántas unidades?"}]

    with deps.shop() as conn:
        ops.add_to_cart(conn, "hilo-nodos", "P1", 2)
        cart = deps.cart(conn, "hilo-nodos")
    plain = turn.responder(AgentState(response="Hecho.", cart=cart))
    assert plain["response"] == "Hecho." and plain["pending_clarification"] is None
    changed = turn.responder(AgentState(response="Hecho.", cart=cart, cart_changed=True, budget_cents=5000))
    assert changed["response"] == f"Hecho. {texts.cart_summary(cart, 5000)}"
    budget_only = turn.responder(AgentState(response="Vale.", budget_changed=True, budget_cents=5000))
    assert budget_only["response"] == "Vale. He anotado un presupuesto de 50,00 €."
    assert turn.responder(AgentState())["response"] == texts.FALLBACK


# --- Nodos de las acciones ----------------------------------------------------------


def test_recuperar_puts_buyable_products_first(deps):
    state = AgentState(decision=call(tools.SEARCH, consulta=" auriculares bluetooth "), budget_cents=1600, turn=1)
    update = actions.recuperar(state, deps=deps)
    shown = update["candidates"]
    assert update["last_query"] == "auriculares bluetooth"
    affordable = [c["product_id"] for c in shown if c["stock"] > 0 and c["price_cents"] <= 1600]
    assert [c["product_id"] for c in shown][: len(affordable)] == affordable  # los comprables, delante
    assert {"P1", "P3"} <= {c["product_id"] for c in shown}  # caro y agotado siguen, detrás
    assert update["steps"][0]["result"] == [c["product_id"] for c in shown]

    empty = actions.recuperar(AgentState(decision=call(tools.SEARCH, consulta="  ")), deps=deps)
    assert empty["steps"][0]["issues"][0]["code"] == tools.INVALID_ARGS and "candidates" not in empty


def test_buyable_first_only_reorders_the_first_results(deps):
    ranked = candidates(deps, "P3", "P1", "P2")  # agotado, 20 €, 15 €
    assert [c["product_id"] for c in actions.buyable_first(ranked, None)] == ["P1", "P2", "P3"]
    assert [c["product_id"] for c in actions.buyable_first(ranked, 1600)] == ["P2", "P3", "P1"]


def test_validar_and_ejecutar_herramienta(deps, shop):
    wrong = searched(deps, decision=call(tools.ADD, product_id="P9", cantidad=1))
    rejected = actions.validar(wrong)
    assert rejected.goto == "interpretar" and not rejected.update["steps"][0]["ok"]

    right = searched(deps, decision=call(tools.ADD, product_id="P2", cantidad=1))
    accepted = actions.validar(right)
    assert isinstance(accepted, Command) and accepted.goto == "ejecutar_herramienta" and accepted.update is None
    update = actions.ejecutar_herramienta(right, CONFIG, deps=deps)
    assert update["cart_changed"] is True and update["steps"][0]["tool"] == tools.ADD
    assert shop.sql("SELECT product_id, quantity FROM cart_items") == [("P2", 1)]


# --- Nodos del cierre de la compra --------------------------------------------------


def quoted(deps, product_id="P2", quantity=2, **fields):
    """Estado justo después de cotizar ``quantity`` unidades de un producto."""
    with deps.shop() as conn:
        ops.add_to_cart(conn, "hilo-nodos", product_id, quantity)
        cart = deps.cart(conn, "hilo-nodos")
    state = AgentState(cart=cart, decision=call(tools.QUOTE), turn=2, **fields)
    command = checkout.cotizar(state, CONFIG, deps=deps)
    return AgentState(cart=cart, quote=command.update["quote"], turn=2, **fields), command


def test_cotizar_repeats_the_order_and_waits_for_confirmation(deps):
    _, command = quoted(deps, budget_cents=5000)
    quote = command.update["quote"]
    assert command.goto == "confirmar" and quote["total_cents"] == 3000
    assert command.update["response"] == quote["message"] and quote["message"].startswith("Te repito el pedido")

    empty = checkout.cotizar(AgentState(decision=call(tools.QUOTE)), {"configurable": {"thread_id": "vacio"}}, deps=deps)
    assert empty.goto == "interpretar" and empty.update["steps"][0]["issues"][0]["code"] == ops.EMPTY_CART


def test_registrar_pedido_is_idempotent(deps, shop):
    state, _ = quoted(deps)
    first = checkout.registrar_pedido(state, CONFIG, deps=deps)
    assert first.goto == "responder" and shop.orders() == 1 and shop.stock("P2") == 1
    order = first.update["order"]
    assert order["message"].startswith("Pedido número 1 registrado") and first.update["quote"] is None

    again = checkout.registrar_pedido(AgentState(order=order, turn=3), CONFIG, deps=deps)
    assert again.goto == "responder" and shop.orders() == 1 and shop.stock("P2") == 1
    assert again.update["order"]["message"] == texts.order_already_registered(1, 3000)
    assert again.update["ops_log"][0]["summary"] == "el pedido ya estaba registrado; no se duplicó"


def test_stock_change_after_the_quote_leads_to_alternatives(deps, shop):
    state, _ = quoted(deps, budget_cents=5000)
    shop.sql("UPDATE inventory SET stock = 1 WHERE product_id = 'P2'")
    failed = checkout.registrar_pedido(state, CONFIG, deps=deps)
    assert failed.goto == "proponer_alternativa" and shop.orders() == 0
    issues = failed.update["confirm_issues"]
    assert [issue["code"] for issue in issues] == [ops.INSUFFICIENT_STOCK]

    update = checkout.proponer_alternativa(AgentState(cart=state.cart, budget_cents=5000, confirm_issues=issues), deps=deps)
    response = update["response"]
    assert response.startswith(texts.NOT_REGISTERED) and response.endswith(texts.WHAT_NEXT)
    assert "solo queda 1 unidad y habías pedido 2" in response and "Como alternativa tengo" in response
    offered = [option["product_id"] for option in update["candidates"]]
    assert offered and "P2" not in offered and len(offered) <= checkout.ALTERNATIVES
    assert all(option["stock"] >= 2 and option["price_cents"] * 2 <= 5000 for option in update["candidates"])


def test_proponer_alternativa_offers_a_new_quote_when_only_the_price_changed(deps):
    issue = IssueRecord(code=ops.PRICE_CHANGED, message="El precio de un producto ha cambiado.", product_id="P1", details={})
    update = checkout.proponer_alternativa(AgentState(confirm_issues=[issue]), deps=deps)
    assert update == {
        "response": f"{texts.NOT_REGISTERED} El precio de un producto ha cambiado. {texts.NEW_QUOTE_OFFER} {texts.WHAT_NEXT}"
    }


# --- Cableado ---------------------------------------------------------------------


def test_graph_wiring_matches_what_each_node_declares(shop):
    """Los destinos de BRANCHES son los que cada nodo declara en su tipo de retorno."""
    functions = {**vars(turn), **vars(actions), **vars(checkout)}
    for name, destinations in agent_graph.BRANCHES.items():
        declared = get_type_hints(functions[name])["return"]
        assert set(get_args(get_args(declared)[0])) == set(destinations), name
        assert get_args(declared)[0].__origin__ is Literal

    graph = build = agent_graph.build_graph(ScriptedLLM([]), shop.search, shop.db_path, InMemorySaver())
    edges = {(edge.source, edge.target) for edge in graph.get_graph().edges}
    expected = {(source, target) for source, targets in agent_graph.BRANCHES.items() for target in targets}
    expected |= {("__start__" if s == "__start__" else s, "__end__" if t == "__end__" else t) for s, t in agent_graph.EDGES.items()}
    assert edges == expected
    assert set(build.get_graph().nodes) - {"__start__", "__end__"} == set(agent_graph.BRANCHES) | set(agent_graph.EDGES) - {"__start__"}
