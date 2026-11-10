"""Herramientas que el LLM puede proponer.

Cada herramienta se declara una sola vez en :data:`TOOLS`: su nombre, lo que el
LLM lee sobre ella, el esquema de sus argumentos, la validación previa y la
función que la ejecuta. El LLM solo elige una y sus argumentos; el esquema
restringe lo que puede escribir y el código comprueba el resto.

No existe una herramienta para registrar el pedido: eso solo ocurre cuando el
usuario confirma la cotización.
"""

from __future__ import annotations

import math
import sqlite3
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from shopping_agent.agent import prompt
from shopping_agent.agent.deps import Deps
from shopping_agent.agent.state import AgentState, Candidate, Update, cart_total
from shopping_agent.store import ops
from shopping_agent.store.ops import Issue, OpResult, format_eur

# Códigos de rechazo propios del agente (los de la tienda están en store.ops).
UNKNOWN_TOOL = "herramienta_desconocida"
INVALID_ARGS = "argumentos_invalidos"
UNIDENTIFIED_PRODUCT = "producto_no_identificado"

SEARCH = "buscar_productos"
DETAIL = "detalle_producto"
COMPARE = "comparar"
PRICE_STOCK = "consultar_precio_stock"
ADD = "agregar_al_carrito"
SET_QUANTITY = "cambiar_cantidad"
REMOVE = "quitar_del_carrito"
SET_BUDGET = "fijar_presupuesto"
SAVE_PREFERENCE = "guardar_preferencia"
QUOTE = "cotizar"
CLARIFY = "pedir_aclaracion"
RESPOND = "responder"

DETAIL_CHARS = (1600, 800)  # viñetas y descripción de un producto
COMPARE_CHARS = (600, 300)  # por producto al comparar varios

Args = dict[str, Any]
Schema = dict[str, Any]


@dataclass(frozen=True)
class ToolCall:
    """Lo que una herramienta tiene a mano al ejecutarse."""

    args: Args
    state: AgentState
    deps: Deps
    conn: sqlite3.Connection  # la tienda
    cart_id: str
    user_id: str


@dataclass(frozen=True)
class ToolOutcome:
    ok: bool
    summary: str  # lo que vuelve al LLM como resultado
    result: Any = None
    issues: tuple[Issue, ...] = ()
    update: Update = field(default_factory=dict)  # cambios en el estado de la conversación


@dataclass(frozen=True)
class Tool:
    name: str
    doc: str  # lo que el LLM lee sobre ella en sus instrucciones
    node: str  # nodo del grafo que atiende la decisión
    params: Callable[[list[str]], Schema]  # esquema de los argumentos, dados los productos conocidos
    min_products: int = 0  # productos conocidos que hacen falta para ofrecerla
    validate: Callable[[Args, set[str]], list[Issue]] | None = None
    run: Callable[[ToolCall], ToolOutcome] | None = None  # ``None``: la ejecuta su propio nodo


# --- Esquemas de los argumentos -------------------------------------------------------

_TEXT: Schema = {"type": "string", "minLength": 1}


def _no_params(known_ids: list[str]) -> Schema:
    return {}


def _text_param(name: str) -> Callable[[list[str]], Schema]:
    return lambda known_ids: {name: _TEXT}


def _product_param(known_ids: list[str]) -> Schema:
    return {"product_id": {"enum": known_ids}}


def _product_and_quantity(known_ids: list[str]) -> Schema:
    return {"product_id": {"enum": known_ids}, "cantidad": {"type": "integer"}}


def _products_param(known_ids: list[str]) -> Schema:
    return {"product_ids": {"type": "array", "items": {"enum": known_ids}, "minItems": 2, "maxItems": 4}}


def _amount_param(known_ids: list[str]) -> Schema:
    return {"importe_eur": {"type": "number"}}


# --- Validación previa a la tienda ----------------------------------------------------
# No consulta la tienda: existencias y presupuesto los decide ``store.ops`` dentro de
# la transacción. Cada función devuelve los rechazos (ninguno si se puede ejecutar).


def budget_to_cents(amount: object) -> int | None:
    """Euros (número) → céntimos. ``None`` si no es un importe positivo."""
    if isinstance(amount, bool) or not isinstance(amount, (int, float)) or not math.isfinite(amount):
        return None
    cents = round(amount * 100)
    return cents if cents > 0 else None


def _product_issues(product_id: object, known: set[str]) -> list[Issue]:
    if isinstance(product_id, str) and product_id in known:
        return []
    message = (
        f"El producto {product_id!r} no está entre los candidatos ni en el carrito. "
        "Hay que buscarlo primero o preguntar al usuario a cuál se refiere."
    )
    return [Issue(UNIDENTIFIED_PRODUCT, message)]


def _check_product(args: Args, known: set[str]) -> list[Issue]:
    return _product_issues(args.get("product_id"), known)


