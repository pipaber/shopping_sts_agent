"""Herramientas que el LLM puede proponer y reglas que el código impone.

El LLM solo elige una herramienta y sus argumentos. Aquí se define el esquema de
esa decisión (que restringe la salida del modelo), la validación previa a tocar
la tienda y el reconocimiento de la confirmación del usuario. No existe una
herramienta para registrar el pedido: eso solo ocurre tras la confirmación.
"""

from __future__ import annotations

import math
import re
import unicodedata
from typing import Any

from shopping_agent.agent.state import AgentState
from shopping_agent.store import ops
from shopping_agent.store.ops import Issue

# Códigos de rechazo propios del agente (los de la tienda están en store.ops).
UNKNOWN_TOOL = "herramienta_desconocida"
INVALID_ARGS = "argumentos_invalidos"
UNIDENTIFIED_PRODUCT = "producto_no_identificado"
UNGROUNDED_NUMBER = "cifra_sin_sustento"
FALSE_ORDER_CLAIM = "pedido_no_registrado"
INTERNAL_CODES = frozenset({UNGROUNDED_NUMBER, FALSE_ORDER_CLAIM})  # no se le dicen al usuario

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

# Herramientas que pasan por validar → ejecutar.
STORE_TOOLS = (DETAIL, COMPARE, PRICE_STOCK, ADD, SET_QUANTITY, REMOVE, SET_BUDGET, SAVE_PREFERENCE)
PRODUCT_TOOLS = (DETAIL, PRICE_STOCK, ADD, SET_QUANTITY, REMOVE)

TOOL_DOCS = {
    SEARCH: "(consulta) Busca en el catálogo. `consulta` son palabras clave en español: tipo de "
    "producto y, si se conocen, marca, color o uso. Úsala cuando el usuario pida un producto nuevo.",
    DETAIL: "(product_id) Devuelve el texto completo del catálogo para un producto.",
    COMPARE: "(product_ids) Devuelve lado a lado los datos de 2 a 4 productos.",
    PRICE_STOCK: "(product_id) Precio y existencias actuales de un producto.",
    ADD: "(product_id, cantidad) Añade unidades de un producto al carrito.",
    SET_QUANTITY: "(product_id, cantidad) Deja un producto del carrito con esa cantidad exacta.",
    REMOVE: "(product_id) Quita un producto del carrito.",
    SET_BUDGET: "(importe_eur) Guarda el gasto máximo que dice el usuario, en euros.",
    SAVE_PREFERENCE: "(preferencia) Guarda un gusto duradero del usuario (marca, color, talla…).",
    QUOTE: "() Prepara la cotización del carrito y pide la confirmación al usuario. Úsala cuando "
    "el usuario quiera comprar, pagar o cerrar el pedido.",
    CLARIFY: "(pregunta) Hace una pregunta al usuario cuando falta un dato o hay ambigüedad.",
    RESPOND: "(texto) Respuesta final del turno, en español, para leer en voz alta.",
}


def known_product_ids(state: AgentState) -> list[str]:
    """Productos a los que el LLM puede referirse: candidatos y carrito, sin repetir."""
    ids = [candidate["product_id"] for candidate in state.get("candidates") or []]
    ids += [line["product_id"] for line in state.get("cart") or []]
    return list(dict.fromkeys(ids))


def decision_args(decision: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in decision.items() if key not in ("motivo", "herramienta")}


def _tool_schema(name: str, **properties: dict[str, Any]) -> dict[str, Any]:
    fields = {"motivo": {"type": "string", "maxLength": 120}, "herramienta": {"const": name}, **properties}
    return {"type": "object", "properties": fields, "required": list(fields), "additionalProperties": False}


