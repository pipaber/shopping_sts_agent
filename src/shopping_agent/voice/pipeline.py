"""Turno completo por voz: audio → ASR → agente → TTS → audio.

Uso::

    python -m shopping_agent.voice.pipeline --scenario demo_compra --mode ambos --restore

``--scenario NOMBRE`` reúne lo que hace falta para un escenario grabado:

- ``scenarios/NOMBRE.txt``: lo que dice el usuario, un turno por línea;
- ``audio/escenarios/NOMBRE/``: un audio por turno, en el mismo orden (``01.wav``,
  ``02.wav``…; se recorren por orden de nombre);
- ``scenarios/NOMBRE.terminos.json`` (opcional): nombres de producto esperados por turno;
- la corrida se guarda en ``results/voz_NOMBRE/``.

Cada parte se puede dar por separado con ``--script``, ``--audios``, ``--terms`` y
``--out``. Con ``--mode ambos`` la conversación se hace primero con los audios y
después se repite desde cero con el texto correcto, para separar los errores del
ASR de los del agente. Sin audios solo se hace la conversación con el texto.

La latencia de un turno va desde que termina la grabación (el audio ya está
disponible) hasta que la respuesta puede reproducirse, y se desglosa en ASR,
recuperación, LLM, herramientas y TTS. La carga de los modelos se mide aparte.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from shopping_agent.agent.session import LLM, RETRIEVAL, TOOLS, ShoppingSession
from shopping_agent.voice.asr import SAMPLE_RATE, SpeechRecognizer
from shopping_agent.voice.audio import write_wav
from shopping_agent.voice.speech_text import to_speech
from shopping_agent.voice.tts import SpeechSynthesizer

ASR, TTS = "asr", "tts"
STAGES = (ASR, RETRIEVAL, LLM, TOOLS, TTS)
AUDIO_SUFFIXES = (".wav", ".flac", ".ogg", ".mp3", ".m4a", ".aac", ".opus", ".webm")
SCENARIO_DIR = Path("scenarios")
SCENARIO_AUDIO_DIR = Path("audio/escenarios")  # grabaciones del usuario; carpeta sin versionar
RESULTS_DIR = Path("results")


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
    product_terms: list[str] = field(default_factory=list)


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

    def _keep_input(self, audio: str | Path | np.ndarray, sample_rate: int, number: int) -> str | None:
        if self.out_dir is None:
            return str(audio) if isinstance(audio, (str, Path)) else None
        if isinstance(audio, (str, Path)):
            target = self.out_dir / f"entrada_{number:02d}{Path(audio).suffix.lower()}"
            if Path(audio).resolve() != target.resolve():
                shutil.copyfile(audio, target)
        else:
            target = write_wav(self.out_dir / f"entrada_{number:02d}.wav", audio, sample_rate)
        return target.name

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
        timings = dict.fromkeys(STAGES, 0.0)

        transcript = input_seconds = None
        if audio is not None:
            if self.asr is None:
                raise ValueError("No hay ASR para transcribir el audio.")
            heard = self.asr.transcribe(audio, sample_rate)
            transcript, input_seconds, timings[ASR] = heard.text, heard.audio_seconds, heard.seconds
            agent_input = heard.text
        else:
            agent_input = text or ""

        result = self.session.send(agent_input)
        for stage in (RETRIEVAL, LLM, TOOLS):
            timings[stage] = result.stages.get(stage, 0.0)

        spoken = to_speech(result.response)
        synthesis = None
        if self.tts is not None and spoken:
            synthesis = self.tts.synthesize(spoken)
            timings[TTS] = synthesis.seconds
            timings["tts_primer_fragmento"] = synthesis.first_chunk_seconds
        timings["total"] = sum(timings[stage] for stage in STAGES)

        # A partir de aquí la respuesta ya puede sonar: guardar no cuenta como latencia.
        input_name = self._keep_input(audio, sample_rate, number) if audio is not None else None
        output_name = None
        if synthesis is not None and self.out_dir is not None:
            output_name = write_wav(self.out_dir / f"respuesta_{number:02d}.wav", synthesis.audio, synthesis.sample_rate).name

        turn = VoiceTurn(
            turn=number,
            input_audio=input_name,
            input_seconds=input_seconds,
            transcript=transcript,
            expected_text=expected_text,
            agent_input=agent_input,
            response=result.response,
            spoken_text=spoken,
            output_audio=output_name,
            output_seconds=synthesis.audio_seconds if synthesis is not None else None,
            awaiting_confirmation=result.awaiting_confirmation,
            operations=[
                {key: operation.get(key) for key in ("tool", "args", "reason", "ok", "summary", "issues")}
                for operation in result.operations
            ],
            timings={key: round(value, 3) for key, value in timings.items()},
            product_terms=list(product_terms),
        )
        self.turns.append(turn)
        return turn


# --- Resúmenes ------------------------------------------------------------------------


def summarize_timings(turns: Sequence[VoiceTurn]) -> dict[str, Any]:
    """Media y máximo por etapa, separando los turnos que pasan por el LLM de los que
    no (confirmar un pedido no lo necesita y es mucho más rápido)."""

    def stats(selected: Sequence[VoiceTurn]) -> dict[str, Any]:
        if not selected:
            return {"turns": 0}
        summary: dict[str, Any] = {"turns": len(selected)}
        for key in (*STAGES, "total"):
            values = [turn.timings.get(key, 0.0) for turn in selected]
            summary[key] = {"mean": round(float(np.mean(values)), 2), "max": round(float(np.max(values)), 2)}
        return summary

    with_llm = [turn for turn in turns if turn.timings.get(LLM, 0.0) > 0]
    without_llm = [turn for turn in turns if turn.timings.get(LLM, 0.0) == 0]
    return {"all": stats(turns), "with_llm": stats(with_llm), "without_llm": stats(without_llm)}


def _actions(turn: VoiceTurn) -> list[tuple[Any, ...]]:
    return [
        (operation["tool"], json.dumps(operation["args"], sort_keys=True, ensure_ascii=False), operation["ok"])
        for operation in turn.operations
    ]


def compare_runs(audio_turns: Sequence[VoiceTurn], text_turns: Sequence[VoiceTurn]) -> list[dict[str, Any]]:
    """Turno a turno: ¿hizo el agente lo mismo con el audio que con el texto correcto?"""
    return [
        {
            "turn": spoken.turn,
            "same_input": " ".join(spoken.agent_input.split()) == " ".join(written.agent_input.split()),
            "same_operations": _actions(spoken) == _actions(written),
            "same_response": spoken.response == written.response,
        }
        for spoken, written in zip(audio_turns, text_turns)
    ]


def to_markdown(record: dict[str, Any]) -> str:
    models, load, voice = record["models"], record["load"], record["voice"]
    lines = ["# Transcripción de una compra por voz", "", f"- Fecha: {record['date']}"]
    if record.get("note"):
        lines.append(f"- Nota: {record['note']}")
    lines += [
        f"- LLM: `{models['llm']}`; ASR: `{models['asr']}`; TTS: `{models['tts']}`; embeddings: `{models['embeddings']}`",
        f"- Voz: {voice.get('mode')} ({voice.get('reference') or voice.get('speaker')})",
        f"- Carga inicial: catálogo y recuperadores {load['search_seconds']} s, LLM {load['llm_seconds']} s, "
        f"ASR {load['asr_seconds']} s, TTS {load['tts_seconds']} s; total {load['total_seconds']} s",
        f"- VRAM del proceso: {load['vram_mib']['loaded']} MiB con todo cargado, "
        f"{load['vram_mib']['after_run']} MiB al terminar la conversación",
        f"- Memoria del agente: {record['memory_backend']}; hilo `{record['thread_id']}`",
        "",
        "## Latencia por turno (segundos)",
        "",
        "| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total | Audio de respuesta |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for turn in record["turns"]:
        t = turn["timings"]
        lines.append(
            f"| {turn['turn']} | {t[ASR]:.2f} | {t[RETRIEVAL]:.2f} | {t[LLM]:.2f} | {t[TOOLS]:.2f} | {t[TTS]:.2f} "
            f"| {t['total']:.2f} | {turn['output_seconds'] or 0:.1f} s |"
        )
    for key, label in (("with_llm", "Media de los turnos con LLM"), ("without_llm", "Media de los turnos sin LLM")):
        stats = record["timings"][key]
        if stats["turns"]:
            lines.append(
                f"| **{label} ({stats['turns']})** | "
                + " | ".join(f"{stats[stage]['mean']:.2f}" for stage in (*STAGES, "total"))
                + " | |"
            )
    lines.append("")
    for turn in record["turns"]:
        lines += [f"## Turno {turn['turn']} ({turn['timings']['total']:.1f} s)", ""]
        if turn["transcript"] is not None:
            lines += [f"**Usuario (transcripción del ASR):** {turn['transcript']}", ""]
            if turn["expected_text"] and turn["expected_text"] != turn["transcript"]:
                lines += [f"**Texto correcto:** {turn['expected_text']}", ""]
        else:
            lines += [f"**Usuario (texto):** {turn['agent_input']}", ""]
        for operation in turn["operations"]:
            args = ", ".join(f"{key}={json.dumps(value, ensure_ascii=False)}" for key, value in operation["args"].items())
            summary = " ".join(str(operation["summary"]).split())
            summary = summary[:300] + "…" if len(summary) > 300 else summary
            lines.append(f"- `{operation['tool']}({args})` → {'OK' if operation['ok'] else 'RECHAZADO'}: {summary}")
        if turn["operations"]:
            lines.append("")
        waiting = " *(esperando confirmación)*" if turn["awaiting_confirmation"] else ""
        lines += [f"**Agente:** {turn['response']}{waiting}", "", f"**Enviado al TTS:** {turn['spoken_text']}", ""]

    from shopping_agent.store.ops import format_eur

    store = record["store"]
    lines += ["## Estado final de la tienda", ""]
    for order in store["orders"]:
        lines.append(f"- Pedido {order['order_id']}: total {format_eur(order['total_cents'])}")
    for item in store["order_items"]:
        lines.append(
            f"  - pedido {item['order_id']}: {item['quantity']} × `{item['product_id']}` a {format_eur(item['unit_price_cents'])}"
        )
    for change in store.get("inventory_changes", []):
        lines.append(f"- Inventario `{change['product_id']}`: {change['initial_stock']} → {change['stock']}")
    lines.append(f"- Líneas de carrito pendientes: {len(store['cart_items'])}")

    if record.get("text_run"):
        comparison = record["text_run"]["comparison"]
        different = [row["turn"] for row in comparison if not row["same_operations"]]
        lines += [
            "",
            "## Misma conversación con las transcripciones correctas",
            "",
            f"- Turnos en los que el ASR cambió el texto: {[row['turn'] for row in comparison if not row['same_input']] or 'ninguno'}",
            f"- Turnos en los que el agente hizo operaciones distintas: {different or 'ninguno'}",
            f"- Estado final de la tienda igual que con audio: {'sí' if record['text_run']['same_store'] else 'no'}",
        ]
    return "\n".join(lines) + "\n"


# --- Línea de órdenes -----------------------------------------------------------------


def _read_lines(path: Path | None) -> list[str]:
    if path is None:
        return []
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _read_terms(path: Path | None, turns: int) -> list[list[str]]:
    """``{"1": ["auriculares bluetooth"], …}``: nombres de producto esperados por turno."""
    if path is None:
        return [[] for _ in range(turns)]
    terms = json.loads(path.read_text(encoding="utf-8"))
    return [list(terms.get(str(number), [])) for number in range(1, turns + 1)]


def scenario_paths(args: argparse.Namespace) -> None:
    """Rellena con la convención de ``--scenario`` lo que no se haya dado de forma explícita."""
    if not args.scenario:
        return
    audio_dir = SCENARIO_AUDIO_DIR / args.scenario
    terms = SCENARIO_DIR / f"{args.scenario}.terminos.json"
    args.script = args.script or SCENARIO_DIR / f"{args.scenario}.txt"
    args.audios = args.audios or (audio_dir if audio_dir.is_dir() else None)
    args.terms = args.terms or (terms if terms.is_file() else None)
    args.out = args.out or RESULTS_DIR / f"voz_{args.scenario}"


def main() -> None:
    from shopping_agent.agent.chat import store_snapshot
    from shopping_agent.agent.graph import build_graph
    from shopping_agent.agent.llm import LocalLLM
    from shopping_agent.agent.memory import open_memory
    from shopping_agent.agent.search import DEFAULT_DATA_DIR, CatalogSearch
    from shopping_agent.gpu import process_vram_mib
    from shopping_agent.retrieval.retrievers import DEFAULT_DENSE_MODEL
    from shopping_agent.store.db import restore
    from shopping_agent.voice.asr import WhisperASR
    from shopping_agent.voice.tts import LicenseNotAccepted, VoiceNotConfigured, XttsTTS

    parser = argparse.ArgumentParser(description="Conversación por voz con el agente de compras.")
    parser.add_argument("--scenario", default=None, help="nombre del escenario: fija --script, --audios, --terms y --out")
    parser.add_argument("--audios", type=Path, default=None, help="carpeta con un audio por turno, en orden de nombre")
    parser.add_argument("--script", type=Path, default=None, help="transcripciones correctas, una por línea")
    parser.add_argument("--terms", type=Path, default=None, help="JSON con los nombres de producto esperados por turno")
    parser.add_argument("--mode", choices=("audio", "texto", "ambos"), default=None)
    parser.add_argument("--out", type=Path, default=None, help="carpeta de la corrida")
    parser.add_argument("--reference", type=Path, default=None, help="grabación de referencia para la voz del agente")
    parser.add_argument("--speaker", default=None, help="hablante incluido en XTTS-v2 (solo para pruebas)")
    parser.add_argument("--no-tts", action="store_true", help="no sintetiza la respuesta")
    parser.add_argument("--note", default=None, help="aclaración que se guarda con los resultados")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--db", type=Path, default=None)
    parser.add_argument("--user", default="anonimo")
    parser.add_argument("--restore", action="store_true", help="devuelve la tienda a su estado inicial antes de empezar")
    parser.add_argument("--n-ctx", type=int, default=8192)
    args = parser.parse_args()
    scenario_paths(args)
    if args.out is None:
        parser.error("Falta --out (o --scenario)")

    expected = _read_lines(args.script)
    audios = sorted(path for path in args.audios.iterdir() if path.suffix.lower() in AUDIO_SUFFIXES) if args.audios else []
    mode = args.mode or ("audio" if audios else "texto")
    if mode in ("audio", "ambos") and not audios:
        parser.error("--mode audio/ambos necesita --audios")
    if mode in ("texto", "ambos") and not expected:
        parser.error("--mode texto/ambos necesita --script con las transcripciones correctas")
    if audios and expected and len(audios) != len(expected):
        parser.error(f"Hay {len(audios)} audios y {len(expected)} líneas en {args.script}")
    turns = len(audios) or len(expected)
    terms = _read_terms(args.terms, turns)

    db_path = args.db or args.data / "store.sqlite"
    seed_path = args.data / "store_seed.sqlite"
    if args.restore:
        restore(seed_path, db_path)

    # --- Carga inicial (se mide aparte de los turnos) ---
    vram: dict[str, int | None] = {}
    start = load_start = time.perf_counter()
    search = CatalogSearch.from_dir(args.data)
    search.rank("calentamiento")  # la primera consulta carga el modelo denso en la GPU
    search_seconds, vram["search"] = time.perf_counter() - start, process_vram_mib()
    llm = LocalLLM(n_ctx=args.n_ctx)
    vram["llm"] = process_vram_mib()
    asr = WhisperASR() if mode in ("audio", "ambos") else None
    vram["asr"] = process_vram_mib()
    try:
        tts = None if args.no_tts else XttsTTS(args.reference, args.speaker)
    except (LicenseNotAccepted, VoiceNotConfigured) as error:
        sys.exit(str(error))
    vram["loaded"] = process_vram_mib()
    load_seconds = time.perf_counter() - load_start
    print(f"[modelos cargados en {load_seconds:.1f} s; VRAM del proceso: {vram['loaded']} MiB]", file=sys.stderr)

    def converse(session: ShoppingSession, out_dir: Path, use_audio: bool, speak: bool = True) -> VoicePipeline:
        pipeline = VoicePipeline(session, asr, tts if speak else None, out_dir)
        for index in range(turns):
            text = expected[index] if expected else None
            if use_audio:
                turn = pipeline.run_turn(audios[index], expected_text=text, product_terms=terms[index])
                print(f"tú (audio)> {turn.transcript}")
            else:
                turn = pipeline.run_turn(text=text, expected_text=text, product_terms=terms[index])
                print(f"tú (texto)> {turn.agent_input}")
            parts = ", ".join(f"{stage} {turn.timings[stage]:.2f}" for stage in STAGES)
            print(f"agente> {turn.response}\n   [{turn.timings['total']:.1f} s: {parts}]")
        return pipeline

    with open_memory() as memory:
        graph = build_graph(llm, search, db_path, memory.checkpointer, memory.store)
        thread_id = f"voz-{uuid.uuid4().hex[:8]}"
        main_run = converse(ShoppingSession(graph, thread_id, args.user), args.out, use_audio=mode != "texto")
        final = main_run.session.state
        store = store_snapshot(db_path, seed_path)
        vram["after_run"] = process_vram_mib()

        text_run = None
        if mode == "ambos":
            restore(seed_path, db_path)  # la repetición parte de la misma tienda
            repeat = converse(ShoppingSession(graph, f"{thread_id}-texto", args.user), args.out / "texto", use_audio=False, speak=False)
            repeat_store = store_snapshot(db_path, seed_path)
            text_run = {
                "thread_id": f"{thread_id}-texto",
                "turns": [asdict(turn) for turn in repeat.turns],
                "timings": summarize_timings(repeat.turns),
                "store": repeat_store,
                "comparison": compare_runs(main_run.turns, repeat.turns),
                "same_store": repeat_store == store,
            }

        record = {
            "date": datetime.now().isoformat(timespec="seconds"),
            "note": args.note,
            "mode": mode,
            "models": {
                "llm": llm.model_path.name,
                "asr": asr.model_name if asr else None,
                "tts": "XTTS-v2" if tts else None,
                "embeddings": DEFAULT_DENSE_MODEL,
            },
            "voice": tts.voice if tts else {},
            "load": {
                "search_seconds": round(search_seconds, 1),
                "llm_seconds": round(llm.load_seconds, 1),
                "asr_seconds": round(asr.load_seconds, 1) if asr else None,
                "tts_seconds": round(tts.load_seconds, 1) if tts else None,
                "total_seconds": round(load_seconds, 1),
                "vram_mib": vram,
            },
            "memory_backend": memory.backend,
            "thread_id": thread_id,
            "turns": [asdict(turn) for turn in main_run.turns],
            "timings": summarize_timings(main_run.turns),
            "final_state": {key: final.get(key) for key in ("budget_cents", "preferences", "cart", "quote", "order")},
            "store": store,
            "text_run": text_run,
        }
    (args.out / "turnos.json").write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    (args.out / "transcripcion.md").write_text(to_markdown(record), encoding="utf-8")
    print(f"[corrida guardada en {args.out}]", file=sys.stderr)


if __name__ == "__main__":
    main()
