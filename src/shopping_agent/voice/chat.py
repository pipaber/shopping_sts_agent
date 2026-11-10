"""Conversación por voz con el agente de compras.

Uso::

    python -m shopping_agent.voice.chat --scenario demo_compra --mode both --restore

``--scenario NOMBRE`` reúne lo que hace falta para un escenario grabado:

- ``scenarios/NOMBRE.txt``: lo que dice el usuario, un turno por línea;
- ``audio/escenarios/NOMBRE/``: un audio por turno, en el mismo orden (``01.wav``,
  ``02.wav``…; se recorren por orden de nombre);
- ``scenarios/NOMBRE.terminos.json`` (opcional): nombres de producto esperados por turno;
- la corrida se guarda en ``results/voz_NOMBRE/``.

Cada parte se puede dar por separado con ``--script``, ``--audios``, ``--terms`` y
``--out``. Con ``--mode both`` la conversación se hace primero con los audios y
después se repite desde cero con el texto correcto, para separar los errores del
ASR de los del agente. Sin audios solo se hace la conversación con el texto.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from shopping_agent.agent.chat import FINAL_STATE_FIELDS, Models, check_memory, load_models
from shopping_agent.agent.graph import build_graph
from shopping_agent.agent.memory import open_memory
from shopping_agent.agent.report import store_snapshot
from shopping_agent.agent.search import DEFAULT_DATA_DIR
from shopping_agent.agent.session import ShoppingSession
from shopping_agent.gpu import process_vram_mib
from shopping_agent.retrieval.retrievers import DEFAULT_DENSE_MODEL
from shopping_agent.store.db import restore
from shopping_agent.voice.asr import WhisperASR
from shopping_agent.voice.pipeline import STAGES, TOTAL, VoicePipeline, comparable_store, compare_runs, summarize_timings
from shopping_agent.voice.report import STAGE_LABELS, to_markdown
from shopping_agent.voice.tts import LicenseNotAccepted, VoiceNotConfigured, XttsTTS

AUDIO, TEXT, BOTH = "audio", "text", "both"
AUDIO_SUFFIXES = (".wav", ".flac", ".ogg", ".mp3", ".m4a", ".aac", ".opus", ".webm")
SCENARIO_DIR = Path("scenarios")
SCENARIO_AUDIO_DIR = Path("audio/escenarios")  # grabaciones del usuario; carpeta sin versionar
RESULTS_DIR = Path("results")
RECORD_FILE, TRANSCRIPT_FILE = "turnos.json", "transcripcion.md"


@dataclass
class Inputs:
    """Lo que dice el usuario en cada turno: el audio, el texto correcto o ambos."""

    mode: str
    audios: list[Path]
    expected: list[str]  # transcripciones correctas, una por turno
    terms: list[list[str]]  # nombres de producto esperados en cada turno

    @property
    def turns(self) -> int:
        return len(self.audios) or len(self.expected)


@dataclass
class Loaded:
    """Los modelos cargados y lo que costó cargarlos."""

    models: Models
    asr: WhisperASR | None
    tts: XttsTTS | None
    seconds: float
    vram_mib: dict[str, int | None]


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


def read_inputs(args: argparse.Namespace) -> Inputs:
    """Lee guion, audios y términos, y comprueba que sirven para el modo pedido."""
    expected = []
    if args.script:
        expected = [line.strip() for line in args.script.read_text(encoding="utf-8").splitlines() if line.strip()]
    audios = []
    if args.audios:
        audios = sorted(path for path in args.audios.iterdir() if path.suffix.lower() in AUDIO_SUFFIXES)
    mode = args.mode or (AUDIO if audios else TEXT)
    if mode in (AUDIO, BOTH) and not audios:
        sys.exit(f"--mode {mode} necesita --audios")
    if mode in (TEXT, BOTH) and not expected:
        sys.exit(f"--mode {mode} necesita --script con las transcripciones correctas")
    if audios and expected and len(audios) != len(expected):
        sys.exit(f"Hay {len(audios)} audios y {len(expected)} líneas en {args.script}")
    # ``{"1": ["auriculares bluetooth"], …}``: nombres de producto esperados por turno.
    by_turn = json.loads(args.terms.read_text(encoding="utf-8")) if args.terms else {}
    turns = len(audios) or len(expected)
    return Inputs(mode, audios, expected, [list(by_turn.get(str(turn), [])) for turn in range(1, turns + 1)])


def load_everything(args: argparse.Namespace, mode: str) -> Loaded:
    """Carga inicial, que se mide aparte de los turnos."""
    start = time.perf_counter()
    models = load_models(args.data, args.n_ctx)
    vram = {"search": models.vram_search_mib, "llm": models.vram_total_mib}
    asr = WhisperASR() if mode in (AUDIO, BOTH) else None
    vram["asr"] = process_vram_mib()
    try:
        tts = None if args.no_tts else XttsTTS(args.reference, args.speaker)
    except (LicenseNotAccepted, VoiceNotConfigured) as error:
        sys.exit(str(error))
    vram["loaded"] = process_vram_mib()
    return Loaded(models, asr, tts, time.perf_counter() - start, vram)


def converse(pipeline: VoicePipeline, inputs: Inputs, use_audio: bool) -> VoicePipeline:
    """Hace todos los turnos, con los audios o con el texto correcto, y los va mostrando."""
    for index in range(inputs.turns):
        text = inputs.expected[index] if inputs.expected else None
        if use_audio:
            turn = pipeline.run_turn(inputs.audios[index], expected_text=text, product_terms=inputs.terms[index])
            print(f"tú (audio)> {turn.transcript}")
        else:
            turn = pipeline.run_turn(text=text, expected_text=text, product_terms=inputs.terms[index])
            print(f"tú (texto)> {turn.agent_input}")
        parts = ", ".join(f"{STAGE_LABELS[stage]} {turn.timings[stage]:.2f}" for stage in STAGES)
        print(f"agente> {turn.response}\n   [{turn.timings[TOTAL]:.1f} s: {parts}]")
    return pipeline


def run_record(args: argparse.Namespace, inputs: Inputs, loaded: Loaded, main_run: VoicePipeline) -> dict[str, Any]:
    """Todo lo que se guarda de la corrida, salvo la memoria usada, la tienda y la repetición."""
    models, asr, tts = loaded.models, loaded.asr, loaded.tts
    final = main_run.session.state
    return {
        "date": datetime.now().isoformat(timespec="seconds"),
        "note": args.note,
        "mode": inputs.mode,
        "models": {
            "llm": models.llm.model_path.name,
            "asr": asr.model_name if asr else None,
            "tts": "XTTS-v2" if tts else None,
            "embeddings": DEFAULT_DENSE_MODEL,
        },
        "voice": tts.voice if tts else {},
        "load": {
            "search_seconds": round(models.search_seconds, 1),
            "llm_seconds": round(models.llm.load_seconds, 1),
            "asr_seconds": round(asr.load_seconds, 1) if asr else None,
            "tts_seconds": round(tts.load_seconds, 1) if tts else None,
            "total_seconds": round(loaded.seconds, 1),
            "vram_mib": loaded.vram_mib,
        },
        "thread_id": main_run.session.thread_id,
        "turns": [asdict(turn) for turn in main_run.turns],
        "timings": summarize_timings(main_run.turns),
        "final_state": {key: final.get(key) for key in FINAL_STATE_FIELDS},
    }


def text_rerun(repeat: VoicePipeline, main_run: VoicePipeline, store: dict[str, Any], repeat_store: dict[str, Any]) -> dict[str, Any]:
    """Lo que se guarda de la repetición con el texto correcto y su comparación con el audio."""
    return {
        "thread_id": repeat.session.thread_id,
        "turns": [asdict(turn) for turn in repeat.turns],
        "timings": summarize_timings(repeat.turns),
        "store": repeat_store,
        "comparison": compare_runs(main_run.turns, repeat.turns),
        "same_store": comparable_store(repeat_store) == comparable_store(store),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Conversación por voz con el agente de compras.")
    parser.add_argument("--scenario", default=None, help="nombre del escenario: fija --script, --audios, --terms y --out")
    parser.add_argument("--audios", type=Path, default=None, help="carpeta con un audio por turno, en orden de nombre")
    parser.add_argument("--script", type=Path, default=None, help="transcripciones correctas, una por línea")
    parser.add_argument("--terms", type=Path, default=None, help="JSON con los nombres de producto esperados por turno")
    parser.add_argument("--mode", choices=(AUDIO, TEXT, BOTH), default=None, help="con audio, con el texto correcto o las dos")
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
    parser.add_argument(
        "--volatile-memory", action="store_true",
        help="no usa Postgres: los checkpoints y el Store se pierden al terminar",
    )
    args = parser.parse_args()
    scenario_paths(args)
    if args.out is None:
        parser.error("Falta --out (o --scenario)")
    return args


def main() -> None:
    args = parse_args()
    check_memory(args.volatile_memory)
    inputs = read_inputs(args)
    db_path = args.db or args.data / "store.sqlite"
    seed_path = args.data / "store_seed.sqlite"
    if args.restore:
        restore(seed_path, db_path)

    loaded = load_everything(args, inputs.mode)
    print(f"[modelos cargados en {loaded.seconds:.1f} s; VRAM del proceso: {loaded.vram_mib['loaded']} MiB]", file=sys.stderr)
    with open_memory(volatile=args.volatile_memory) as memory:
        graph = build_graph(loaded.models.llm, loaded.models.search, db_path, memory.checkpointer, memory.store)
        thread_id = f"voz-{uuid.uuid4().hex[:8]}"
        session = ShoppingSession(graph, thread_id, args.user)
        main_run = converse(VoicePipeline(session, loaded.asr, loaded.tts, args.out), inputs, inputs.mode != TEXT)
        store = store_snapshot(db_path, seed_path)
        loaded.vram_mib["after_run"] = process_vram_mib()
        record = run_record(args, inputs, loaded, main_run)
        record.update(memory_backend=memory.backend, store=store, text_run=None)

        if inputs.mode == BOTH:
            restore(seed_path, db_path)  # la repetición parte de la misma tienda
            session = ShoppingSession(graph, f"{thread_id}-texto", args.user)
            repeat = converse(VoicePipeline(session, None, None), inputs, use_audio=False)
            record["text_run"] = text_rerun(repeat, main_run, store, store_snapshot(db_path, seed_path))

    (args.out / RECORD_FILE).write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    (args.out / TRANSCRIPT_FILE).write_text(to_markdown(record), encoding="utf-8")
    print(f"[corrida guardada en {args.out}]", file=sys.stderr)


if __name__ == "__main__":
    main()
