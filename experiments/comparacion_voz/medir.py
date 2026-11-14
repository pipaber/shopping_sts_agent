"""Mide todas las variantes de ``audio/comparacion_voz`` con las mismas reglas.

Por variante: semejanza de hablante (ECAPA) con las grabaciones reales del grupo de
medida, WER de Whisper, velocidad al hablar y tono frente a la voz real, y el tiempo
de síntesis y la memoria que cada script anotó al generar. Entorno del proyecto:

    PYTHONPATH=src python experiments/comparacion_voz/medir.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import librosa
import numpy as np
from comun import CLONE_SCENARIOS, HERE, MEASURE_SCENARIOS, OUT, PREVIOUS_REFERENCE, REFERENCE, recordings, with_text

from shopping_agent.eval.voice import EcapaEmbedder, mean_similarity, pooled_wer, wer
from shopping_agent.voice.asr import WhisperASR
from shopping_agent.voice.audio import read_audio

PITCH_RATE = 16000
PITCH_RANGE = (60.0, 350.0)  # Hz: voz hablada adulta
SILENCE_DB = 35  # por debajo del máximo: lo que cuenta como pausa


def syllables(text: str) -> int:
    """Sílabas aproximadas: grupos de vocales seguidas."""
    return len(re.findall(r"[aeiouáéíóúü]+", text.lower()))


def speech_seconds(audio: np.ndarray, rate: int) -> float:
    """Tiempo hablando, sin las pausas."""
    spans = librosa.effects.split(audio, top_db=SILENCE_DB)
    return float(sum(end - start for start, end in spans) / rate)


def pitch_frames(audio: np.ndarray, rate: int) -> np.ndarray:
    """Tono (Hz) de los tramos con voz."""
    samples = librosa.resample(audio, orig_sr=rate, target_sr=PITCH_RATE)
    f0, voiced, _ = librosa.pyin(samples, fmin=PITCH_RANGE[0], fmax=PITCH_RANGE[1], sr=PITCH_RATE)
    return f0[voiced & ~np.isnan(f0)]


def traits(audios: list[tuple[Path, str]]) -> dict[str, float]:
    """Cómo suena un conjunto de audios: sílabas por segundo hablando, tono medio y
    cuánto se mueve el tono (desviación en semitonos alrededor de la mediana)."""
    spoken, count, tones = 0.0, 0, []
    for path, text in audios:
        audio, rate = read_audio(path)
        spoken += speech_seconds(audio, rate)
        count += syllables(text)
        tones.append(pitch_frames(audio, rate))
    f0 = np.concatenate(tones)
    median = float(np.median(f0))
    spread = float(np.std(12 * np.log2(f0 / median)))
    return {"syllables_per_second": count / spoken, "pitch_hz": median, "pitch_spread_semitones": spread}


def measure_variant(folder: Path, asr: WhisperASR, embedder: EcapaEmbedder, real: list[np.ndarray]) -> dict[str, Any]:
    meta = json.loads((folder / "meta.json").read_text(encoding="utf-8"))
    cases: list[dict[str, Any]] = []
    for phrase in meta["phrases"]:
        path = folder / phrase["file"]
        heard = asr.transcribe(path).text
        similarity = mean_similarity(embedder.embed(*read_audio(path)), real)
        cases.append({**phrase, "heard": heard, "wer": wer(phrase["text"], heard), "similarity_real": similarity})
    audios = [(folder / case["file"], case["text"]) for case in cases]
    return {**{key: meta[key] for key in meta if key != "phrases"}, "cases": cases, "summary": summarize(cases, audios)}


def summarize(cases: list[dict[str, Any]], audios: list[tuple[Path, str]]) -> dict[str, Any]:
    synth = sum(case["synth_seconds"] for case in cases)
    audio = sum(case["audio_seconds"] for case in cases)
    similarities = [case["similarity_real"] for case in cases]
    return {
        "similarity_real_mean": float(np.mean(similarities)),
        "similarity_real_min": float(np.min(similarities)),
        "wer": pooled_wer(case["wer"] for case in cases),
        "exact": sum(case["wer"]["wer"] == 0 for case in cases),
        "synth_seconds": synth,
        "audio_seconds": audio,
        "real_time_factor": synth / audio,
        **traits(audios),
    }


def real_voice(asr: WhisperASR, embedder: EcapaEmbedder, measure: list[np.ndarray]) -> dict[str, dict[str, Any]]:
    """Las filas de la voz real: el techo de la semejanza y con qué comparar ritmo y tono."""
    rest = [measure[:i] + measure[i + 1 :] for i in range(len(measure))]
    among = float(np.mean([mean_similarity(one, others) for one, others in zip(measure, rest)]))
    clone = with_text(CLONE_SCENARIOS)
    turns = float(np.mean([mean_similarity(embedder.embed(*read_audio(path)), measure) for path, _ in clone]))
    rows = {
        "Voz real: grupo de medida (19 turnos, entre sí)": {"similarity_real_mean": among, **traits(with_text(MEASURE_SCENARIOS))},
        "Voz real: 12 turnos del grupo de clonar": {"similarity_real_mean": turns, **traits(clone)},
    }
    for label, path in (("Voz real: grabación de referencia", REFERENCE), ("Voz real: referencia anterior", PREVIOUS_REFERENCE)):
        similarity = mean_similarity(embedder.embed(*read_audio(path)), measure)
        rows[label] = {"similarity_real_mean": similarity, **traits([(path, asr.transcribe(path).text)])}
    return rows


def _row(label: str, s: dict[str, Any], vram: Any = None) -> str:
    def cell(key: str, fmt: str) -> str:
        return format(s[key], fmt) if s.get(key) is not None else "—"

    wer_cell = f"{s['wer']:.1%}".replace("%", " %") if s.get("wer") is not None else "—"
    cells = [label, cell("similarity_real_mean", ".3f"), cell("similarity_real_min", ".3f"), wer_cell]
    cells += [cell("syllables_per_second", ".2f"), cell("pitch_hz", ".0f"), cell("pitch_spread_semitones", ".2f")]
    cells += [cell("synth_seconds", ".1f"), cell("real_time_factor", ".2f"), str(vram) if vram else "—"]
    return "| " + " | ".join(cells) + " |"


def to_markdown(report: dict[str, Any]) -> str:
    header = "| Variante | Semejanza (media) | Semejanza (mín.) | WER | Sílabas/s | Tono (Hz) | Variación del tono (st) "
    header += "| Síntesis (s) | Síntesis / audio | VRAM (MiB) |"
    lines = ["# Comparación de voces: resultados", "", header, "|" + "---|" * 10]
    lines += [_row(label, row) for label, row in report["real"].items()]
    for name, variant in report["variants"].items():
        lines.append(_row(f"`{name}`", variant["summary"], variant.get("process_vram_mib")))
    lines += ["", "## Qué es cada variante", ""]
    lines += [f"- `{name}`: {variant['description']}." for name, variant in report["variants"].items()]
    lines += ["", "## Lo que Whisper entendió en la frase 7 (marcas difíciles)", ""]
    lines += [f"- `{name}` (WER {v['cases'][6]['wer']['wer']:.0%}): «{v['cases'][6]['heard']}»" for name, v in report["variants"].items()]
    return "\n".join(lines) + "\n"


def listening_guide(report: dict[str, Any]) -> str:
    """Lo que hay en cada carpeta de audios, para escucharlos sin abrir el repositorio."""
    lines = ["Comparación de voces: diez frases (frases.txt) dichas por cada variante, NN.wav = frase NN.", ""]
    lines += ["voz_real/: grabaciones reales del autor que ninguna variante usó para clonar.", ""]
    lines += [f"{name}/: {variant['description']}." for name, variant in report["variants"].items()]
    return "\n".join(lines) + "\n"


def main() -> None:
    asr, embedder = WhisperASR(), EcapaEmbedder()
    measure = [embedder.embed(*read_audio(path)) for path in recordings(MEASURE_SCENARIOS)]
    folders = sorted(path.parent for path in OUT.glob("*/meta.json"))
    variants = {folder.name: measure_variant(folder, asr, embedder, measure) for folder in folders}
    report = {"asr_model": asr.model_name, "real": real_voice(asr, embedder, measure), "variants": variants}
    (HERE / "resultados.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    (HERE / "RESULTADOS.md").write_text(to_markdown(report), encoding="utf-8")
    (OUT / "LEEME.txt").write_text(listening_guide(report), encoding="utf-8")
    print(to_markdown(report))


if __name__ == "__main__":
    main()
