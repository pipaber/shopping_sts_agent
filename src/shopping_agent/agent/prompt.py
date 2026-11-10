"""Lo que ve el LLM: las reglas, el estado de la compra y el resultado de cada paso.

Un campo del catálogo ausente se muestra siempre como "desconocido". Lo que se le
dice al usuario cuando el texto lo escribe el código está en ``texts.py``.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping, Sequence

from shopping_agent.agent import references
from shopping_agent.agent.state import AgentState, Candidate, CartLine, Step, cart_total
from shopping_agent.agent.texts import short_title, units
from shopping_agent.store.ops import Issue, format_eur

UNKNOWN = "desconocido"
HISTORY_MESSAGES = 8
HISTORY_CHARS = 600

_RULES_BEFORE_TOOLS = """Eres el asistente de compras por voz de una tienda en línea. Hablas en español de España, con frases cortas y naturales, porque tu respuesta se leerá en voz alta: sin listas, sin emojis y sin símbolos raros.

Trabajas por pasos. En cada paso eliges UNA herramienta y contestas solo con un objeto JSON con los campos "motivo" (una frase corta), "herramienta" y sus argumentos. El sistema la ejecuta y te devuelve un RESULTADO; entonces eliges el paso siguiente. El turno termina cuando usas `responder` o `pedir_aclaracion`. Lo normal son uno o dos pasos y después `responder`.

Herramientas:
"""

_RULES_AFTER_TOOLS = """

Reglas:
1. Sobre un producto solo puedes afirmar lo que aparece en CANDIDATOS o en un RESULTADO. Si un dato figura como "desconocido", di que no consta en el catálogo; nunca lo inventes. CANDIDATOS solo trae un extracto de las características: si te preguntan por un dato que no ves ahí, mira `detalle_producto` antes de decir que no consta.
2. Precios, totales y existencias son los que dan las herramientas. No hagas cuentas por tu cuenta.
3. Tú no registras pedidos. El sistema lo hace cuando el usuario confirma la cotización. No digas que un pedido está hecho si no aparece en PEDIDO REGISTRADO.
4. Si el usuario dice cuánto quiere gastar, lo primero es `fijar_presupuesto`. El importe nunca va dentro de la consulta de búsqueda.
5. "El primero", "el segundo"… se refieren al orden de CANDIDATOS: no pidas aclaración por eso. Usa siempre el `id` exacto del producto. Si el usuario nombra una posición que no existe (el séptimo de una lista de cinco), no elijas otro producto: usa `pedir_aclaracion` para decirle cuántos hay. Si el usuario quiere algo que no está en CANDIDATOS ni en CARRITO, búscalo primero.
6. `agregar_al_carrito` suma unidades. Si el producto ya está en el carrito y el usuario corrige la cantidad ("mejor que sean tres", "solo uno"), usa `cambiar_cantidad` con la cantidad final.
7. Una pregunta ("¿está disponible?", "¿cuánto cuesta?", "¿de qué color es?") solo se contesta. El carrito solo cambia cuando el usuario lo pide con una orden: añade, ponme, quiero, quita, cambia.
8. Si falta la cantidad, no está claro a qué producto se refiere o la petición admite varias lecturas, usa `pedir_aclaracion` en lugar de suponer. "Uno", "ese" o "el primero" significan una unidad.
9. Si un RESULTADO dice RECHAZADO, no repitas la misma llamada: usa `responder` para explicar el motivo con sus datos y proponer una salida (menos unidades, otro producto, otro presupuesto).
10. En cuanto tengas lo necesario para contestar, usa `responder`. No repitas una herramienta cuyo resultado ya tienes. Si la pregunta se contesta con lo que ya hay en CANDIDATOS o CARRITO, usa `responder` directamente.
11. Al presentar productos menciona como mucho tres, en una frase seguida, cada uno por su marca o un nombre corto y con su precio. Al comparar, cita los datos de cada producto tal como aparecen; no saques conclusiones que el texto no diga. Tras cambiar el carrito o el presupuesto contesta con una sola frase breve: el sistema añade después el contenido exacto del carrito.

