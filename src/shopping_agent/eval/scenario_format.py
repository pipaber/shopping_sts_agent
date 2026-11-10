"""Formato declarativo de los escenarios de evaluación.

Un escenario es un JSON con los turnos del usuario, los sucesos externos que
ocurren entre turnos y lo que se espera, comprobado por código::

    {
      "id": "v1_compra_confirmada", "title": "…", "kind": "compra_confirmada",
      "voice": true, "description": "…",
      "steps": [
        {"say": "Busco una cafetera italiana.", "terms": ["cafetera italiana"],
         "expect": [{"check": "cart", "empty": true}]},
        {"remember": {"elegida": "candidate:1"}},
        {"event": "set_offer", "product": "@elegida", "price_cents": 1450, "stock": 20},
        {"new_conversation": true}
      ],
      "expect": [{"check": "orders", "count": 1}]
    }

Los productos no se nombran por su identificador: ``candidate:N`` y ``cart:N`` son
el candidato o la línea de carrito N en ese momento de la conversación, y
``remember`` les pone un nombre (``@elegida``) para usarlo después. Así el
escenario no depende de qué producto devuelva la búsqueda, y lo que condiciona el
resultado (precio y existencias) se fija con ``set_offer`` por regla, no a mano.

``expect`` dentro de un turno se comprueba al terminar ese turno; el del
escenario, al final. Las comprobaciones están en ``scenario_checks``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from shopping_agent.eval.scenario_checks import CHECKS

DEFAULT_DIR = Path("scenarios/evaluacion")
SET_OFFER = "set_offer"

_SCENARIO_KEYS = {"id", "title", "kind", "voice", "description", "steps", "expect"}
_STEP_KEYS = {
    "say": {"say", "terms", "expect"},
    "remember": {"remember"},
    "event": {"event", "product", "price_cents", "stock"},
    "new_conversation": {"new_conversation"},
}


class ScenarioError(ValueError):
    """El archivo de un escenario no sigue el formato."""


@dataclass(frozen=True)
class Check:
    name: str
    params: dict[str, Any]


@dataclass(frozen=True)
class Say:
    """Un turno del usuario: lo que dice y, si hace falta, los nombres de producto
    que el ASR debería entender y lo que se comprueba al terminar el turno."""

    text: str
    terms: tuple[str, ...] = ()
    expect: tuple[Check, ...] = ()


@dataclass(frozen=True)
class Remember:
    names: dict[str, str]  # nombre → referencia a un producto


@dataclass(frozen=True)
class SetOffer:
    """Suceso externo: la tienda cambia el precio o las existencias de un producto."""

    product: str
    price_cents: int | None = None
    stock: int | None = None


@dataclass(frozen=True)
class NewConversation:
    """El mismo usuario abre otra conversación: hilo y carrito nuevos, misma memoria."""


Step = Say | Remember | SetOffer | NewConversation


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    kind: str
    voice: bool
    description: str
    steps: tuple[Step, ...]
    expect: tuple[Check, ...]

    @property
    def says(self) -> list[Say]:
        return [step for step in self.steps if isinstance(step, Say)]


def _only_keys(raw: dict[str, Any], allowed: set[str], where: str) -> None:
    unknown = sorted(set(raw) - allowed)
    if unknown:
        raise ScenarioError(f"{where}: claves desconocidas {unknown}")


def parse_check(raw: dict[str, Any], where: str) -> Check:
    name = raw.get("check")
    if not isinstance(name, str) or name not in CHECKS:
        raise ScenarioError(f"{where}: comprobación desconocida {name!r}")
    params = {key: value for key, value in raw.items() if key != "check"}
    _only_keys(params, set(CHECKS[name].params), f"{where}, comprobación {name}")
    return Check(name, params)


def _parse_checks(raw: list[dict[str, Any]], where: str) -> tuple[Check, ...]:
    return tuple(parse_check(item, where) for item in raw)


def parse_step(raw: dict[str, Any], where: str) -> Step:
    kind = next((key for key in _STEP_KEYS if key in raw), None)
    if kind is None:
        raise ScenarioError(f"{where}: paso sin tipo ({sorted(raw)})")
    _only_keys(raw, _STEP_KEYS[kind], where)
    if kind == "say":
        return Say(str(raw["say"]), tuple(raw.get("terms", ())), _parse_checks(raw.get("expect", []), where))
    if kind == "remember":
        return Remember(dict(raw["remember"]))
    if kind == "new_conversation":
        return NewConversation()
    if raw["event"] != SET_OFFER or ("price_cents" not in raw and "stock" not in raw):
        raise ScenarioError(f"{where}: suceso no válido {raw}")
    return SetOffer(raw["product"], raw.get("price_cents"), raw.get("stock"))


def parse_scenario(raw: dict[str, Any]) -> Scenario:
    where = f"escenario {raw.get('id', '?')}"
    _only_keys(raw, _SCENARIO_KEYS, where)
    missing = sorted(_SCENARIO_KEYS - {"voice", "expect"} - set(raw))
    if missing:
        raise ScenarioError(f"{where}: faltan {missing}")
    steps = tuple(parse_step(step, f"{where}, paso {number}") for number, step in enumerate(raw["steps"], 1))
    if not any(isinstance(step, Say) for step in steps):
        raise ScenarioError(f"{where}: no tiene ningún turno")
    return Scenario(
        id=raw["id"],
        title=raw["title"],
        kind=raw["kind"],
        voice=bool(raw.get("voice", False)),
        description=raw["description"],
        steps=steps,
        expect=_parse_checks(raw.get("expect", []), where),
    )


def load_scenarios(folder: Path = DEFAULT_DIR) -> list[Scenario]:
    """Los escenarios de una carpeta, por orden de nombre de archivo."""
    scenarios = [parse_scenario(json.loads(path.read_text(encoding="utf-8"))) for path in sorted(folder.glob("*.json"))]
    ids = [scenario.id for scenario in scenarios]
    if len(set(ids)) != len(ids):
        raise ScenarioError(f"Hay identificadores repetidos en {folder}")
    return scenarios


def recording_script(scenarios: list[Scenario], audio_dir: str = "audio/escenarios") -> str:
    """Guion de grabación de los escenarios de voz: un archivo por turno y su texto exacto."""
    lines = [
        "# Guion de grabación de los escenarios de voz",
        "",
        "Generado con `python -m shopping_agent.eval.scenarios --recording-script` a partir de los JSON de",
        "esta carpeta; no se edita a mano. Un archivo por turno, con el texto dicho tal cual: es la",
        "transcripción correcta con la que se compara el ASR. Formato y consejos de grabación, en el README.",
    ]
    for scenario in (scenario for scenario in scenarios if scenario.voice):
        lines += ["", f"## {scenario.id} — {scenario.title}", "", "| Archivo | Texto que hay que decir |", "|---|---|"]
        lines += [
            f"| `{audio_dir}/{scenario.id}/{number:02d}.wav` | {say.text} |"
            for number, say in enumerate(scenario.says, 1)
        ]
    return "\n".join(lines) + "\n"