def decision_schema(known_ids: list[str]) -> dict[str, Any]:
    """Esquema JSON de una decisión. Los ``product_id`` posibles se limitan a los
    conocidos; sin productos conocidos, las herramientas que los necesitan no existen."""
    text = {"type": "string", "minLength": 1}
    options = [
        _tool_schema(SEARCH, consulta=text),
        _tool_schema(SET_BUDGET, importe_eur={"type": "number"}),
        _tool_schema(SAVE_PREFERENCE, preferencia=text),
        _tool_schema(QUOTE),
        _tool_schema(CLARIFY, pregunta=text),
        _tool_schema(RESPOND, texto=text),
    ]
    if known_ids:
        product = {"enum": known_ids}
        quantity = {"type": "integer"}
        options += [
            _tool_schema(DETAIL, product_id=product),
            _tool_schema(PRICE_STOCK, product_id=product),
            _tool_schema(ADD, product_id=product, cantidad=quantity),
            _tool_schema(SET_QUANTITY, product_id=product, cantidad=quantity),
            _tool_schema(REMOVE, product_id=product),
        ]
    if len(known_ids) >= 2:
        options.append(
            _tool_schema(COMPARE, product_ids={"type": "array", "items": {"enum": known_ids}, "minItems": 2, "maxItems": 4})
        )
    return {"anyOf": options}


# --- Validación previa a la tienda ------------------------------------------------


def budget_to_cents(amount: object) -> int | None:
    """Euros (número) → céntimos. ``None`` si no es un importe positivo."""
    if isinstance(amount, bool) or not isinstance(amount, (int, float)) or not math.isfinite(amount):
        return None
    cents = round(amount * 100)
    return cents if cents > 0 else None


def validate_call(tool: object, args: dict[str, Any], state: AgentState) -> list[Issue]:
    """Comprueba que la llamada está bien formada y se refiere a productos reales.

    No consulta la tienda: existencias y presupuesto los decide ``store.ops`` dentro
    de la transacción. Devuelve la lista de rechazos (vacía si se puede ejecutar).
    """
    if tool not in STORE_TOOLS:
        return [Issue(UNKNOWN_TOOL, f"La herramienta {tool!r} no existe.")]
    known = set(known_product_ids(state))
    issues: list[Issue] = []

    def check_product(product_id: object) -> None:
        if not isinstance(product_id, str) or product_id not in known:
            issues.append(
                Issue(
                    UNIDENTIFIED_PRODUCT,
                    f"El producto {product_id!r} no está entre los candidatos ni en el carrito. "
                    "Hay que buscarlo primero o preguntar al usuario a cuál se refiere.",
                )
            )

    if tool in PRODUCT_TOOLS:
        check_product(args.get("product_id"))
    if tool in (ADD, SET_QUANTITY):
        invalid = ops.check_quantity(args.get("cantidad"))
        if invalid:
            issues.append(invalid)
    if tool == COMPARE:
        ids = args.get("product_ids")
        if not isinstance(ids, list) or not 2 <= len(set(map(str, ids))) <= 4:
            issues.append(Issue(INVALID_ARGS, "Para comparar hacen falta entre 2 y 4 productos distintos."))
        else:
            for product_id in ids:
                check_product(product_id)
    if tool == SET_BUDGET and budget_to_cents(args.get("importe_eur")) is None:
        issues.append(
            Issue(ops.INVALID_BUDGET, f"El presupuesto debe ser un importe mayor que cero (se recibió {args.get('importe_eur')!r}).")
        )
    if tool == SAVE_PREFERENCE:
        preference = args.get("preferencia")
        if not isinstance(preference, str) or not 0 < len(preference.strip()) <= 200:
            issues.append(Issue(INVALID_ARGS, "La preferencia debe ser un texto breve."))
    return issues


# --- Confirmación del usuario -------------------------------------------------------

