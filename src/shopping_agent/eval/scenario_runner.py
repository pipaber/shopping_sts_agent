"""Ejecuta un escenario de principio a fin y guarda todo lo que pasó.

Cada escenario parte de la tienda recién restaurada desde la semilla, con un hilo
y un usuario nuevos (memoria vacía). Los turnos pasan por el mismo camino que una
conversación normal (``VoicePipeline`` sobre ``ShoppingSession``): con audio, por
el ASR y el TTS; con texto, directos al agente. Tras cada paso se toma una
instantánea del estado del agente, de la tienda y de las ofertas de los productos
que han aparecido; sobre ellas se evalúan las comprobaciones y las violaciones.
"""

from __future__ import annotations

import traceback
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from shopping_agent.agent.report import store_snapshot
from shopping_agent.agent.search import CatalogSearch
from shopping_agent.agent.session import ShoppingSession
from shopping_agent.eval.scenario_checks import Snapshot, View, resolve, run_check
from shopping_agent.eval.scenario_format import NewConversation, Remember, Say, Scenario, SetOffer, Step
from shopping_agent.eval.scenario_violations import find_violations
from shopping_agent.store.db import connect, restore
from shopping_agent.voice.asr import SpeechRecognizer
from shopping_agent.voice.pipeline import VoicePipeline, summarize_timings
from shopping_agent.voice.tts import SpeechSynthesizer

AUDIO, TEXT = "audio", "texto"
CANDIDATE_FIELDS = ("product_id", "title", "brand", "price_cents", "stock")
_SET_OFFER = (
    "UPDATE inventory SET price_cents = COALESCE(?, price_cents), stock = COALESCE(?, stock) WHERE product_id = ?"
)


@dataclass(frozen=True)
class Bench:
    """Lo que comparten todos los escenarios de una corrida."""

    graph: Any  # el grafo del agente, ya compilado sobre ``db_path``
    search: CatalogSearch
    db_path: Path
    seed_path: Path
    asr: SpeechRecognizer | None = None
    tts: SpeechSynthesizer | None = None


@dataclass(frozen=True)
class AudioInputs:
    """Los audios de los turnos de un escenario, en orden, y de dónde salen."""

    source: str
    files: list[Path]


def agent_state(session: ShoppingSession) -> dict[str, Any]:
    """Lo que se guarda del estado del agente en cada instantánea."""
    values = session.state
    candidates = [{key: candidate[key] for key in CANDIDATE_FIELDS} for candidate in values.get("candidates") or []]
    return {
        "budget_cents": values.get("budget_cents"),
        "preferences": list(values.get("preferences") or []),
        "pending_clarification": values.get("pending_clarification"),
        "quote": values.get("quote"),
        "order": values.get("order"),
        "candidates": candidates,
        "awaiting_confirmation": session.awaiting_confirmation,
    }


def read_offers(db_path: Path, product_ids: set[str]) -> dict[str, dict[str, int]]:
    """Precio y existencias actuales de unos productos."""
    marks = ", ".join("?" for _ in product_ids)
    conn = connect(db_path)
    try:
        rows = conn.execute(
            f"SELECT product_id, price_cents, stock FROM inventory WHERE product_id IN ({marks})", sorted(product_ids)
        ).fetchall()
    finally:
        conn.close()
    return {product_id: {"price_cents": price, "stock": stock} for product_id, price, stock in rows}


def set_offer(db_path: Path, product_id: str, price_cents: int | None, stock: int | None) -> None:
    """Suceso externo: la tienda cambia el precio o las existencias de un producto."""
    conn = connect(db_path)
    try:
        conn.execute(_SET_OFFER, (price_cents, stock, product_id))
    finally:
        conn.close()


