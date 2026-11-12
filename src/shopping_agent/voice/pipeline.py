"""Turno completo por voz: audio → ASR → agente → TTS → audio.

La latencia de un turno va desde que termina la grabación (el audio ya está
disponible) hasta que la respuesta puede reproducirse, y se desglosa en ASR,
recuperación, LLM, herramientas y TTS. La carga de los modelos se mide aparte.

El comando que usa esto está en ``voice/chat.py``.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from shopping_agent.agent.report import operation_records
from shopping_agent.agent.session import LLM, RETRIEVAL, TOOLS, ShoppingSession, TurnResult
from shopping_agent.voice.asr import SAMPLE_RATE, SpeechRecognizer, Transcription
from shopping_agent.voice.audio import write_wav
from shopping_agent.voice.speech_text import to_speech
from shopping_agent.voice.tts import SpeechSynthesizer, Synthesis

ASR, TTS, TOTAL = "asr", "tts", "total"
STAGES = (ASR, RETRIEVAL, LLM, TOOLS, TTS)
VOLATILE_KEYS = ("quote_id",)  # identificadores aleatorios: distintos en cada corrida
NOT_HEARD = "No te he oído bien. ¿Puedes repetirlo?"


@dataclass
class VoiceTurn:
    turn: int
    input_audio: str | None  # ruta dentro de la carpeta de la corrida; ``None`` si la entrada fue texto
    input_seconds: float | None
    transcript: str | None  # lo que entendió el ASR
    expected_text: str | None  # la transcripción correcta, si se conoce
    agent_input: str  # lo que recibió el agente
    response: str  # texto del agente, tal como queda en la transcripción
    spoken_text: str  # lo que se envió al TTS
    output_audio: str | None
    output_seconds: float | None
    awaiting_confirmation: bool
    operations: list[dict[str, Any]] = field(default_factory=list)
    timings: dict[str, float] = field(default_factory=dict)  # segundos por etapa y ``total``
    llm_steps: int = 0  # veces que se consultó al LLM
    tts_first_chunk_seconds: float | None = None  # cuándo podría empezar a sonar la respuesta
    tts_retries: int = 0
    product_terms: list[str] = field(default_factory=list)


def stage_timings(heard: Transcription | None, result: TurnResult, synthesis: Synthesis | None) -> dict[str, float]:
    """Segundos de cada etapa del turno y su suma."""
    timings = {
        ASR: heard.seconds if heard else 0.0,
        **{stage: result.stages.get(stage, 0.0) for stage in (RETRIEVAL, LLM, TOOLS)},
        TTS: synthesis.seconds if synthesis else 0.0,
    }
    timings[TOTAL] = sum(timings.values())
    return {stage: round(seconds, 3) for stage, seconds in timings.items()}


class VoicePipeline:
    """Encadena ASR, agente y TTS, y guarda lo que entra y sale de cada turno."""

    def __init__(
        self,
        session: ShoppingSession,
        asr: SpeechRecognizer | None,
        tts: SpeechSynthesizer | None,
        out_dir: Path | None = None,
    ) -> None:
        self.session = session
        self.asr = asr
        self.tts = tts
        self.out_dir = out_dir
        self.turns: list[VoiceTurn] = []
        if out_dir is not None:
            out_dir.mkdir(parents=True, exist_ok=True)

    def run_turn(
        self,
        audio: str | Path | np.ndarray | None = None,
        *,
        text: str | None = None,
        expected_text: str | None = None,
        product_terms: Sequence[str] = (),
        sample_rate: int = SAMPLE_RATE,
    ) -> VoiceTurn:
        """Un turno. Con ``audio`` pasa por el ASR; con ``text`` el agente recibe ese
        texto directamente (la transcripción correcta, para aislar los errores del ASR)."""
        if (audio is None) == (text is None):
            raise ValueError("Un turno necesita o bien audio o bien texto.")
        number = len(self.turns) + 1
        heard = self._listen(audio, sample_rate) if audio is not None else None
        result = self._ask(heard.text if heard else text or "", spoken=heard is not None)
        spoken = to_speech(result.response)
        synthesis = self.tts.synthesize(spoken) if self.tts is not None and spoken else None

        # A partir de aquí la respuesta ya puede sonar: guardar no cuenta como latencia.
        turn = VoiceTurn(
            turn=number,
            input_audio=self._keep_input(audio, sample_rate, number) if audio is not None else None,
            input_seconds=heard.audio_seconds if heard else None,
            transcript=heard.text if heard else None,
            expected_text=expected_text,
            agent_input=result.user,
            response=result.response,
            spoken_text=spoken,
            output_audio=self._keep_output(synthesis, number),
            output_seconds=synthesis.audio_seconds if synthesis else None,
            awaiting_confirmation=result.awaiting_confirmation,
            operations=operation_records(result.operations),
            timings=stage_timings(heard, result, synthesis),
            llm_steps=result.llm_steps,
            tts_first_chunk_seconds=round(synthesis.first_chunk_seconds, 3) if synthesis else None,
            tts_retries=synthesis.retries if synthesis else 0,
            product_terms=list(product_terms),
        )
        self.turns.append(turn)
        return turn

    def _listen(self, audio: str | Path | np.ndarray, sample_rate: int) -> Transcription:
        if self.asr is None:
            raise ValueError("No hay ASR para transcribir el audio.")
        return self.asr.transcribe(audio, sample_rate)

    def _ask(self, said: str, spoken: bool) -> TurnResult:
        """Lo que contesta el agente. Un audio sin voz no le llega como si fuera un
        mensaje: se pide repetir y, si esperaba la confirmación, la sigue esperando."""
        if spoken and not said.strip():
            return TurnResult("", NOT_HEARD, self.session.awaiting_confirmation, 0.0)
        return self.session.send(said)

    def _keep_input(self, audio: str | Path | np.ndarray, sample_rate: int, number: int) -> str | None:
        """Guarda el audio de entrada en la carpeta de la corrida y devuelve su nombre."""
        if self.out_dir is None:
            return str(audio) if isinstance(audio, (str, Path)) else None
        if not isinstance(audio, (str, Path)):
            return write_wav(self.out_dir / f"entrada_{number:02d}.wav", audio, sample_rate).name
        target = self.out_dir / f"entrada_{number:02d}{Path(audio).suffix.lower()}"
        if Path(audio).resolve() != target.resolve():
            shutil.copyfile(audio, target)
        return target.name

    def _keep_output(self, synthesis: Synthesis | None, number: int) -> str | None:
        if synthesis is None or self.out_dir is None:
            return None
        return write_wav(self.out_dir / f"respuesta_{number:02d}.wav", synthesis.audio, synthesis.sample_rate).name


# --- Resúmenes ------------------------------------------------------------------------


def _stats(turns: Sequence[VoiceTurn]) -> dict[str, Any]:
    summary: dict[str, Any] = {"turns": len(turns)}
    for stage in (*STAGES, TOTAL) if turns else ():
        values = [turn.timings.get(stage, 0.0) for turn in turns]
        summary[stage] = {"mean": round(float(np.mean(values)), 2), "max": round(float(np.max(values)), 2)}
    return summary


def summarize_timings(turns: Sequence[VoiceTurn]) -> dict[str, Any]:
    """Media y máximo por etapa, separando los turnos que pasan por el LLM de los que
    no (confirmar un pedido no lo necesita y es mucho más rápido)."""
    with_llm = [turn for turn in turns if turn.llm_steps > 0]
    without_llm = [turn for turn in turns if turn.llm_steps == 0]
    return {"all": _stats(turns), "with_llm": _stats(with_llm), "without_llm": _stats(without_llm)}


def _actions(turn: VoiceTurn) -> list[tuple[Any, ...]]:
    actions = []
    for operation in turn.operations:
        args = {key: value for key, value in operation["args"].items() if key not in VOLATILE_KEYS}
        actions.append((operation["tool"], json.dumps(args, sort_keys=True, ensure_ascii=False), operation["ok"]))
    return actions


def comparable_store(store: dict[str, Any]) -> dict[str, Any]:
    """Estado de la tienda sin los identificadores que cambian de una corrida a otra."""
    return {
        key: [{name: value for name, value in row.items() if name not in VOLATILE_KEYS} for row in rows]
        for key, rows in store.items()
    }


def compare_runs(audio_turns: Sequence[VoiceTurn], text_turns: Sequence[VoiceTurn]) -> list[dict[str, Any]]:
    """Turno a turno: ¿hizo el agente lo mismo con el audio que con el texto correcto?

    ``same_input`` es la igualdad literal; ``same_words`` ignora mayúsculas, tildes,
    puntuación y la forma de escribir las cifras, que el ASR decide por su cuenta.
    """
    from shopping_agent.eval.voice import normalize

    return [
        {
            "turn": spoken.turn,
            "same_input": " ".join(spoken.agent_input.split()) == " ".join(written.agent_input.split()),
            "same_words": normalize(spoken.agent_input) == normalize(written.agent_input),
            "same_operations": _actions(spoken) == _actions(written),
            "same_response": spoken.response == written.response,
        }
        for spoken, written in zip(audio_turns, text_turns)
    ]
