"""Referencias del usuario a un candidato por su posición en la lista: "el segundo",
"de la primera", "el último".

El LLM es quien traduce "la primera" a un identificador, y a veces elige otro
producto o elige uno cuando la posición nombrada no existe ("el séptimo" de cinco).
Eso sí lo puede comprobar el código: qué posiciones nombra el mensaje, si existen
y si el producto que el LLM quiere añadir es uno de los señalados.

Solo cuentan los ordinales con artículo ("el primero", "del tercero"); "primero
busca…" no es una referencia. No se reconocen otras formas ("el número dos", "la
opción 3"): con ellas decide el LLM, como antes.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from shopping_agent.agent.guards import fold
from shopping_agent.agent.state import Candidate
from shopping_agent.store.ops import Issue

NO_SUCH_POSITION = "posicion_inexistente"
OTHER_PRODUCT = "producto_no_senalado"
CODES = frozenset({NO_SUCH_POSITION, OTHER_PRODUCT})  # son para el LLM, no para el usuario

_NAMES = ("primero", "segundo", "tercero", "cuarto", "quinto", "sexto", "séptimo", "octavo", "noveno", "décimo")
_LAST = 0  # "el último": la posición depende de cuántos candidatos haya
_ORDINALS = {fold(name): position for position, name in enumerate(_NAMES, 1)}
_ORDINALS.update({fold(name)[:-1] + "a": position for position, name in enumerate(_NAMES, 1)})
_ORDINALS.update({"primer": 1, "tercer": 3, "ultimo": _LAST, "ultima": _LAST})
_REFERENCE = re.compile(r"\b(?:el|la|del|al)\s+(" + "|".join(_ORDINALS) + r")\b")


def positions(text: str, listed: int) -> list[int]:
    """Posiciones (desde 1) que nombra el mensaje, sin repetir. ``listed`` es cuántos
    candidatos hay, para saber cuál es "el último"."""
    found = [_ORDINALS[word] or listed for word in _REFERENCE.findall(fold(text))]
    return list(dict.fromkeys(found))


def _name(position: int) -> str:
    return _NAMES[position - 1] if position <= len(_NAMES) else f"número {position}"


def mentions_brand(text: str, candidate: Candidate) -> bool:
    """¿Nombra el mensaje la marca del producto? Es la otra forma de señalarlo."""
    brand = fold(candidate["brand"] or "").strip()
    return bool(brand) and re.search(rf"\b{re.escape(brand)}\b", fold(text)) is not None


def reference_hint(text: str, candidates: Sequence[Candidate]) -> str:
    """Aviso determinista para el LLM: a qué candidato corresponde cada posición que
    nombra el mensaje, o que esa posición no existe."""
    named = positions(text, len(candidates)) if candidates else []
    missing = [position for position in named if position > len(candidates)]
    if missing:
        return (
            f"AVISO DEL SISTEMA: el mensaje nombra el {_name(missing[0])} de la lista y CANDIDATOS solo tiene "
            f"{len(candidates)}. Ese producto no existe: no elijas otro en su lugar; díselo y pregunta cuál quiere."
        )
    if not named:
        return ""
    pairs = "; ".join(f"el {_name(position)} es [{position}] id={candidates[position - 1]['product_id']}" for position in named)
    return f"AVISO DEL SISTEMA: si el mensaje se refiere a la lista de CANDIDATOS, {pairs}."


def _other_product(text: str, candidates: Sequence[Candidate], named: list[int], product_ids: Sequence[str]) -> Issue | None:
    """Rechazo si se quiere añadir un candidato que el mensaje no señala ni por posición ni por marca."""
    pointed = {candidates[position - 1]["product_id"] for position in named}
    listed = {candidate["product_id"]: candidate for candidate in candidates}
    wrong = [pid for pid in product_ids if pid in listed and pid not in pointed and not mentions_brand(text, listed[pid])]
    if not wrong:
        return None
    wanted = ", ".join(f"[{position}] id={candidates[position - 1]['product_id']}" for position in named)
    return Issue(
        OTHER_PRODUCT,
        f"El usuario señala {wanted} y tú quieres añadir {', '.join(wrong)}, que no ha pedido. Añade solo lo que "
        "pide. Si ese producto no se puede añadir, usa responder para explicarlo y proponer otro, sin añadirlo tú.",
    )


def check_products(text: str, candidates: Sequence[Candidate], product_ids: Sequence[str], adding: bool) -> list[Issue]:
    """Comprueba una llamada sobre ``product_ids`` contra las posiciones que nombra el mensaje."""
    named = positions(text, len(candidates)) if candidates else []
    missing = [position for position in named if position > len(candidates)]
    if missing:
        message = (
            f"El usuario se refiere al {_name(missing[0])} de la lista y CANDIDATOS solo tiene {len(candidates)}. "
            "No elijas otro producto por él: usa pedir_aclaracion para decirle cuántos hay y preguntarle cuál quiere."
        )
        return [Issue(NO_SUCH_POSITION, message)]
    wrong = _other_product(text, candidates, named, product_ids) if adding and named else None
    return [wrong] if wrong else []
