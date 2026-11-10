"""Síntesis de voz con XTTS-v2 y clonación desde una grabación de referencia.

Uso::

    python -m shopping_agent.voice.tts --list-speakers
    python -m shopping_agent.voice.tts --text "Hola, ¿qué buscas hoy?" --out saludo.wav
    python -m shopping_agent.voice.tts --script scenarios/demo_compra.txt --out-dir audio/sinteticos/demo_compra

La voz sale de la grabación de referencia: ``--reference``, ``SHOPPING_AGENT_VOICE_REF``
o, por defecto, ``audio/referencia/referencia.wav`` (mono o estéreo, a cualquier
frecuencia de muestreo). Mientras no exista esa grabación se puede desarrollar con
uno de los hablantes que trae XTTS-v2 (``--speaker`` o ``SHOPPING_AGENT_TTS_SPEAKER``);
no se clona la voz de nadie que no la haya cedido.

XTTS-v2 se publica con la licencia CPML de Coqui (uso no comercial). Este módulo
no la acepta por nadie: si no consta aceptada, se detiene y explica cómo hacerlo.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

import numpy as np

from shopping_agent.gpu import process_vram_mib
from shopping_agent.voice.audio import write_wav
from shopping_agent.voice.speech_text import split_for_tts, to_speech

MODEL_NAME = "tts_models/multilingual/multi-dataset/xtts_v2"
REFERENCE_ENV = "SHOPPING_AGENT_VOICE_REF"
SPEAKER_ENV = "SHOPPING_AGENT_TTS_SPEAKER"
DEFAULT_REFERENCE = Path("audio/referencia/referencia.wav")  # carpeta sin versionar
LICENSE_URL = "https://tts-hub.github.io/cpml"  # la dirección que muestra el propio paquete
SAMPLE_RATE = 24000  # salida de XTTS-v2
MAX_CHARS = 200  # por debajo del límite de 239 caracteres de XTTS-v2 en español
PAUSE_SECONDS = 0.25  # silencio entre fragmentos
MAX_ATTEMPTS = 3  # síntesis de un fragmento antes de quedarse con la más corta


class LicenseNotAccepted(RuntimeError):
    """El usuario todavía no ha aceptado la licencia CPML de XTTS-v2."""


class VoiceNotConfigured(RuntimeError):
    """No hay grabación de referencia ni se ha elegido un hablante incluido."""


@dataclass
class Synthesis:
    audio: np.ndarray  # mono float32
    sample_rate: int
    seconds: float  # tiempo de síntesis completo
    first_chunk_seconds: float  # cuándo podría empezar a sonar el primer fragmento
    audio_seconds: float
    chunks: list[str] = field(default_factory=list)
    retries: int = 0  # fragmentos que hubo que volver a sintetizar por salir demasiado largos


class SpeechSynthesizer(Protocol):
    """Lo que el turno por voz necesita de un TTS (permite sustituirlo en las pruebas)."""

    sample_rate: int

    def synthesize(self, text: str) -> Synthesis: ...


def too_long(audio_seconds: float, characters: int) -> bool:
    """¿Dura el audio mucho más de lo razonable para su texto?

    XTTS-v2 a veces sigue "hablando" después del texto, sobre todo con frases muy
    cortas ("Sí." puede salir con cinco segundos de balbuceo). El habla normal medida
    con este modelo va de 0,05 a 0,10 s por carácter según la voz; el umbral deja
    margen de sobra para una voz pausada y solo salta cuando claramente sobra audio.
    """
    return audio_seconds > 2.0 + 0.15 * characters


def join_chunks(pieces: list[np.ndarray], sample_rate: int, pause_seconds: float = PAUSE_SECONDS) -> np.ndarray:
    """Une los fragmentos sintetizados con un silencio corto entre ellos."""
    if not pieces:
        return np.zeros(0, dtype=np.float32)
    pause = np.zeros(int(sample_rate * pause_seconds), dtype=np.float32)
    joined: list[np.ndarray] = []
    for index, piece in enumerate(pieces):
        if index:
            joined.append(pause)
        joined.append(np.asarray(piece, dtype=np.float32).reshape(-1))
    return np.concatenate(joined)


def resolve_voice(reference: str | Path | None = None, speaker: str | None = None) -> tuple[Path | None, str | None]:
    """Decide de dónde sale la voz.

    Los argumentos mandan. Sin ellos: la grabación de ``SHOPPING_AGENT_VOICE_REF``, la
    grabación de la ruta por defecto si existe y, solo si no hay ninguna, el hablante
    incluido de ``SHOPPING_AGENT_TTS_SPEAKER``.
    """
    if reference is None and speaker is None:
        reference = os.environ.get(REFERENCE_ENV) or (DEFAULT_REFERENCE if DEFAULT_REFERENCE.is_file() else None)
        speaker = os.environ.get(SPEAKER_ENV) or None
    if reference:
        path = Path(reference).expanduser()
        if not path.is_file():
            raise VoiceNotConfigured(f"No existe la grabación de referencia: {path}")
        return path, None
    if speaker:
        return None, speaker
    raise VoiceNotConfigured(
        f"Falta la voz: deja tu grabación de referencia en {DEFAULT_REFERENCE} (o indica otra ruta en "
        f"{REFERENCE_ENV}) o, para pruebas, elige en {SPEAKER_ENV} uno de los hablantes incluidos en "
        "XTTS-v2 (--list-speakers)."
    )


def ensure_model() -> tuple[Path, Path]:
    """Carpeta del modelo y ruta de su configuración, descargándolo si hace falta.

    Solo descarga si la licencia consta aceptada (el marcador que deja Coqui o
    ``COQUI_TOS_AGREED=1``). En una terminal interactiva Coqui pregunta al usuario;
    sin terminal, se detiene aquí en vez de quedarse esperando una respuesta.
    """
    from TTS.utils.manage import ModelManager

    manager = ModelManager(progress_bar=sys.stderr.isatty())
    item, full_name, _ = manager._set_model_item(MODEL_NAME)
    marker_dir = manager.output_prefix / full_name
    if not manager.tos_agreed(item, marker_dir) and not sys.stdin.isatty():
        raise LicenseNotAccepted(
            "XTTS-v2 requiere aceptar la licencia CPML de Coqui (uso no comercial): "
            f"{LICENSE_URL}. Si la aceptas, añade COQUI_TOS_AGREED=1 a tu .env, o ejecuta este "
            "comando en una terminal y responde a la pregunta de Coqui."
        )
    model_path, config_path, _ = manager.download_model(MODEL_NAME)
    model_dir = Path(model_path)
    if model_dir.is_file():
        model_dir = model_dir.parent
    return model_dir, Path(config_path) if config_path else model_dir / "config.json"


class XttsTTS:
    """XTTS-v2 con una voz fija: clonada de una grabación o un hablante incluido."""

    sample_rate = SAMPLE_RATE

    def __init__(
        self,
        reference: str | Path | None = None,
        speaker: str | None = None,
        *,
        language: str = "es",
        device: str = "auto",
        temperature: float = 0.65,
        seed: int = 0,
        max_chars: int = MAX_CHARS,
    ) -> None:
        import torch

        self.reference, self.speaker = resolve_voice(reference, speaker)
        self.language = language
        self.temperature = temperature
        self.seed = seed
        self.max_chars = max_chars
        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device

        vram_before = process_vram_mib() or 0
        start = time.perf_counter()
        model_dir, config_path = ensure_model()

        from TTS.tts.configs.xtts_config import XttsConfig
        from TTS.tts.models.xtts import Xtts

        config = XttsConfig()
        config.load_json(str(config_path))
        self.model = Xtts.init_from_config(config)
        self.model.load_checkpoint(config, checkpoint_dir=str(model_dir), eval=True)
        self.model.to(device)
        self.model_dir = model_dir

        if self.reference is not None:
            self.gpt_cond_latent, self.speaker_embedding = self.model.get_conditioning_latents(
                audio_path=[str(self.reference)]
            )
        else:
            speakers = self.speaker_names
            if self.speaker not in speakers:
                raise VoiceNotConfigured(
                    f"XTTS-v2 no trae el hablante {self.speaker!r}. Disponibles: {', '.join(sorted(speakers))}"
                )
            latent, embedding = self.model.speaker_manager.speakers[self.speaker].values()
            self.gpt_cond_latent, self.speaker_embedding = latent.to(device), embedding.to(device)

        self._generate("Hola.")  # deja fuera del primer turno la inicialización perezosa
        self._release_gpu_cache()
        self.load_seconds = time.perf_counter() - start
        vram_after = process_vram_mib()
        self.vram_mib = None if vram_after is None else vram_after - vram_before

    @property
    def speaker_names(self) -> list[str]:
        manager = getattr(self.model, "speaker_manager", None)
        return list(manager.speakers) if manager is not None else []

    @property
    def voice(self) -> dict[str, Any]:
        """De dónde sale la voz, para dejarlo escrito en los resultados."""
        if self.reference is not None:
            return {"mode": "referencia", "reference": str(self.reference), "speaker": None}
        return {"mode": "hablante_incluido", "reference": None, "speaker": self.speaker}

    def _generate(self, text: str) -> np.ndarray:
        import torch

        with torch.inference_mode():
            output = self.model.inference(
                text,
                self.language,
                self.gpt_cond_latent,
                self.speaker_embedding,
                temperature=self.temperature,
                enable_text_splitting=False,
            )
        wav = output["wav"]
        if hasattr(wav, "cpu"):
            wav = wav.cpu().numpy()
        return np.asarray(wav, dtype=np.float32).reshape(-1)

    def _generate_checked(self, chunk: str) -> tuple[np.ndarray, int]:
        """Sintetiza un fragmento; si sale demasiado largo lo reintenta con otra semilla
        y se queda con el intento más corto. Devuelve el audio y los reintentos."""
        import torch

        best: np.ndarray | None = None
        for attempt in range(MAX_ATTEMPTS):
            torch.manual_seed(self.seed + attempt)  # muestreo aleatorio: misma entrada, misma salida
            audio = self._generate(chunk)
            if best is None or len(audio) < len(best):
                best = audio
            if not too_long(len(audio) / self.sample_rate, len(chunk)):
                return audio, attempt
        assert best is not None
        return best, MAX_ATTEMPTS - 1

    def _release_gpu_cache(self) -> None:
        """Devuelve a la GPU la memoria que PyTorch se queda en reserva tras sintetizar.

        El LLM (llama.cpp) y Whisper (CTranslate2) reservan memoria fuera de PyTorch:
        si este acapara la que ya no usa (cerca de 1 GB tras una respuesta larga), a
        los otros puede faltarles.
        """
        if self.device != "cpu":
            import torch

            torch.cuda.empty_cache()

    def synthesize(self, text: str) -> Synthesis:
        """Sintetiza un texto ya preparado para voz (véase ``speech_text.to_speech``)."""
        chunks = split_for_tts(text, self.max_chars)
        start = time.perf_counter()
        pieces, first, retries = [], 0.0, 0
        for index, chunk in enumerate(chunks):
            audio, attempts = self._generate_checked(chunk)
            pieces.append(audio)
            retries += attempts
            if index == 0:
                first = time.perf_counter() - start
        audio = join_chunks(pieces, self.sample_rate)
        self._release_gpu_cache()
        return Synthesis(
            audio=audio,
            sample_rate=self.sample_rate,
            seconds=time.perf_counter() - start,
            first_chunk_seconds=first,
            audio_seconds=len(audio) / self.sample_rate,
            chunks=chunks,
            retries=retries,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Síntesis de voz con XTTS-v2.")
    parser.add_argument("--reference", type=Path, default=None, help="grabación de referencia para clonar la voz")
    parser.add_argument("--speaker", default=None, help="hablante incluido en XTTS-v2 (solo para pruebas)")
    parser.add_argument("--list-speakers", action="store_true")
    parser.add_argument("--text", default=None)
    parser.add_argument("--out", type=Path, default=None, help="WAV de salida para --text")
    parser.add_argument("--script", type=Path, default=None, help="archivo con una frase por línea")
    parser.add_argument("--out-dir", type=Path, default=None, help="carpeta de salida para --script (01.wav, 02.wav…)")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    try:
        if args.list_speakers:
            import torch

            model_dir, _ = ensure_model()
            print("\n".join(sorted(torch.load(model_dir / "speakers_xtts.pth", weights_only=True))))
            return
        tts = XttsTTS(args.reference, args.speaker, seed=args.seed)
    except (LicenseNotAccepted, VoiceNotConfigured) as error:
        sys.exit(str(error))
    print(f"[XTTS-v2 en {tts.device}; voz: {tts.voice}; carga {tts.load_seconds:.1f} s; VRAM {tts.vram_mib} MiB]", file=sys.stderr)

    jobs: list[tuple[str, Path]] = []
    if args.text:
        jobs.append((args.text, args.out or Path("salida.wav")))
    if args.script:
        out_dir = args.out_dir or args.script.with_suffix("")
        lines = [line.strip() for line in args.script.read_text(encoding="utf-8").splitlines() if line.strip()]
        jobs += [(line, out_dir / f"{number:02d}.wav") for number, line in enumerate(lines, 1)]
    for text, path in jobs:
        result = tts.synthesize(to_speech(text))
        write_wav(path, result.audio, result.sample_rate)
        retried = f", {result.retries} reintentos" if result.retries else ""
        print(f"{path} ({result.audio_seconds:.1f} s de audio en {result.seconds:.1f} s{retried}): {text}")


if __name__ == "__main__":
    main()
