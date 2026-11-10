"""Comprobaciones de un escenario: código que mira la tienda y el estado del agente.

Ningún veredicto lo da un LLM. Cada comprobación recibe una :class:`View` (la
instantánea tomada al terminar el turno, el propio turno y los productos con
nombre) y devuelve si se cumple y un detalle legible para la ficha.

Las que miran el texto de la respuesta (``offered_alternative``,
``declares_unknown``, ``mentions_price``, ``response_contains``) buscan cifras,
marcas o expresiones concretas: son deterministas, pero una respuesta correcta
dicha de otra forma puede no pasarlas. La ficha conserva el texto para revisarlo.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from shopping_agent.agent.guards import numbers_in
from shopping_agent.eval.voice import normalize

Snapshot = dict[str, Any]
Outcome = tuple[bool, str]

CLARIFY_TOOL = "pedir_aclaracion"
# Formas de decir que un dato no está en el catálogo, sobre el texto ya normalizado.
_UNKNOWN = re.compile(
    r"\bno (consta|indica|aparece|figura|especifica|menciona|incluye|dispongo|tengo|hay|proporciona|ofrece|da|puedo"
    r"|se|lo se|esta disponible|viene|trae|cuento|dice|detalla|facilita)\b|\bdesconoc|\bsin (informacion|datos)\b"
)


@dataclass(frozen=True)
class View:
    """Lo que una comprobación puede mirar."""

    snapshot: Snapshot  # estado del agente, tienda y ofertas al terminar el turno
    turn: dict[str, Any] | None  # el turno comprobado: respuesta y operaciones
    names: Mapping[str, str]  # productos con nombre (``remember``)
    product_text: Callable[[str], str]  # todo el texto del catálogo de un producto


@dataclass(frozen=True)
class CheckSpec:
    params: tuple[str, ...]
    run: Callable[[View, dict[str, Any]], Outcome]


# --- Lectura de una instantánea ---------------------------------------------------------


def cart_lines(snapshot: Snapshot) -> list[dict[str, Any]]:
    """Líneas del carrito de la conversación, tal como están en la tienda."""
    items = snapshot["store"]["cart_items"]
    return [
        {"product_id": item["product_id"], "quantity": item["quantity"]}
        for item in items
        if item["cart_id"] == snapshot["cart_id"]
    ]


def order_lines(snapshot: Snapshot, order_id: int) -> list[dict[str, Any]]:
    return [item for item in snapshot["store"]["order_items"] if item["order_id"] == order_id]


def resolve(ref: str, view: View) -> str | None:
    """``@nombre``, ``candidate:N`` o ``cart:N`` → identificador del producto, si existe."""
    if ref.startswith("@"):
        return view.names.get(ref[1:])
    kind, _, position = ref.partition(":")
    lines = {"candidate": view.snapshot["state"]["candidates"], "cart": cart_lines(view.snapshot)}.get(kind)
    if lines is None or not position.isdigit() or not 1 <= int(position) <= len(lines):
        return None
    return lines[int(position) - 1]["product_id"]


def price_figure(cents: int) -> str:
    """Un precio en la forma canónica de ``numbers_in``: 1450 → "14.5"."""
    return f"{cents / 100:g}"


# --- Líneas esperadas -------------------------------------------------------------------


def _line_matches(spec: dict[str, Any], line: dict[str, Any], view: View) -> bool:
    """``{"product": ref, "quantity": n}`` o ``{"not": ref, "quantity": n}`` (cualquier otro producto)."""
    if line["quantity"] != spec["quantity"]:
        return False
    if "product" in spec:
        return line["product_id"] == resolve(spec["product"], view)
    excluded = resolve(spec["not"], view)
    return excluded is not None and line["product_id"] != excluded


def match_lines(expected: Sequence[dict[str, Any]], actual: Sequence[dict[str, Any]], view: View) -> bool:
    """¿Son las líneas reales exactamente las esperadas, sin importar el orden?"""
    remaining = list(actual)
    for spec in sorted(expected, key=lambda spec: "product" not in spec):  # primero las de producto fijo
        found = next((line for line in remaining if _line_matches(spec, line, view)), None)
        if found is None:
            return False
        remaining.remove(found)
    return not remaining


def _describe(lines: Sequence[dict[str, Any]]) -> str:
    return ", ".join(f"{line['quantity']} × {line['product_id']}" for line in lines) or "vacío"


# --- Comprobaciones sobre la tienda y el estado ---------------------------------------------


def _budget(view: View, params: dict[str, Any]) -> Outcome:
    actual = view.snapshot["state"]["budget_cents"]
    return actual == params["cents"], f"presupuesto en el estado: {actual}"


def _cart(view: View, params: dict[str, Any]) -> Outcome:
    actual = cart_lines(view.snapshot)
    expected = [] if params.get("empty") else params["lines"]
    return match_lines(expected, actual, view), f"carrito: {_describe(actual)}"


def _orders(view: View, params: dict[str, Any]) -> Outcome:
    count = len(view.snapshot["store"]["orders"])
    return count == params["count"], f"pedidos registrados: {count}"


def _order(view: View, params: dict[str, Any]) -> Outcome:
    """El último pedido tiene exactamente esas líneas (y ese total, si se indica)."""
    orders = view.snapshot["store"]["orders"]
    if not orders:
        return False, "no hay ningún pedido"
    last = orders[-1]
    lines = order_lines(view.snapshot, last["order_id"])
    total_ok = "total_cents" not in params or last["total_cents"] == params["total_cents"]
    detail = f"pedido {last['order_id']}: {_describe(lines)}; total {last['total_cents']} céntimos"
    return match_lines(params["lines"], lines, view) and total_ok, detail


def _stock(view: View, params: dict[str, Any]) -> Outcome:
    product = resolve(params["product"], view)
    offer = view.snapshot["offers"].get(product) if product else None
    if offer is None:
        return False, f"no se pudo resolver {params['product']}"
    return offer["stock"] == params["equals"], f"existencias de {product}: {offer['stock']}"


def _preference(view: View, params: dict[str, Any]) -> Outcome:
    preferences = view.snapshot["state"]["preferences"]
    wanted = normalize(params["contains"])
    return any(wanted in normalize(item) for item in preferences), f"preferencias: {preferences}"


def _awaiting_confirmation(view: View, params: dict[str, Any]) -> Outcome:
    waiting = view.snapshot["state"]["awaiting_confirmation"]
    return waiting == params["value"], f"esperando confirmación: {'sí' if waiting else 'no'}"


# --- Comprobaciones sobre el turno --------------------------------------------------------


def _operations(view: View) -> list[dict[str, Any]]:
    return view.turn["operations"] if view.turn else []


def _response(view: View) -> str:
    return view.turn["response"] if view.turn else ""


def _asked_clarification(view: View, params: dict[str, Any]) -> Outcome:
    asked = any(operation["tool"] == CLARIFY_TOOL and operation["ok"] for operation in _operations(view))
    return asked, "pidió aclaración" if asked else "no pidió aclaración"


def _rejected(view: View, params: dict[str, Any]) -> Outcome:
    """Alguna operación del turno se rechazó con ese código."""
    codes = [issue["code"] for operation in _operations(view) if not operation["ok"] for issue in operation["issues"]]
    return params["code"] in codes, f"rechazos del turno: {codes or 'ninguno'}"


def _offered_alternative(view: View, params: dict[str, Any]) -> Outcome:
    """La respuesta cita, por su precio o por su marca, otro candidato con existencias."""
    avoided = resolve(params["instead_of"], view)
    figures, said = numbers_in(_response(view)), f" {normalize(_response(view))} "
    offers = view.snapshot["offers"]
    cited = [
        candidate["product_id"]
        for candidate in view.snapshot["state"]["candidates"]
        if candidate["product_id"] != avoided
        and offers[candidate["product_id"]]["stock"] > 0
        and (
            price_figure(offers[candidate["product_id"]]["price_cents"]) in figures
            or bool(candidate["brand"] and f" {normalize(candidate['brand'])} " in said)
        )
    ]
    return bool(avoided and cited), f"alternativas con existencias citadas: {cited or 'ninguna'}"


def _declares_unknown(view: View, params: dict[str, Any]) -> Outcome:
    """Si el catálogo no trae el dato, la respuesta debe decir que no consta; si lo
    trae, no puede decir que no consta."""
    product = resolve(params["product"], view)
    if product is None:
        return False, f"no se pudo resolver {params['product']}"
    catalog = normalize(view.product_text(product))
    in_catalog = any(normalize(keyword) in catalog for keyword in params["keywords"])
    says_unknown = bool(_UNKNOWN.search(normalize(_response(view))))
    detail = f"dato en el catálogo: {'sí' if in_catalog else 'no'}; la respuesta dice que no consta: {'sí' if says_unknown else 'no'}"
    return says_unknown != in_catalog, detail


def _mentions_price(view: View, params: dict[str, Any]) -> Outcome:
    product = resolve(params["product"], view)
    offer = view.snapshot["offers"].get(product) if product else None
    if offer is None:
        return False, f"no se pudo resolver {params['product']}"
    figure = price_figure(offer["price_cents"])
    return figure in numbers_in(_response(view)), f"precio en la tienda: {figure} €"


def _response_contains(view: View, params: dict[str, Any]) -> Outcome:
    found = normalize(params["text"]) in normalize(_response(view))
    return found, f"la respuesta {'contiene' if found else 'no contiene'} «{params['text']}»"


CHECKS: dict[str, CheckSpec] = {
    "budget": CheckSpec(("cents",), _budget),
    "cart": CheckSpec(("lines", "empty"), _cart),
    "orders": CheckSpec(("count",), _orders),
    "order": CheckSpec(("lines", "total_cents"), _order),
    "stock": CheckSpec(("product", "equals"), _stock),
    "preference": CheckSpec(("contains",), _preference),
    "awaiting_confirmation": CheckSpec(("value",), _awaiting_confirmation),
    "asked_clarification": CheckSpec((), _asked_clarification),
    "rejected": CheckSpec(("code",), _rejected),
    "offered_alternative": CheckSpec(("instead_of",), _offered_alternative),
    "declares_unknown": CheckSpec(("product", "keywords"), _declares_unknown),
    "mentions_price": CheckSpec(("product",), _mentions_price),
    "response_contains": CheckSpec(("text",), _response_contains),
}


def run_check(name: str, params: dict[str, Any], view: View) -> dict[str, Any]:
    """Resultado de una comprobación, en la forma que se guarda en la corrida."""
    try:
        ok, detail = CHECKS[name].run(view, params)
    except (KeyError, TypeError) as error:  # parámetros que faltan o una referencia sin resolver
        ok, detail = False, f"no se pudo comprobar: {error!r}"
    return {"check": name, "params": params, "ok": ok, "detail": detail}
