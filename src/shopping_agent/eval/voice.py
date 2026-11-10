"""Métricas de voz: inteligibilidad, semejanza con la referencia y errores del ASR.

- **Inteligibilidad:** WER de Whisper sobre el audio sintetizado frente al texto
  que se envió al TTS.
- **Semejanza:** coseno entre los embeddings de hablante (ECAPA-TDNN) de la
  grabación de referencia y de la síntesis.
- **Errores del ASR:** además del WER, qué cantidades, importes y nombres de
  producto del texto correcto no llegaron a la transcripción.

Uso, sobre una corrida guardada por ``shopping_agent.voice.pipeline``::

    python -m shopping_agent.eval.voice results/voz_compra
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Callable, Iterable, Protocol, Sequence

import numpy as np

from shopping_agent.voice.speech_text import to_speech

# --- Normalización y WER --------------------------------------------------------------


def _fold(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.lower())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def normalize(text: str) -> str:
    """Forma comparable de un texto: cifras en palabras, minúsculas, sin tildes ni
    puntuación. Así "60 €", "60 euros" y "sesenta euros" cuentan como lo mismo, y
    una tilde de más o de menos no cuenta como error de reconocimiento."""
    return " ".join(re.findall(r"[a-z0-9]+", _fold(to_speech(text)).replace("'", "")))


def wer(reference: str, hypothesis: str) -> dict[str, Any]:
    """Tasa de error por palabra entre dos textos, ya normalizados aquí dentro."""
    import jiwer

    ref, hyp = normalize(reference), normalize(hypothesis)
    ref_words, hyp_words = len(ref.split()), len(hyp.split())
    if ref_words == 0:
        return {
            "wer": 0.0 if hyp_words == 0 else None, "reference_words": 0, "hits": 0,
            "substitutions": 0, "deletions": 0, "insertions": hyp_words,
        }
    if hyp_words == 0:
        return {
            "wer": 1.0, "reference_words": ref_words, "hits": 0,
            "substitutions": 0, "deletions": ref_words, "insertions": 0,
        }
    output = jiwer.process_words(ref, hyp)
    return {
        "wer": output.wer, "reference_words": ref_words, "hits": output.hits,
        "substitutions": output.substitutions, "deletions": output.deletions, "insertions": output.insertions,
    }


def pooled_wer(results: Iterable[dict[str, Any]]) -> float | None:
    """WER del conjunto: errores totales entre palabras de referencia totales."""
    results = list(results)
    words = sum(result["reference_words"] for result in results)
    errors = sum(result["substitutions"] + result["deletions"] + result["insertions"] for result in results)
    return errors / words if words else None


# --- Cantidades e importes ------------------------------------------------------------

_UNIT_VALUES = {
    word: value
    for value, word in enumerate(
        "cero uno dos tres cuatro cinco seis siete ocho nueve diez once doce trece catorce quince dieciseis "
        "diecisiete dieciocho diecinueve veinte veintiuno veintidos veintitres veinticuatro veinticinco "
        "veintiseis veintisiete veintiocho veintinueve".split()
    )
}
_UNIT_VALUES.update({"un": 1, "una": 1, "veintiun": 21, "veintiuna": 21})
_TENS_VALUES = {
    "treinta": 30, "cuarenta": 40, "cincuenta": 50, "sesenta": 60, "setenta": 70, "ochenta": 80, "noventa": 90,
}
_HUNDRED_VALUES = {"cien": 100, "ciento": 100}
for _value, _stem in enumerate(
    "doscient trescient cuatrocient quinient seiscient setecient ochocient novecient".split(), start=2
):
    _HUNDRED_VALUES[_stem + "os"] = _HUNDRED_VALUES[_stem + "as"] = _value * 100
_MILLION = ("millon", "millones")
_EUROS = ("euro", "euros")
_CENTS = ("centimo", "centimos")
_COUNTED = frozenset((*_EUROS, *_CENTS, "unidad", "unidades"))


def _under_1000(tokens: Sequence[str], index: int) -> tuple[int, int] | None:
    start, value = index, 0
    if index < len(tokens) and tokens[index] in _HUNDRED_VALUES:
        value += _HUNDRED_VALUES[tokens[index]]
        index += 1
        if tokens[index - 1] == "cien":
            return value, index
    if index < len(tokens) and tokens[index] in _TENS_VALUES:
        value += _TENS_VALUES[tokens[index]]
        index += 1
        if index + 1 < len(tokens) and tokens[index] == "y" and 1 <= _UNIT_VALUES.get(tokens[index + 1], 0) <= 9:
            value += _UNIT_VALUES[tokens[index + 1]]
            index += 2
    elif index < len(tokens) and tokens[index] in _UNIT_VALUES:
        value += _UNIT_VALUES[tokens[index]]
        index += 1
    return (value, index) if index > start else None


def read_number(tokens: Sequence[str], index: int) -> tuple[int, int] | None:
    """Lee un número en palabras que empiece en ``tokens[index]``: ``(valor, índice siguiente)``."""
    start, total = index, 0
    group = _under_1000(tokens, index)
    if group and group[1] < len(tokens) and tokens[group[1]] in _MILLION:
        total += group[0] * 10**6
        index = group[1] + 1
        group = _under_1000(tokens, index)
    if group and group[1] < len(tokens) and tokens[group[1]] == "mil":
        total += group[0] * 1000
        index = group[1] + 1
        group = _under_1000(tokens, index)
    elif not group and index < len(tokens) and tokens[index] == "mil":
        total += 1000
        index += 1
        group = _under_1000(tokens, index)
    if group:
        total += group[0]
        index = group[1]
    return (total, index) if index > start else None


@dataclass
class Figures:
    amounts: list[int] = field(default_factory=list)  # en céntimos
    quantities: list[int] = field(default_factory=list)


def extract_figures(text: str) -> Figures:
    """Importes (en céntimos) y cantidades que menciona un texto, vengan en cifras o
    en palabras. "un" y "una" sueltos son artículos y no cuentan como cantidad."""
    tokens = re.findall(r"[a-z0-9]+|[^\sa-z0-9]", _fold(to_speech(text)).replace("'", ""))
    figures = Figures()
    index = 0
    while index < len(tokens):
        number = read_number(tokens, index)
        if number is None:
            index += 1
            continue
        value, after = number
        following = tokens[after] if after < len(tokens) else ""
        if after - index == 1 and tokens[index] in ("un", "una") and following not in _COUNTED:
            index = after
            continue
        if following in _EUROS:
            cents = value * 100
            after += 1
            if after < len(tokens) and tokens[after] == "con":
                fraction = read_number(tokens, after + 1)
                if fraction and fraction[1] < len(tokens) and tokens[fraction[1]] in _CENTS:
                    cents += fraction[0]
                    after = fraction[1] + 1
            figures.amounts.append(cents)
        elif following in _CENTS:
            figures.amounts.append(value)
            after += 1
        else:
            figures.quantities.append(value)
        index = after
    return figures


def _difference(reference: list[int], hypothesis: list[int]) -> dict[str, Any]:
    missing = sorted((Counter(reference) - Counter(hypothesis)).elements())
    extra = sorted((Counter(hypothesis) - Counter(reference)).elements())
    return {
        "reference": reference, "hypothesis": hypothesis, "missing": missing, "extra": extra,
        # una cifra cambiada por otra es un error, no dos
        "errors": max(len(missing), len(extra)),
    }


def compare_figures(reference: str, hypothesis: str) -> dict[str, dict[str, Any]]:
    ref, hyp = extract_figures(reference), extract_figures(hypothesis)
    return {
        "amounts": _difference(ref.amounts, hyp.amounts),
        "quantities": _difference(ref.quantities, hyp.quantities),
    }


# --- Nombres de producto --------------------------------------------------------------


def _closest(term_words: list[str], words: list[str]) -> tuple[str, float]:
    best, best_ratio = "", 0.0
    size = len(term_words)
    term = " ".join(term_words)
    for start in range(max(1, len(words) - size + 1)):
        window = " ".join(words[start : start + size])
        ratio = SequenceMatcher(None, term, window).ratio()
        if ratio > best_ratio:
            best, best_ratio = window, ratio
    return best, best_ratio


def compare_terms(terms: Iterable[str], hypothesis: str) -> dict[str, Any]:
    """Qué nombres (producto, marca) del texto correcto no aparecen en la transcripción.
    Para cada ausente se da el tramo más parecido, que suele ser lo que entendió el ASR."""
    words = normalize(hypothesis).split()
    padded = f" {' '.join(words)} "
    total, missing = 0, []
    for term in terms:
        term_words = normalize(term).split()
        if not term_words:
            continue
        total += 1
        if f" {' '.join(term_words)} " not in padded:
            closest, ratio = _closest(term_words, words)
            missing.append({"term": term, "closest": closest, "similarity": round(ratio, 2)})
    return {"total": total, "missing": missing, "errors": len(missing)}


def asr_errors(reference: str, hypothesis: str, product_terms: Iterable[str] = ()) -> dict[str, Any]:
    """Comparación completa de una transcripción con el texto correcto."""
    return {
        "reference": reference,
        "hypothesis": hypothesis,
        "wer": wer(reference, hypothesis),
        **compare_figures(reference, hypothesis),
        "products": compare_terms(product_terms, hypothesis),
    }


def summarize_asr(cases: Sequence[dict[str, Any]]) -> dict[str, Any]:
    def rate(key: str) -> dict[str, Any]:
        total = sum(case[key]["total"] if key == "products" else len(case[key]["reference"]) for case in cases)
        errors = sum(case[key]["errors"] for case in cases)
        return {"total": total, "errors": errors, "error_rate": errors / total if total else None}

    return {
        "cases": len(cases),
        "wer": pooled_wer(case["wer"] for case in cases),
        "exact": sum(1 for case in cases if normalize(case["reference"]) == normalize(case["hypothesis"])),
        "amounts": rate("amounts"),
        "quantities": rate("quantities"),
        "products": rate("products"),
    }


# --- Semejanza de hablante ------------------------------------------------------------


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    a, b = np.asarray(a, dtype=np.float64).ravel(), np.asarray(b, dtype=np.float64).ravel()
    norm = np.linalg.norm(a) * np.linalg.norm(b)
    return float(a @ b / norm) if norm else 0.0


class SpeakerEmbedder(Protocol):
    def embed(self, audio: np.ndarray, rate: int) -> np.ndarray: ...


class EcapaEmbedder:
    """ECAPA-TDNN de SpeechBrain entrenado en VoxCeleb (verificación de hablante).

    Es un modelo distinto del codificador de voz de XTTS-v2, así que la semejanza
    no se mide con el mismo modelo que hizo la clonación. Va en CPU por defecto:
    solo se usa al evaluar y no ocupa VRAM del sistema.
    """

    SOURCE = "speechbrain/spkrec-ecapa-voxceleb"
    RATE = 16000

    def __init__(self, device: str = "cpu") -> None:
        from speechbrain.inference.speaker import EncoderClassifier

        self.model = EncoderClassifier.from_hparams(source=self.SOURCE, run_opts={"device": device})
        self.device = device

    def embed(self, audio: np.ndarray, rate: int) -> np.ndarray:
        import torch

        from shopping_agent.voice.audio import resample

        samples = torch.from_numpy(resample(audio, rate, self.RATE)).unsqueeze(0).to(self.device)
        with torch.no_grad():
            return self.model.encode_batch(samples).squeeze().cpu().numpy()


def speaker_similarity(embedder: SpeakerEmbedder, reference: tuple[np.ndarray, int], sample: tuple[np.ndarray, int]) -> float:
    """Coseno entre los embeddings de hablante de dos audios ``(muestras, frecuencia)``."""
    return cosine(embedder.embed(*reference), embedder.embed(*sample))


# --- Evaluación de una corrida guardada -----------------------------------------------


def evaluate_run(
    run_dir: Path,
    transcribe: Callable[[Path], str],
    embedder: SpeakerEmbedder | None,
    reference_audio: Path | None,
    read: Callable[[Path], tuple[np.ndarray, int]],
) -> dict[str, Any]:
    """Calcula las tres métricas sobre los turnos guardados en ``run_dir/turnos.json``.

    ``transcribe`` y ``embedder`` llegan desde fuera para poder probar esta función
    sin modelos.
    """
    record = json.loads((run_dir / "turnos.json").read_text(encoding="utf-8"))
    reference = read(reference_audio) if embedder is not None and reference_audio else None

    asr_cases, tts_cases = [], []
    for turn in record["turns"]:
        expected = turn.get("expected_text")
        if expected and turn.get("transcript") is not None and turn.get("input_audio"):
            case = asr_errors(expected, turn["transcript"], turn.get("product_terms") or ())
            asr_cases.append({"turn": turn["turn"], **case})
        if turn.get("output_audio") and turn.get("spoken_text"):
            path = run_dir / turn["output_audio"]
            heard = transcribe(path)
            case = {"turn": turn["turn"], "spoken_text": turn["spoken_text"], "heard": heard, "wer": wer(turn["spoken_text"], heard)}
            if reference is not None and embedder is not None:
                case["similarity"] = speaker_similarity(embedder, reference, read(path))
            tts_cases.append(case)

    similarities = [case["similarity"] for case in tts_cases if "similarity" in case]
    return {
        "asr": {"summary": summarize_asr(asr_cases), "cases": asr_cases},
        "tts": {
            "summary": {
                "cases": len(tts_cases),
                "wer": pooled_wer(case["wer"] for case in tts_cases),
                "similarity_mean": float(np.mean(similarities)) if similarities else None,
                "similarity_min": float(np.min(similarities)) if similarities else None,
            },
            "cases": tts_cases,
        },
    }


def _percent(value: float | None) -> str:
    return "—" if value is None else f"{100 * value:.1f} %"


def to_markdown(metrics: dict[str, Any]) -> str:
    asr, tts = metrics["asr"]["summary"], metrics["tts"]["summary"]
    lines = [
        "# Métricas de voz",
        "",
        "## Errores del ASR (transcripción frente al texto correcto)",
        "",
        f"- Turnos comparados: {asr['cases']}; idénticos tras normalizar: {asr['exact']}",
        f"- WER: {_percent(asr['wer'])}",
    ]
    for key, label in (("amounts", "Importes"), ("quantities", "Cantidades"), ("products", "Nombres de producto")):
        lines.append(f"- {label}: {asr[key]['errors']} errores de {asr[key]['total']} ({_percent(asr[key]['error_rate'])})")
    for case in metrics["asr"]["cases"]:
        problems = []
        for key in ("amounts", "quantities"):
            if case[key]["errors"]:
                problems.append(f"{key}: faltan {case[key]['missing']}, sobran {case[key]['extra']}")
        for miss in case["products"]["missing"]:
            problems.append(f"producto «{miss['term']}» → «{miss['closest']}»")
        if problems or case["wer"]["wer"]:
            lines += ["", f"- Turno {case['turn']} (WER {_percent(case['wer']['wer'])}): «{case['reference']}» → «{case['hypothesis']}»"]
            lines += [f"  - {problem}" for problem in problems]
    lines += [
        "",
        "## Voz sintetizada",
        "",
        f"- Respuestas evaluadas: {tts['cases']}",
        f"- Inteligibilidad (WER de Whisper sobre la síntesis): {_percent(tts['wer'])}",
    ]
    if tts["similarity_mean"] is not None:
        lines.append(
            f"- Semejanza con la referencia (coseno ECAPA): media {tts['similarity_mean']:.3f}, mínima {tts['similarity_min']:.3f}"
        )
    for case in metrics["tts"]["cases"]:
        similarity = f", semejanza {case['similarity']:.3f}" if "similarity" in case else ""
        lines.append(f"- Turno {case['turn']}: WER {_percent(case['wer']['wer'])}{similarity}")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Métricas de voz sobre una corrida guardada.")
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--reference", type=Path, default=None, help="grabación de referencia (por defecto, la de la corrida)")
    parser.add_argument("--no-similarity", action="store_true")
    args = parser.parse_args()

    from shopping_agent.voice.asr import WhisperASR
    from shopping_agent.voice.audio import read_audio

    record = json.loads((args.run_dir / "turnos.json").read_text(encoding="utf-8"))
    reference = args.reference or (Path(record["voice"]["reference"]) if record.get("voice", {}).get("reference") else None)
    asr = WhisperASR()
    embedder = None if args.no_similarity or reference is None else EcapaEmbedder()
    metrics = evaluate_run(args.run_dir, lambda path: asr.transcribe(path).text, embedder, reference, read_audio)
    metrics["models"] = {"asr": asr.model_name, "speaker": EcapaEmbedder.SOURCE if embedder else None}
    metrics["reference"] = str(reference) if reference else None
    (args.run_dir / "metricas.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    (args.run_dir / "metricas.md").write_text(to_markdown(metrics), encoding="utf-8")
    print(to_markdown(metrics))


if __name__ == "__main__":
    main()