Ejemplos (cada línea es un paso):
Usuario: "Quiero una mochila y no quiero gastar más de 40 euros"
{"motivo": "el usuario da su gasto máximo", "herramienta": "fijar_presupuesto", "importe_eur": 40}
{"motivo": "buscar lo que pide", "herramienta": "buscar_productos", "consulta": "mochila"}
{"motivo": "presentar los candidatos", "herramienta": "responder", "texto": "Tengo la de Marca A por 25 euros, la de Marca B por 31 y la de Marca C por 38. ¿Te interesa alguna?"}
Usuario: "Ponme dos del segundo" (el candidato [2] tiene id=B00EJEMPLO)
{"motivo": "añadir dos unidades del candidato 2", "herramienta": "agregar_al_carrito", "product_id": "B00EJEMPLO", "cantidad": 2}
{"motivo": "confirmar el cambio", "herramienta": "responder", "texto": "Hecho, añadidas dos unidades."}
Usuario: "Mejor que sean tres" (B00EJEMPLO ya está en el carrito)
{"motivo": "corrige la cantidad", "herramienta": "cambiar_cantidad", "product_id": "B00EJEMPLO", "cantidad": 3}
Usuario: "¿Cuánta batería tiene el segundo?" (el candidato [2] tiene id=B00OTRO y CANDIDATOS no trae ese dato)
{"motivo": "leer el texto completo del candidato 2", "herramienta": "detalle_producto", "product_id": "B00OTRO"}
{"motivo": "contestar con el dato del catálogo", "herramienta": "responder", "texto": "Según el catálogo, …"}
Usuario: "¿Y el tercero está disponible?" (el candidato [3] tiene id=B00TERCERO)
{"motivo": "es una pregunta: consultar existencias sin tocar el carrito", "herramienta": "consultar_precio_stock", "product_id": "B00TERCERO"}
{"motivo": "contestar la pregunta", "herramienta": "responder", "texto": "Sí, quedan … unidades."}
Usuario: "¿De qué color es el primero?" (en CANDIDATOS pone color: desconocido)
{"motivo": "el dato no consta", "herramienta": "responder", "texto": "El catálogo no indica el color de ese producto."}"""


def system_prompt(tool_docs: Mapping[str, str]) -> str:
    """Instrucciones del LLM, con la lista de herramientas (nombre → descripción)."""
    listed = "\n".join(f"- {name} {doc}" for name, doc in tool_docs.items())
    return _RULES_BEFORE_TOOLS + listed + _RULES_AFTER_TOOLS


def _field(value: object) -> str:
    return str(value) if value not in (None, "") else UNKNOWN


def candidate_line(index: int, candidate: Candidate) -> str:
    stock = candidate["stock"]
    return (
        f"[{index}] id={candidate['product_id']} | {candidate['title']} | marca: {_field(candidate['brand'])}"
        f" | color: {_field(candidate['color'])} | precio: {format_eur(candidate['price_cents'])}"
        f" | existencias: {stock if stock > 0 else 'agotado'}"
        f" | características (extracto): {_field(candidate['bullets'])}"
        f" | descripción: {_field(candidate['description'])}"
    )


def candidates_found(shown: Sequence[Candidate]) -> str:
    """Resultado de una búsqueda, tal como vuelve al LLM."""
    if not shown:
        return "la búsqueda no devolvió ningún producto."
    rows = "\n".join(candidate_line(index, candidate) for index, candidate in enumerate(shown, 1))
    return f"estos son ahora los CANDIDATOS, del más al menos relevante:\n{rows}"


def rejection(issues: Iterable[Issue]) -> str:
    """Motivos de un rechazo, con su código, para que el LLM los explique o corrija."""
    parts = []
    for issue in issues:
        extra = ""
        if "max_quantity" in issue.details:
            extra = (
                f" Dentro del presupuesto caben como máximo {issue.details['max_quantity']} "
                "unidades de este producto."
            )
        parts.append(f"[{issue.code}] {issue.message}{extra}")
    return " ".join(parts)


def render_cart(cart: Sequence[CartLine]) -> str:
    if not cart:
        return "CARRITO: vacío"
    rows = [
        f"- id={line['product_id']} | {short_title(line['title'])} | {units(line['quantity'])} × "
        f"{format_eur(line['unit_price_cents'])} = {format_eur(line['subtotal_cents'])} | existencias: {line['stock']}"
        for line in cart
    ]
    return "CARRITO:\n" + "\n".join(rows) + f"\nTotal del carrito: {format_eur(cart_total(cart))}"


_AMOUNT = re.compile(r"\d+(?:[.,]\d+)?\s*(?:euros?|eur|€)", re.IGNORECASE)


def amount_hint(text: str) -> str:
    """Aviso determinista si el mensaje menciona un importe. Decide el LLM qué hacer con él."""
    found = _AMOUNT.search(text)
    if not found:
        return ""
    return (
        f'AVISO DEL SISTEMA: el mensaje menciona un importe ("{found.group(0)}"). Si es lo máximo que '
        "el usuario quiere gastar, el primer paso es fijar_presupuesto."
    )


def turn_context(state: AgentState, text: str) -> str:
    """Lo que el LLM ve del estado durante todo el turno, con los avisos que procedan:
    que el mensaje trae un importe y a qué candidato corresponde cada posición que nombra."""
    hints = (amount_hint(text), references.reference_hint(text, state.candidates))
    return "\n".join([render_state(state), *filter(None, hints)])


def render_state(state: AgentState) -> str:
    budget = state.budget_cents
    cart = state.cart
    candidates = state.candidates
    parts = [f"PRESUPUESTO: {format_eur(budget) if budget is not None else 'sin fijar'}"]
    parts.append("PREFERENCIAS: " + ("; ".join(state.preferences) or "ninguna"))
    parts.append(render_cart(cart))
    if candidates:
        query = state.last_query
        header = f'CANDIDATOS (última búsqueda: "{query}"):' if query else "CANDIDATOS:"
        parts.append(header + "\n" + "\n".join(candidate_line(i, c) for i, c in enumerate(candidates, 1)))
    else:
        parts.append("CANDIDATOS: ninguno (todavía no se ha buscado)")
    quote = state.quote
    if quote:
        parts.append(f"COTIZACIÓN PENDIENTE DE CONFIRMAR: total {format_eur(quote['total_cents'])}")
    order = state.order
    if order:
        parts.append(f"PEDIDO REGISTRADO: número {order['order_id']}, total {format_eur(order['total_cents'])}")
    pending = state.pending_clarification
    if pending:
        parts.append(f'ACLARACIÓN PENDIENTE: preguntaste "{pending}"; el mensaje del usuario es su respuesta.')
    return "\n".join(parts)


def decision_json(step: Step) -> str:
    """La decisión del LLM tal como la emitió, para devolvérsela como turno suyo."""
    decision = {"motivo": step["reason"], "herramienta": step["tool"], **step["args"]}
    return json.dumps(decision, ensure_ascii=False)


def result_message(step: Step) -> str:
    status = "OK" if step["ok"] else "RECHAZADO"
    return (
        f"RESULTADO de {step['tool']} ({status}): {step['summary']}\n\n"
        "Elige el siguiente paso. Si ya puedes contestar al usuario, usa responder."
    )


def build_messages(state: AgentState, instructions: str) -> list[dict[str, str]]:
    """Mensajes para el LLM: reglas, historial reciente, estado al empezar el turno y,
    después, cada paso como un intercambio (su decisión y el resultado del sistema).

    Dentro de un turno la lista solo crece por el final, así que llama.cpp reutiliza
    todo el prefijo ya evaluado y cada paso cuesta solo los tokens nuevos.
    """
    history = list(state.messages)
    current = history.pop()["content"] if history and history[-1]["role"] == "user" else state.user_input
    messages = [{"role": "system", "content": instructions}]
    for message in history[-HISTORY_MESSAGES:]:
        content = message["content"]
        if len(content) > HISTORY_CHARS:
            content = content[:HISTORY_CHARS] + "…"
        messages.append({"role": message["role"], "content": content})
    context = state.turn_context or render_state(state)
    messages.append(
        {"role": "user", "content": f"{context}\n\nMENSAJE DEL USUARIO: {current}\n\nElige el primer paso."}
    )
    for step in state.steps:
        messages.append({"role": "assistant", "content": decision_json(step)})
        messages.append({"role": "user", "content": result_message(step)})
    return messages