_YES = frozenset(
    "si vale confirmo confirma confirmar confirmado confirmalo confirmamelo adelante ok okay okey claro "
    "correcto acuerdo acepto hazlo procede perfecto dale exacto compralo registralo afirmativo".split()
)
_NO = frozenset(
    "no cancela cancelar cancelalo cancelo anula anular anulalo espera detente para todavia aun "
    "tampoco nunca negativo".split()
)
_FILLER = frozenset(
    "de el la lo los las un una pedido compra por favor gracias esta bien todo es eso asi pues venga ya "
    "muy que estoy seguro segura te me quiero comprar registra registrar mi orden mejor ahora mismo y "
    "claro esto conforme".split()
)
_WORD = re.compile(r"[a-z0-9]+")


def classify_confirmation(text: str) -> str:
    """``"si"``, ``"no"`` u ``"otro"``.

    Solo cuenta como sí una respuesta que no dice nada más que confirmar; "sí, pero
    que sean tres" es ``"otro"`` y se trata como un turno nuevo. Comprar exige un sí
    inequívoco.
    """
    folded = unicodedata.normalize("NFKD", text.lower())
    words = _WORD.findall("".join(char for char in folded if not unicodedata.combining(char)))
    if not words or len(words) > 12:
        return "otro"
    has_yes = any(word in _YES for word in words)
    has_no = any(word in _NO for word in words)
    if any(word not in _YES and word not in _NO and word not in _FILLER for word in words):
        return "otro"
    if has_no:
        return "otro" if has_yes else "no"
    return "si" if has_yes else "otro"


# --- Validación de la respuesta del LLM ----------------------------------------------

# Números que no forman parte de un identificador (no van pegados a una letra).
_NUMBER = re.compile(r"(?<![A-Za-z0-9])\d+(?:[.,]\d+)?")
_ORDER_CLAIM = re.compile(
    r"pedido\s+(?:ya\s+)?(?:esta|ha\s+sido|queda|quedo|fue|se\s+ha)\s+"
    r"(?:listo|registrado|confirmado|realizado|hecho|completado|procesado|tramitado)"
    r"|pedido\s+(?:registrado|confirmado|realizado|completado|procesado)"
    r"|compra\s+(?:ha\s+sido\s+|esta\s+|queda\s+)?(?:realizada|confirmada|completada|registrada|hecha)"
    r"|gracias\s+por\s+(?:tu|su)\s+(?:compra|pedido)"
)


def _fold(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text.lower())
    return "".join(char for char in folded if not unicodedata.combining(char))


def numbers_in(text: str) -> set[str]:
    """Cifras de un texto en forma canónica: ``"45,70"`` y ``"45.7"`` son la misma."""
    return {f"{float(token.replace(',', '.')):g}" for token in _NUMBER.findall(text)}


def check_response(text: str, evidence: str, has_order: bool) -> list[Issue]:
    """Lo que el código puede comprobar de una respuesta redactada por el LLM.

    - Toda cifra (precio, existencias, horas, medidas…) debe aparecer en la evidencia
      que el LLM tuvo delante: estado, resultados de herramientas e historial reciente.
    - No puede dar por hecho un pedido si no hay ninguno registrado.
    """
    issues: list[Issue] = []
    missing = sorted(numbers_in(text) - numbers_in(evidence), key=float)
    if missing:
        issues.append(
            Issue(
                UNGROUNDED_NUMBER,
                f"En tu respuesta hay cifras que no aparecen en los datos ({', '.join(missing)}). Usa solo "
                "cifras de CANDIDATOS, CARRITO o de un RESULTADO, sin hacer cuentas; si te falta un dato de "
                "un producto, consúltalo con detalle_producto o di que no consta.",
                details={"numbers": missing},
            )
        )
    if not has_order and _ORDER_CLAIM.search(_fold(text)):
        issues.append(
            Issue(
                FALSE_ORDER_CLAIM,
                "No hay ningún pedido registrado, así que no puedes darlo por hecho. Para cerrar la compra "
                "usa cotizar; el pedido solo se registra cuando el usuario confirma la cotización.",
            )
        )
    return issues