class ScenarioRun:
    """Una corrida de un escenario. ``audio`` decide si los turnos entran por voz."""

    def __init__(
        self,
        scenario: Scenario,
        bench: Bench,
        run_id: str,
        audio: AudioInputs | None = None,
        audio_out: Path | None = None,
    ) -> None:
        self.scenario, self.bench, self.audio = scenario, bench, audio
        self.user_id = f"{run_id}-{scenario.id}"
        self.names: dict[str, str] = {}
        self.tracked: set[str] = set()
        self.threads: list[str] = []
        self.steps: list[dict[str, Any]] = []
        self.problems: list[str] = []
        restore(bench.seed_path, bench.db_path)
        asr, tts = (bench.asr, bench.tts) if audio else (None, None)
        self.pipeline = VoicePipeline(self._new_session(), asr, tts, audio_out)
        self.last = self._snapshot()

    # --- Estado de la corrida ---------------------------------------------------------

    def _new_session(self) -> ShoppingSession:
        thread = f"{self.user_id}-c{len(self.threads) + 1}"
        self.threads.append(thread)
        return ShoppingSession(self.bench.graph, thread, self.user_id)

    def _snapshot(self) -> Snapshot:
        session = self.pipeline.session
        state = agent_state(session)
        store = store_snapshot(self.bench.db_path, self.bench.seed_path)
        self.tracked.update(candidate["product_id"] for candidate in state["candidates"])
        self.tracked.update(item["product_id"] for item in [*store["cart_items"], *store["order_items"]])
        offers = read_offers(self.bench.db_path, self.tracked)
        return {"cart_id": session.thread_id, "state": state, "store": store, "offers": offers}

    def _product_text(self, product_id: str) -> str:
        evidence = self.bench.search.evidence(product_id, 10**6, 10**6)
        return " ".join(str(value) for value in evidence.values() if value)

    def _view(self, turn: dict[str, Any] | None = None) -> View:
        return View(self.last, turn, self.names, self._product_text)

    def _resolve(self, ref: str) -> str | None:
        product_id = resolve(ref, self._view())
        if product_id is None:
            self.problems.append(f"no se pudo resolver la referencia {ref!r}")
        return product_id

    # --- Pasos ------------------------------------------------------------------------

    def _say(self, step: Say) -> None:
        number, before = len(self.pipeline.turns) + 1, self.last
        # Con audio el agente recibe lo que entienda el ASR; sin audio, el texto correcto.
        audio, text = (self.audio.files[number - 1], None) if self.audio else (None, step.text)
        turn = self.pipeline.run_turn(audio, text=text, expected_text=step.text, product_terms=step.terms)
        self.last = self._snapshot()
        record = {"kind": "turn", **asdict(turn), "before": before, "after": self.last}
        record["checks"] = [run_check(check.name, check.params, self._view(record)) for check in step.expect]
        self.steps.append(record)

    def _remember(self, step: Remember) -> None:
        for name, ref in step.names.items():
            product_id = self._resolve(ref)
            if product_id is not None:
                self.names[name] = product_id
                self.tracked.add(product_id)
            title = self.bench.search.title(product_id) if product_id else None
            self.steps.append({"kind": "remember", "name": name, "ref": ref, "product_id": product_id, "title": title})

    def _set_offer(self, step: SetOffer) -> None:
        product_id = self._resolve(step.product)
        if product_id is not None:
            set_offer(self.bench.db_path, product_id, step.price_cents, step.stock)
            self.last = self._snapshot()
        change = {"product": step.product, "product_id": product_id, "price_cents": step.price_cents, "stock": step.stock}
        self.steps.append({"kind": "event", "event": "set_offer", **change})

    def _new_conversation(self, step: NewConversation) -> None:
        self.pipeline.session = self._new_session()
        self.last = self._snapshot()
        self.steps.append({"kind": "new_conversation", "thread_id": self.threads[-1]})

    def _step(self, step: Step) -> None:
        if isinstance(step, Say):
            self._say(step)
        elif isinstance(step, Remember):
            self._remember(step)
        elif isinstance(step, SetOffer):
            self._set_offer(step)
        else:
            self._new_conversation(step)

    # --- Corrida ----------------------------------------------------------------------

    def run(self) -> dict[str, Any]:
        """Hace todos los pasos y devuelve la corrida con su veredicto."""
        try:
            for step in self.scenario.steps:
                self._step(step)
        except Exception as error:  # un fallo a mitad de escenario es un resultado, no detiene la evaluación
            self.problems.append(f"error durante el escenario: {error!r}")
            self.steps.append({"kind": "error", "traceback": traceback.format_exc()})
        return self._record()

    def _record(self) -> dict[str, Any]:
        scenario = self.scenario
        turns = [step for step in self.steps if step["kind"] == "turn"]
        view = self._view(turns[-1] if turns else None)
        final_checks = [run_check(check.name, check.params, view) for check in scenario.expect]
        checks = [check for turn in turns for check in turn["checks"]] + final_checks
        violations = find_violations(turns)
        return {
            **{key: getattr(scenario, key) for key in ("id", "title", "kind", "description", "voice")},
            "input": AUDIO if self.audio else TEXT,
            "audio_source": self.audio.source if self.audio else None,
            "user_id": self.user_id,
            "threads": self.threads,
            "names": self.names,
            "steps": self.steps,
            "final": {"snapshot": self.last, "checks": final_checks},
            "violations": violations,
            "problems": self.problems,
            "passed": all(check["ok"] for check in checks) and not violations and not self.problems,
            "timings": summarize_timings(self.pipeline.turns),
        }
