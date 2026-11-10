"""Comprobaciones por código sobre texto libre: si el usuario ha confirmado y si
la respuesta que redacta el LLM se sostiene con los datos que tuvo delante."""

from __future__ import annotations

import re
import unicodedata

from shopping_agent.store.ops import Issue

UNGROUNDED_NUMBER = "cifra_sin_sustento"
FALSE_ORDER_CLAIM = "pedido_no_registrado"
MUST_QUOTE = "cierre_sin_cotizar"
INTERNAL_CODES = frozenset({UNGROUNDED_NUMBER, FALSE_ORDER_CLAIM, MUST_QUOTE})  # no se le dicen al usuario

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


# --- Petición de cerrar la compra ----------------------------------------------------

# Formas de pedir que se cierre la compra. El verbo tiene que ir con el pedido
# ("cierra el pedido", "ciérralo", "tramitarlo"): "una bolsa que cierre bien" no lo
# es, y "quiero comprar un regalo" es el principio de una búsqueda.
_THE_ORDER = r"(?:el|la|mi|este|esta|ese|esa) (?:pedido|compra|carrito|orden)"
_CHECKOUT = re.compile(
    r"\b(?:cierr[ae]|cerrar|cerramos|finaliz[ae]|finalizar|tramit[ae]|tramitar|confirm[ae]|confirmar"
    rf"|haz|hazme|hacer|realiza|realizar) {_THE_ORDER}\b"
    r"|\b(?:cierra|finaliza|tramita)(?:lo|la|melo|mela)\b"
    r"|\b(?:cerrar|finalizar|tramitar|pagar|comprar)l[oa]s?\b"
    r"|\bpagar\b|\beso es todo\b"
)
_NOT_YET = frozenset("no todavia aun antes espera esperate nunca tampoco".split())


def wants_checkout(text: str) -> bool:
    """¿Pide el mensaje cerrar la compra? Sin negación y sin ser una pregunta: "ciérralo",
    "eso es todo, ya puedes tramitarlo", "quiero pagar". Es prudente a propósito; lo
    que no reconoce lo sigue decidiendo el LLM."""
    folded = fold(text)
    if "?" in folded or _NOT_YET & set(_WORD.findall(folded)):
        return False
    return _CHECKOUT.search(folded) is not None


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


def fold(text: str) -> str:
    """Minúsculas y sin tildes, para comparar texto libre."""
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
    if not has_order and _ORDER_CLAIM.search(fold(text)):
        issues.append(
            Issue(
                FALSE_ORDER_CLAIM,
                "No hay ningún pedido registrado, así que no puedes darlo por hecho. Para cerrar la compra "
                "usa cotizar; el pedido solo se registra cuando el usuario confirma la cotización.",
            )
        )
    return issues