def _check_product_and_quantity(args: Args, known: set[str]) -> list[Issue]:
    invalid = ops.check_quantity(args.get("cantidad"))
    return _check_product(args, known) + ([invalid] if invalid else [])


def _check_products(args: Args, known: set[str]) -> list[Issue]:
    ids = args.get("product_ids")
    if not isinstance(ids, list) or not 2 <= len(set(map(str, ids))) <= 4:
        return [Issue(INVALID_ARGS, "Para comparar hacen falta entre 2 y 4 productos distintos.")]
    return [issue for product_id in ids for issue in _product_issues(product_id, known)]


def _check_amount(args: Args, known: set[str]) -> list[Issue]:
    amount = args.get("importe_eur")
    if budget_to_cents(amount) is not None:
        return []
    return [Issue(ops.INVALID_BUDGET, f"El presupuesto debe ser un importe mayor que cero (se recibió {amount!r}).")]


def _check_preference(args: Args, known: set[str]) -> list[Issue]:
    preference = args.get("preferencia")
    if isinstance(preference, str) and 0 < len(preference.strip()) <= 200:
        return []
    return [Issue(INVALID_ARGS, "La preferencia debe ser un texto breve.")]


# --- Ejecución ------------------------------------------------------------------------
# Las herramientas llegan aquí ya validadas.


def _rejected(issues: tuple[Issue, ...], **update: Any) -> ToolOutcome:
    return ToolOutcome(False, prompt.rejection(issues), issues=issues, update=update)


def _shown(products: list[Candidate]) -> ToolOutcome:
    summary = "\n" + "\n".join(prompt.candidate_line(index, product) for index, product in enumerate(products, 1))
    return ToolOutcome(True, summary, result=[product["product_id"] for product in products])


def _detail(call: ToolCall) -> ToolOutcome:
    return _shown([call.deps.priced(call.conn, call.args["product_id"], *DETAIL_CHARS)])


def _compare(call: ToolCall) -> ToolOutcome:
    ids = list(dict.fromkeys(call.args["product_ids"]))
    return _shown([call.deps.priced(call.conn, product_id, *COMPARE_CHARS) for product_id in ids])


def _price_stock(call: ToolCall) -> ToolOutcome:
    offer = ops.price_and_stock(call.conn, call.args["product_id"])
    if not offer.ok:
        return _rejected(offer.issues)
    stock = offer.data["stock"]
    summary = (
        f"precio {format_eur(offer.data['price_cents'])}; "
        + (f"quedan {stock} unidades." if stock else "agotado.")
        + " Esta herramienta no da características: para color, batería, medidas u otros datos"
        " del producto usa detalle_producto."
    )
    return ToolOutcome(True, summary, result=offer.data)


def _cart_changed(call: ToolCall, result: OpResult) -> ToolOutcome:
    """Resultado común de las tres herramientas que tocan el carrito."""
    cart = call.deps.cart(call.conn, call.cart_id)
    if not result.ok:
        return _rejected(result.issues, cart=cart)
    summary = f"hecho. Así queda el carrito.\n{prompt.render_cart(cart)}"
    # Cualquier cambio en el carrito invalida la cotización anterior.
    update = {"cart": cart, "quote": None, "cart_changed": True}
    return ToolOutcome(True, summary, result={"total_cents": cart_total(cart)}, update=update)


def _add(call: ToolCall) -> ToolOutcome:
    args, budget = call.args, call.state.budget_cents
    return _cart_changed(call, ops.add_to_cart(call.conn, call.cart_id, args["product_id"], args["cantidad"], budget))


def _set_quantity(call: ToolCall) -> ToolOutcome:
    args, budget = call.args, call.state.budget_cents
    return _cart_changed(call, ops.set_quantity(call.conn, call.cart_id, args["product_id"], args["cantidad"], budget))


def _remove(call: ToolCall) -> ToolOutcome:
    return _cart_changed(call, ops.remove_from_cart(call.conn, call.cart_id, call.args["product_id"]))


def _set_budget(call: ToolCall) -> ToolOutcome:
    cents = budget_to_cents(call.args["importe_eur"])
    assert cents is not None  # lo garantiza la validación
    total = cart_total(call.state.cart)
    summary = f"presupuesto fijado en {format_eur(cents)}."
    if total > cents:
        summary += f" Aviso: el carrito suma {format_eur(total)} y lo supera en {format_eur(total - cents)}."
    update = {"budget_cents": cents, "quote": None, "budget_changed": True}
    return ToolOutcome(True, summary, result={"budget_cents": cents}, update=update)


def _save_preference(call: ToolCall) -> ToolOutcome:
    preference = call.args["preferencia"].strip()
    preferences = list(dict.fromkeys([*call.state.preferences, preference]))
    call.deps.save_preferences(call.user_id, preferences)
    return ToolOutcome(True, "preferencia guardada.", result=preferences, update={"preferences": preferences})


