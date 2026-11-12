"""¿Estropea la voz hablar más rápido? Los mismos textos a varias velocidades.

Uso::

    python -m shopping_agent.eval.tts_speed --speeds 1.0 1.1 --run results/escenarios/voz_referencia_anterior
    python -m shopping_agent.eval.tts_speed --speeds 1.0 1.1 1.15 1.3 --script frases.txt

Sintetiza con la voz del agente los textos de ``--script`` (uno por línea) y las
respuestas de una corrida de escenarios por voz ya guardada (``--run``: lo que se
envió al TTS en cada turno), una vez por cada velocidad, y mide de cada una:

- la inteligibilidad: WER de Whisper sobre el audio frente al texto sintetizado;
- la semejanza con la grabación de referencia y con las grabaciones reales del
  hablante (``--real``), como en ``shopping_agent.eval.voice``;
- cuánto dura el audio, cuánto tarda la síntesis y cuántos fragmentos hubo que
  repetir por salir demasiado largos.

Escribe ``results/voz_velocidad.json`` y ``.md``. Los audios van a
``audio/corridas/velocidad/<velocidad>/``, fuera de git.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from shopping_agent.eval.scenario_report import load_run, turns_of
from shopping_agent.eval.voice import (
    SIMILARITY,
    SIMILARITY_REAL,
    Compare,
    EcapaEmbedder,
    audio_files,
    normalize,
    pooled_wer,
    similarity_among,
    speaker_comparison,
    wer,
)
from shopping_agent.voice.audio import read_audio, write_wav
from shopping_agent.voice.speech_text import to_speech
from shopping_agent.voice.tts import DEFAULT_SPEED, SpeechSynthesizer, XttsTTS

RESULTS = Path("results/voz_velocidad")
AUDIO_DIR = Path("audio/corridas/velocidad")  # carpeta sin versionar
REAL_DIR = Path("audio/escenarios")  # grabaciones del usuario


def texts_to_speak(script: Path | None, run_dir: Path | None) -> list[str]:
    """Los textos de la medida, sin repetir: las frases del guion, ya en forma apta
    para voz, y lo que una corrida guardada envió al TTS."""
    texts = []
    if script:
        texts += [to_speech(line.strip()) for line in script.read_text(encoding="utf-8").splitlines() if line.strip()]
    if run_dir:
        texts += [turn["spoken_text"] for record in load_run(run_dir)["records"] for turn in turns_of(record) if turn["spoken_text"]]
    return list(dict.fromkeys(texts))


def measure(
    texts: list[str], tts: SpeechSynthesizer, transcribe: Callable[[Path], str], compare: Compare | None, out_dir: Path
) -> list[dict[str, Any]]:
    """Sintetiza cada texto y mide el audio que sale."""
    cases = []
    for number, text in enumerate(texts, 1):
        made = tts.synthesize(text)
        path = write_wav(out_dir / f"{number:02d}.wav", made.audio, made.sample_rate)
        heard = transcribe(path)
        case = {"text": text, "heard": heard, "wer": wer(text, heard), "audio_seconds": made.audio_seconds}
        case |= {"tts_seconds": made.seconds, "retries": made.retries, **(compare(path) if compare else {})}
        cases.append(case)
    return cases


def summarize(cases: list[dict[str, Any]]) -> dict[str, Any]:
    def mean(key: str) -> float | None:
        values = [case[key] for case in cases if key in case]
        return sum(values) / len(values) if values else None

    audio_seconds = sum(case["audio_seconds"] for case in cases)
    words = sum(len(normalize(case["text"]).split()) for case in cases)
    return {
        "texts": len(cases),
        "wer": pooled_wer(case["wer"] for case in cases),
        "exact": sum(1 for case in cases if not case["wer"]["wer"]),
        SIMILARITY: mean(SIMILARITY),
        SIMILARITY_REAL: mean(SIMILARITY_REAL),
        "audio_seconds": audio_seconds,
        "words_per_second": words / audio_seconds if audio_seconds else None,
        "tts_seconds": sum(case["tts_seconds"] for case in cases),
        "retries": sum(case["retries"] for case in cases),
    }


def _cell(value: float | None, digits: int = 3) -> str:
    return "—" if value is None else f"{value:.{digits}f}"


def _difference_lines(speed: str, cases: list[dict[str, Any]]) -> list[str]:
    """Los textos que Whisper no entendió igual a una velocidad."""
    wrong = [case for case in cases if case["wer"]["wer"]]
    lines = [f"### Velocidad {speed}: {len(wrong)} de {len(cases)} textos con alguna palabra distinta", ""]
    lines += [f"- WER {100 * case['wer']['wer']:.0f} %: «{case['text']}» → «{case['heard']}»" for case in wrong]
    return [*lines, ""]


def to_markdown(report: dict[str, Any]) -> str:
    real = report["real_recordings"]
    lines = [
        "# Velocidad del habla e inteligibilidad",
        "",
        f"Los mismos {report['texts']} textos sintetizados con la voz del agente (`{report['voice']['reference'] or report['voice']['speaker']}`) "
        f"a cada velocidad, y transcritos con Whisper `{report['asr_model']}`. La velocidad 1,0 es el ritmo de la grabación de referencia.",
        "",
        "| Velocidad | Inteligibilidad (WER) | Textos entendidos igual | Semejanza con la referencia | Semejanza con las grabaciones reales "
        "| Audio (s) | Palabras por segundo | Síntesis (s) | Fragmentos repetidos |",
        "|---" * 9 + "|",
    ]
    for speed, entry in report["speeds"].items():
        found = entry["summary"]
        cells = [speed, f"{100 * found['wer']:.1f} %", f"{found['exact']} de {found['texts']}", _cell(found[SIMILARITY]), _cell(found[SIMILARITY_REAL])]
        cells += [_cell(found["audio_seconds"], 1), _cell(found["words_per_second"], 2), _cell(found["tts_seconds"], 1), str(found["retries"])]
        lines.append("| " + " | ".join(cells) + " |")
    if real["similarity_among"] is not None:
        lines += ["", f"Las {real['count']} grabaciones reales del hablante se parecen entre sí {real['similarity_among']:.3f} (el techo de esa columna)."]
    lines.append("")
    for speed, entry in report["speeds"].items():
        lines += _difference_lines(speed, entry["cases"])
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mide la voz del agente a varias velocidades del habla.")
    parser.add_argument("--speeds", type=float, nargs="+", default=[1.0, DEFAULT_SPEED])
    parser.add_argument("--script", type=Path, default=None, help="archivo con una frase por línea")
    parser.add_argument("--run", type=Path, default=None, help="corrida de escenarios por voz de la que tomar las respuestas")
    parser.add_argument("--reference", type=Path, default=None, help="grabación de referencia para la voz del agente")
    parser.add_argument("--real", type=Path, default=REAL_DIR, help="grabaciones reales del hablante que no se usan para clonar")
    parser.add_argument("--audio-out", type=Path, default=AUDIO_DIR)
    parser.add_argument("--out", type=Path, default=RESULTS, help="ruta del informe, sin extensión")
    return parser.parse_args()


def main() -> None:
    from shopping_agent.voice.asr import WhisperASR

    args = parse_args()
    texts = texts_to_speak(args.script, args.run)
    tts, asr, embedder = XttsTTS(args.reference), WhisperASR(), EcapaEmbedder()
    real = audio_files(args.real if args.real.is_dir() else None)
    compare = speaker_comparison(embedder, tts.reference, real, read_audio)
    speeds = {}
    for speed in args.speeds:
        tts.speed = speed
        cases = measure(texts, tts, lambda path: asr.transcribe(path).text, compare, args.audio_out / f"{speed:.2f}")
        speeds[f"{speed:.2f}"] = {"summary": summarize(cases), "cases": cases}
        print(f"[velocidad {speed:.2f}: {speeds[f'{speed:.2f}']['summary']}]", flush=True)
    among = similarity_among(embedder, real, read_audio)
    voice = {"reference": str(tts.reference) if tts.reference else None, "speaker": tts.speaker}
    report = {"voice": voice, "asr_model": asr.model_name, "texts": len(texts), "speeds": speeds}
    report["real_recordings"] = {"count": len(real), "similarity_among": among}
    args.out.with_suffix(".json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    args.out.with_suffix(".md").write_text(to_markdown(report), encoding="utf-8")
    print(to_markdown(report))


if __name__ == "__main__":
    main()
