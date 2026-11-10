"""Evaluación con escenarios: los corre por texto o por voz y guarda cada corrida.

Uso::

    python -m shopping_agent.eval.scenarios --mode text
    SHOPPING_AGENT_RERANKER=sage python -m shopping_agent.eval.scenarios --mode text
    SHOPPING_AGENT_RERANKER=off python -m shopping_agent.eval.scenarios --mode text
    python -m shopping_agent.eval.scenarios --synthesize --speaker "Luis Moray"
    python -m shopping_agent.eval.scenarios --mode voice
    python -m shopping_agent.eval.scenarios --recording-script

- ``--mode text`` corre todos los escenarios con el texto de cada turno y guarda
  ``results/escenarios/texto/``; con otro reranker, ``texto_<variante>``, y con el
  reranker apagado, ``texto_sin_reranker``.
- ``--mode voice`` corre los escenarios de voz con audio (``results/escenarios/voz/``)
  y los repite con la transcripción correcta (``voz_texto_correcto``). Usa las
  grabaciones de ``audio/escenarios/<escenario>/NN.wav`` si están todas; si no, los
  audios sintéticos de ``audio/sinteticos/<escenario>/``, que genera ``--synthesize``
  con un hablante incluido en XTTS-v2. De dónde salió el audio queda anotado.
- ``--recording-script`` escribe el guion de lo que hay que grabar.

De cada escenario se guardan la corrida completa (``<escenario>.json``: turnos,
operaciones, tiempos por etapa, instantáneas de la tienda) y su ficha
(``<escenario>.md``). Los audios de entrada y de respuesta van a
``audio/corridas/``, fuera de git. El resumen lo escribe ``scenario_report``.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from shopping_agent.agent.chat import check_memory
from shopping_agent.agent.graph import build_graph
from shopping_agent.agent.memory import open_memory
from shopping_agent.agent.search import DEFAULT_DATA_DIR, RERANKER_DEFAULT
from shopping_agent.eval.provenance import current_commit
from shopping_agent.eval.scenario_format import DEFAULT_DIR, Scenario, load_scenarios, recording_script
from shopping_agent.eval.scenario_report import (
    AUDIO_RUN,
    RUN_FILE,
    TEXT_REPEAT_RUN,
    VOICE_METRICS_FILE,
    Record,
    ficha,
    run_summary,
    turns_of,
)
from shopping_agent.eval.scenario_runner import AUDIO, TEXT, AudioInputs, Bench, ScenarioRun
from shopping_agent.eval.voice import EcapaEmbedder, evaluate_turns, summarize_asr, summarize_tts
from shopping_agent.retrieval.retrievers import DEFAULT_DENSE_MODEL
from shopping_agent.voice import chat as voice_chat
from shopping_agent.voice.audio import read_audio, write_wav
from shopping_agent.voice.speech_text import to_speech
from shopping_agent.voice.tts import XttsTTS

MODE_TEXT, MODE_VOICE = "text", "voice"
RESULTS_DIR = Path("results/escenarios")
RECORDINGS_DIR = voice_chat.SCENARIO_AUDIO_DIR  # grabaciones del usuario
SYNTHETIC_DIR = Path("audio/sinteticos")  # audios de entrada de prueba
RUNS_AUDIO_DIR = Path("audio/corridas")  # audios de cada corrida; carpeta sin versionar
SCRIPT_FILE = "GUION_GRABACION.md"
SOURCE_FILE = "fuente.json"
USER_RECORDING = "grabaciones del usuario"


# --- Audios de entrada --------------------------------------------------------------------


def turn_files(folder: Path, turns: int) -> list[Path] | None:
    """Los audios ``01``, ``02``… de una carpeta; ``None`` si falta alguno."""
    files = []
    for number in range(1, turns + 1):
        found = [path for suffix in voice_chat.AUDIO_SUFFIXES if (path := folder / f"{number:02d}{suffix}").is_file()]
        if not found:
            return None
        files.append(found[0])
    return files


def synthetic_source(folder: Path) -> str:
    source = json.loads((folder / SOURCE_FILE).read_text(encoding="utf-8")) if (folder / SOURCE_FILE).is_file() else {}
    return f"sintéticos, hablante de prueba «{source.get('speaker', 'desconocido')}» de XTTS-v2 (no es la voz del usuario)"


def audio_inputs(scenario: Scenario, recordings: Path, synthetic: Path) -> AudioInputs:
    """Las grabaciones del usuario si están todas; si no, los audios sintéticos."""
    recorded = turn_files(recordings / scenario.id, len(scenario.says))
    if recorded:
        return AudioInputs(USER_RECORDING, recorded)
    generated = turn_files(synthetic / scenario.id, len(scenario.says))
    if generated:
        return AudioInputs(synthetic_source(synthetic / scenario.id), generated)
    sys.exit(f"Faltan los audios de {scenario.id}: grábalos en {recordings / scenario.id} o genera los de prueba con --synthesize.")


def synthesize_inputs(scenarios: list[Scenario], folder: Path, speaker: str) -> None:
    """Audios de entrada de prueba, con un hablante incluido en XTTS-v2."""
    tts = XttsTTS(speaker=speaker)
    for scenario in scenarios:
        target = folder / scenario.id
        for number, say in enumerate(scenario.says, 1):
            result = tts.synthesize(to_speech(say.text))
            write_wav(target / f"{number:02d}.wav", result.audio, result.sample_rate)
            print(f"{target / f'{number:02d}.wav'} ({result.audio_seconds:.1f} s): {say.text}")
        (target / SOURCE_FILE).write_text(json.dumps({"speaker": speaker, "model": "XTTS-v2"}, ensure_ascii=False), encoding="utf-8")


# --- Corrida ------------------------------------------------------------------------------


def run_info(loaded: voice_chat.Loaded, memory_backend: str) -> dict[str, Any]:
    """Con qué se hizo la corrida y cuánto costó cargarlo, aparte de los turnos."""
    models, asr, tts = loaded.models, loaded.asr, loaded.tts
    return {
        "date": datetime.now().isoformat(timespec="seconds"),
        "commit": current_commit(),
        "memory_backend": memory_backend,
        "models": {
            "llm": models.llm.model_path.name,
            "asr": asr.model_name if asr else None,
            "tts": "XTTS-v2" if tts else None,
            "embeddings": DEFAULT_DENSE_MODEL,
            "reranker": models.search.reranker_name,
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
    }


def run_all(
    scenarios: list[Scenario], bench: Bench, run_id: str, inputs: dict[str, AudioInputs] | None, audio_out: Path | None
) -> list[Record]:
    """Corre los escenarios uno tras otro, cada uno desde la tienda inicial."""
    records = []
    for scenario in scenarios:
        audio = inputs[scenario.id] if inputs else None
        out_dir = audio_out / scenario.id if audio_out else None
        record = ScenarioRun(scenario, bench, run_id, audio, out_dir).run()
        records.append(record)
        seconds = sum(turn["timings"]["total"] for turn in turns_of(record))
        print(f"[{'correcto' if record['passed'] else 'FALLO'}] {scenario.id} ({len(turns_of(record))} turnos, {seconds:.0f} s)", flush=True)
    return records


def save_run(out_dir: Path, info: dict[str, Any], records: list[Record]) -> None:
    """Guarda la corrida de cada escenario, su ficha y el índice de la corrida."""
    out_dir.mkdir(parents=True, exist_ok=True)
    for record in records:
        (out_dir / f"{record['id']}.json").write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
        (out_dir / f"{record['id']}.md").write_text(ficha(record), encoding="utf-8")
    rows = [{key: record[key] for key in ("id", "title", "kind", "passed")} for record in records]
    index = {**info, "scenarios": rows, "summary": run_summary(records)}
    (out_dir / RUN_FILE).write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[corrida guardada en {out_dir}: {index['summary']['passed']} de {len(records)} correctos]", file=sys.stderr)


def voice_metrics(records: list[Record], audio_root: Path, loaded: voice_chat.Loaded) -> dict[str, Any]:
    """Errores del ASR, inteligibilidad y semejanza de la voz, por escenario y en conjunto."""
    asr, tts = loaded.asr, loaded.tts
    assert asr is not None and tts is not None  # la corrida por voz carga los dos
    reference = tts.reference
    embedder = EcapaEmbedder() if reference else None

    def transcribe(path: Path) -> str:
        return asr.transcribe(path).text

    scenarios = {
        record["id"]: evaluate_turns(turns_of(record), audio_root / record["id"], transcribe, embedder, reference, read_audio)
        for record in records
    }
    summary = {
        "asr": summarize_asr([case for metrics in scenarios.values() for case in metrics["asr"]["cases"]]),
        "tts": summarize_tts([case for metrics in scenarios.values() for case in metrics["tts"]["cases"]]),
    }
    models = {"asr": asr.model_name, "speaker": EcapaEmbedder.SOURCE if embedder else None}
    return {"summary": summary, "scenarios": scenarios, "models": models, "reference": str(reference) if reference else None}


def text_run_name(reranker: str | None) -> str:
    """``texto`` con el reranker por defecto; si no, el nombre dice cuál se usó."""
    if reranker is None:
        return "texto_sin_reranker"
    return "texto" if reranker == RERANKER_DEFAULT else f"texto_{reranker}"


def run_text(args: argparse.Namespace, scenarios: list[Scenario], bench: Bench, info: dict[str, Any]) -> None:
    name = args.name or text_run_name(info["models"]["reranker"])
    records = run_all(scenarios, bench, f"eval-{uuid.uuid4().hex[:8]}", None, None)
    save_run(args.out / name, {**info, "input": TEXT, "audio_sources": {}}, records)


def run_voice(args: argparse.Namespace, scenarios: list[Scenario], bench: Bench, info: dict[str, Any], loaded: voice_chat.Loaded) -> None:
    """Los escenarios de voz con audio y, después, con la transcripción correcta."""
    inputs = {scenario.id: audio_inputs(scenario, args.recordings, args.synthetic) for scenario in scenarios}
    run_id, audio_root = f"eval-{uuid.uuid4().hex[:8]}", args.audio_out / AUDIO_RUN
    records = run_all(scenarios, bench, run_id, inputs, audio_root)
    sources = {scenario_id: audio.source for scenario_id, audio in inputs.items()}
    save_run(args.out / AUDIO_RUN, {**info, "input": AUDIO, "audio_sources": sources, "audio_dir": str(audio_root)}, records)
    metrics = voice_metrics(records, audio_root, loaded)
    (args.out / AUDIO_RUN / VOICE_METRICS_FILE).write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    repeat = run_all(scenarios, bench, f"{run_id}-texto", None, None)
    save_run(args.out / TEXT_REPEAT_RUN, {**info, "input": TEXT, "audio_sources": {}}, repeat)


# --- Comando ------------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Corre los escenarios de evaluación por texto o por voz.")
    parser.add_argument("--mode", choices=(MODE_TEXT, MODE_VOICE), default=MODE_TEXT)
    parser.add_argument("--scenarios", type=Path, default=DEFAULT_DIR, help="carpeta con los JSON de los escenarios")
    parser.add_argument("--only", nargs="+", default=None, help="identificadores de los escenarios que se corren")
    parser.add_argument("--out", type=Path, default=RESULTS_DIR)
    parser.add_argument("--name", default=None, help="nombre de la corrida por texto (por defecto, según el reranker)")
    parser.add_argument("--recordings", type=Path, default=RECORDINGS_DIR, help="grabaciones del usuario, por escenario")
    parser.add_argument("--synthetic", type=Path, default=SYNTHETIC_DIR, help="audios de entrada sintéticos, por escenario")
    parser.add_argument("--audio-out", type=Path, default=RUNS_AUDIO_DIR, help="audios de las corridas (sin versionar)")
    parser.add_argument("--synthesize", action="store_true", help="genera los audios de entrada sintéticos y termina")
    parser.add_argument("--speaker", default=None, help="hablante incluido en XTTS-v2 para --synthesize")
    parser.add_argument("--recording-script", action="store_true", help="escribe el guion de grabación y termina")
    parser.add_argument("--reference", type=Path, default=None, help="grabación de referencia para la voz del agente")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--n-ctx", type=int, default=8192)
    parser.add_argument("--volatile-memory", action="store_true", help="no usa Postgres para la memoria del agente")
    return parser.parse_args()


def select(scenarios: list[Scenario], only: list[str] | None, voice: bool) -> list[Scenario]:
    chosen = [scenario for scenario in scenarios if (scenario.voice or not voice) and (not only or scenario.id in only)]
    if not chosen:
        sys.exit("Ningún escenario cumple lo pedido.")
    return chosen


def prepare_only(args: argparse.Namespace, scenarios: list[Scenario]) -> bool:
    """Las dos opciones que no corren el agente. Devuelve si se atendió alguna."""
    if args.recording_script:
        (args.scenarios / SCRIPT_FILE).write_text(recording_script(scenarios, str(args.recordings)), encoding="utf-8")
        print(f"[guion en {args.scenarios / SCRIPT_FILE}]", file=sys.stderr)
    elif args.synthesize:
        if not args.speaker:
            sys.exit("--synthesize necesita --speaker (lista: python -m shopping_agent.voice.tts --list-speakers)")
        synthesize_inputs(select(scenarios, args.only, voice=True), args.synthetic, args.speaker)
    return args.recording_script or args.synthesize


def main() -> None:
    args = parse_args()
    scenarios = load_scenarios(args.scenarios)
    if prepare_only(args, scenarios):
        return
    voice = args.mode == MODE_VOICE
    scenarios = select(scenarios, args.only, voice)
    check_memory(args.volatile_memory)
    settings = argparse.Namespace(data=args.data, n_ctx=args.n_ctx, no_tts=not voice, reference=args.reference, speaker=None)
    loaded = voice_chat.load_everything(settings, voice_chat.AUDIO if voice else voice_chat.TEXT)
    with tempfile.TemporaryDirectory() as folder, open_memory(volatile=args.volatile_memory) as memory:
        db_path = Path(folder) / "store.sqlite"  # tienda propia de la corrida, restaurada en cada escenario
        models = loaded.models
        graph = build_graph(models.llm, models.search, db_path, memory.checkpointer, memory.store)
        bench = Bench(graph, models.search, db_path, args.data / "store_seed.sqlite", loaded.asr, loaded.tts)
        info = run_info(loaded, memory.backend)
        if voice:
            run_voice(args, scenarios, bench, info, loaded)
        else:
            run_text(args, scenarios, bench, info)


if __name__ == "__main__":
    main()