# --- Registro -------------------------------------------------------------------------
# El orden es el de las instrucciones del LLM.

_VALIDATED = "validar"  # las que pasan por validar → ejecutar_herramienta

_ALL = (
    Tool(
        SEARCH,
        "(consulta) Busca en el catálogo. `consulta` son palabras clave en español: tipo de "
        "producto y, si se conocen, marca, color o uso. Úsala cuando el usuario pida un producto nuevo.",
        node="recuperar",
        params=_text_param("consulta"),
    ),
    Tool(
        DETAIL,
        "(product_id) Devuelve el texto completo del catálogo para un producto.",
        node=_VALIDATED,
        params=_product_param,
        min_products=1,
        validate=_check_product,
        run=_detail,
    ),
    Tool(
        COMPARE,
        "(product_ids) Devuelve lado a lado los datos de 2 a 4 productos.",
        node=_VALIDATED,
        params=_products_param,
        min_products=2,
        validate=_check_products,
        run=_compare,
    ),
    Tool(
        PRICE_STOCK,
        "(product_id) Precio y existencias actuales de un producto.",
        node=_VALIDATED,
        params=_product_param,
        min_products=1,
        validate=_check_product,
        run=_price_stock,
    ),
    Tool(
        ADD,
        "(product_id, cantidad) Añade unidades de un producto al carrito.",
        node=_VALIDATED,
        params=_product_and_quantity,
        min_products=1,
        validate=_check_product_and_quantity,
        run=_add,
    ),
    Tool(
        SET_QUANTITY,
        "(product_id, cantidad) Deja un producto del carrito con esa cantidad exacta.",
        node=_VALIDATED,
        params=_product_and_quantity,
        min_products=1,
        validate=_check_product_and_quantity,
        run=_set_quantity,
    ),
    Tool(
        REMOVE,
        "(product_id) Quita un producto del carrito.",
        node=_VALIDATED,
        params=_product_param,
        min_products=1,
        validate=_check_product,
        run=_remove,
    ),
    Tool(
        SET_BUDGET,
        "(importe_eur) Guarda el gasto máximo que dice el usuario, en euros.",
        node=_VALIDATED,
        params=_amount_param,
        validate=_check_amount,
        run=_set_budget,
    ),
    Tool(
        SAVE_PREFERENCE,
        "(preferencia) Guarda un gusto duradero del usuario (marca, color, talla…).",
        node=_VALIDATED,
        params=_text_param("preferencia"),
        validate=_check_preference,
        run=_save_preference,
    ),
    Tool(
        QUOTE,
        "() Prepara la cotización del carrito y pide la confirmación al usuario. Úsala cuando "
        "el usuario quiera comprar, pagar o cerrar el pedido.",
        node="cotizar",
        params=_no_params,
    ),
    Tool(
        CLARIFY,
        "(pregunta) Hace una pregunta al usuario cuando falta un dato o hay ambigüedad.",
        node="pedir_aclaracion",
        params=_text_param("pregunta"),
    ),
    Tool(
        RESPOND,
        "(texto) Respuesta final del turno, en español, para leer en voz alta.",
        node="responder",
        params=_text_param("texto"),
    ),
)
TOOLS: dict[str, Tool] = {tool.name: tool for tool in _ALL}
SYSTEM_PROMPT = prompt.system_prompt({tool.name: tool.doc for tool in _ALL})


def known_product_ids(state: AgentState) -> list[str]:
    """Productos a los que el LLM puede referirse: candidatos y carrito, sin repetir."""
    ids = [candidate["product_id"] for candidate in state.candidates]
    ids += [line["product_id"] for line in state.cart]
    return list(dict.fromkeys(ids))


def _tool_schema(name: str, properties: Schema) -> Schema:
    fields = {"motivo": {"type": "string", "maxLength": 120}, "herramienta": {"const": name}, **properties}
    return {"type": "object", "properties": fields, "required": list(fields), "additionalProperties": False}


def decision_schema(known_ids: list[str]) -> Schema:
    """Esquema JSON de una decisión. Los ``product_id`` posibles se limitan a los
    conocidos; sin productos conocidos, las herramientas que los necesitan no existen."""
    offered = [tool for tool in _ALL if len(known_ids) >= tool.min_products]
    # Primero las que no necesitan productos, después las que necesitan uno y dos.
    offered.sort(key=lambda tool: tool.min_products)
    return {"anyOf": [_tool_schema(tool.name, tool.params(known_ids)) for tool in offered]}


def validate_call(name: object, args: Args, state: AgentState) -> list[Issue]:
    """Comprueba que la llamada está bien formada y se refiere a productos reales."""
    tool = TOOLS.get(name) if isinstance(name, str) else None
    if tool is None or tool.validate is None:
        return [Issue(UNKNOWN_TOOL, f"La herramienta {name!r} no existe.")]
    return tool.validate(args, set(known_product_ids(state)))
