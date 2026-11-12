"""Conversación por voz en vivo: un proceso carga los modelos una vez y atiende turnos.

Uso::

    python -m shopping_agent.voice.live --restore

Abre un servidor HTTP en ``127.0.0.1`` (``--port``, por defecto 8765) y contesta en
JSON. Lo usa quien no puede importar el paquete, como las celdas de un notebook:

- ``GET /health``: ``ready`` es ``false`` mientras cargan los modelos.
- ``POST /turn`` con ``{"audio": "/ruta/turno.wav"}`` o ``{"text": "…"}``: un turno.
- ``POST /reset`` con ``{"restore": true|false}``: conversación nueva.

Los turnos se atienden de uno en uno. Cada conversación deja sus audios en
``audio/corridas/en_vivo/<hilo>/`` (sin versionar) y su transcripción en
``results/en_vivo/<hilo>/``, que se reescribe tras cada turno.
"""

from __future__ import annotations

import argparse
import json
import logging
import signal
import sys
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from shopping_agent.agent.chat import check_memory
from shopping_agent.agent.graph import build_graph
from shopping_agent.agent.memory import open_memory
from shopping_agent.agent.report import SUMMARY_CHARS, store_snapshot
from shopping_agent.agent.search import DEFAULT_DATA_DIR
from shopping_agent.agent.session import ShoppingSession
from shopping_agent.gpu import process_vram_mib
from shopping_agent.store.db import restore
from shopping_agent.voice import chat as voice_chat
from shopping_agent.voice.asr import SpeechRecognizer
from shopping_agent.voice.pipeline import VoicePipeline, VoiceTurn
from shopping_agent.voice.report import to_markdown, voice_label
from shopping_agent.voice.tts import SpeechSynthesizer

HOST, DEFAULT_PORT = "127.0.0.1", 8765
AUDIO_DIR = Path("audio/corridas/en_vivo")  # audios de cada conversación; carpeta sin versionar
RESULTS_DIR = Path("results/en_vivo")
NOTE = "conversación en vivo"
LOADING_MESSAGE = "Los modelos todavía se están cargando; consulta /health hasta que ready sea true."
TURN_INPUT_MESSAGE = 'Un turno lleva o bien "audio" (la ruta de un archivo) o bien "text".'

log = logging.getLogger(__name__)


class RequestError(Exception):
    """Una petición que no se puede atender; se contesta con ``status`` y el mensaje."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status


@dataclass(frozen=True)
class StoreFiles:
    db_path: Path
    seed_path: Path  # la tienda inicial, a la que se vuelve con ``restore``


def turn_input(request: dict[str, Any]) -> tuple[Path | None, str | None]:
    """El audio o el texto de un turno; exactamente uno de los dos."""
    audio, text = request.get("audio"), request.get("text")
    if (audio is None) == (text is None) or not isinstance(audio or text, str):
        raise RequestError(400, TURN_INPUT_MESSAGE)
    if text is not None and not text.strip():
        raise RequestError(400, 'El campo "text" está vacío.')
    if audio is not None and not Path(audio).is_file():
        raise RequestError(400, f"No existe el archivo de audio: {audio}")
    return (Path(audio), None) if audio is not None else (None, text)


def brief(operation: dict[str, Any]) -> dict[str, Any]:
    """Una operación del turno, con su resultado resumido en una línea."""
    summary = " ".join(str(operation["summary"]).split())
    return {"tool": operation["tool"], "args": operation["args"], "ok": operation["ok"], "summary": summary[:SUMMARY_CHARS]}


class LiveChat:
    """Los modelos ya cargados y la conversación en curso; atiende un turno a la vez."""

    def __init__(
        self,
        graph: Any,
        asr: SpeechRecognizer | None,
        tts: SpeechSynthesizer | None,
        shop: StoreFiles,
        user: str,
        setup: dict[str, Any],
    ) -> None:
        self.graph, self.asr, self.tts = graph, asr, tts
        self.shop, self.user = shop, user
        self.setup = setup  # con qué se conversa: nota, modelos, voz, carga y memoria
        self.lock = threading.Lock()  # los modelos comparten la GPU
        self.pipeline, self.started = self._open()

    def _open(self) -> tuple[VoicePipeline, str]:
        """Una conversación nueva, en otro hilo y con sus propias carpetas."""
        thread = f"vivo-{uuid.uuid4().hex[:8]}"
        session = ShoppingSession(self.graph, thread, self.user)
        pipeline = VoicePipeline(session, self.asr, self.tts, (AUDIO_DIR / thread).resolve())
        return pipeline, datetime.now().isoformat(timespec="seconds")

    @property
    def thread(self) -> str:
        return self.pipeline.session.thread_id

    def health(self) -> dict[str, Any]:
        load = self.setup["load"]
        seconds = {key.removesuffix("_seconds"): value for key, value in load.items() if key.endswith("_seconds")}
        voice = voice_label(self.setup["voice"])
        return {"ready": True, "load": seconds, "vram_mib": process_vram_mib(), "thread": self.thread, "voice": voice}

    def turn(self, request: dict[str, Any]) -> dict[str, Any]:
        audio, text = turn_input(request)
        with self.lock:
            made = self.pipeline.run_turn(audio, text=text)
            self._save()
            return self._reply(made)

    def reset(self, request: dict[str, Any]) -> dict[str, Any]:
        restored = request.get("restore", False)
        if not isinstance(restored, bool):
            raise RequestError(400, 'El campo "restore" es true o false.')
        with self.lock:
            if restored:
                restore(self.shop.seed_path, self.shop.db_path)
            self.pipeline, self.started = self._open()
        return {"thread": self.thread, "restored": restored}

    def _reply(self, turn: VoiceTurn) -> dict[str, Any]:
        folder = self.pipeline.out_dir
        return {
            "turn": turn.turn,
            "heard": turn.agent_input,
            "response": turn.response,
            "spoken": turn.spoken_text,
            "audio": str(folder / turn.output_audio) if folder and turn.output_audio else None,
            "operations": [brief(operation) for operation in turn.operations],
            "awaiting_confirmation": turn.awaiting_confirmation,
            "seconds": turn.timings,
        }

    def _save(self) -> None:
        """La transcripción de la conversación hasta ahora, como la de una corrida por voz."""
        self.setup["load"]["vram_mib"]["after_run"] = process_vram_mib()
        record = {"date": self.started, **self.setup, **voice_chat.conversation_record(self.pipeline)}
        record.update(store=store_snapshot(self.shop.db_path, self.shop.seed_path), text_run=None)
        folder = RESULTS_DIR / self.thread
        folder.mkdir(parents=True, exist_ok=True)
        (folder / voice_chat.RECORD_FILE).write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
        (folder / voice_chat.TRANSCRIPT_FILE).write_text(to_markdown(record), encoding="utf-8")


@dataclass
class Service:
    """Lo que atiende el servidor; ``chat`` es ``None`` mientras cargan los modelos."""

    chat: LiveChat | None = None

    def health(self) -> dict[str, Any]:
        if self.chat is not None:
            return self.chat.health()
        return {"ready": False, "load": {}, "vram_mib": process_vram_mib(), "thread": None, "voice": None}

    def post(self, path: str, request: dict[str, Any]) -> dict[str, Any]:
        if path not in ("/turn", "/reset"):
            raise RequestError(404, f"No existe la ruta POST {path}; están /turn y /reset.")
        if self.chat is None:
            raise RequestError(503, LOADING_MESSAGE)
        return self.chat.turn(request) if path == "/turn" else self.chat.reset(request)


class Handler(BaseHTTPRequestHandler):
    """Rutas del servidor. Toda respuesta es JSON, también los errores."""

    def __init__(self, service: Service, *args: Any, **kwargs: Any) -> None:
        self.service = service
        super().__init__(*args, **kwargs)

    def do_GET(self) -> None:
        if self.path == "/health":
            self._send(200, self.service.health())
        else:
            self._send(404, {"error": f"No existe la ruta GET {self.path}; está /health."})

    def do_POST(self) -> None:
        try:
            status, body = 200, self.service.post(self.path, self._request())
        except RequestError as error:
            status, body = error.status, {"error": str(error)}
        except Exception as error:  # un turno que falla no tumba el servidor
            log.exception("Fallo al atender %s", self.path)
            status, body = 500, {"error": f"{type(error).__name__}: {error}"}
        self._send(status, body)

    def _request(self) -> dict[str, Any]:
        """El cuerpo de la petición: un objeto JSON, o nada."""
        raw = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        try:
            request = json.loads(raw.decode("utf-8")) if raw.strip() else {}
        except ValueError as error:
            raise RequestError(400, f"El cuerpo no es JSON en UTF-8: {error}") from error
        if not isinstance(request, dict):
            raise RequestError(400, "El cuerpo tiene que ser un objeto JSON.")
        return request

    def _send(self, status: int, body: dict[str, Any]) -> None:
        payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: Any) -> None:
        log.info("%s %s", self.address_string(), format % args)


def serve(service: Service, port: int) -> ThreadingHTTPServer:
    """Arranca el servidor en un hilo aparte y lo devuelve; se para con ``shutdown``."""
    server = ThreadingHTTPServer((HOST, port), partial(Handler, service))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Servidor local para conversar por voz con el agente, turno a turno.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--reference", type=Path, default=None, help="grabación de referencia para la voz del agente")
    parser.add_argument("--speaker", default=None, help="hablante incluido en XTTS-v2 (solo para pruebas)")
    parser.add_argument("--restore", action="store_true", help="devuelve la tienda a su estado inicial antes de empezar")
    parser.add_argument("--user", default="anonimo")
    parser.add_argument("--n-ctx", type=int, default=8192)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--db", type=Path, default=None)
    parser.add_argument(
        "--volatile-memory", action="store_true",
        help="no usa Postgres: los checkpoints y el Store se pierden al terminar",
    )
    parser.set_defaults(no_tts=False)  # lo que ``voice.chat`` permite y aquí no tiene sentido
    return parser.parse_args()


def wait_until_stopped() -> None:
    """Espera a Ctrl+C o a ``kill``; con los dos se sale cerrando la memoria."""
    signal.signal(signal.SIGTERM, signal.default_int_handler)
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        print("[servidor detenido]", file=sys.stderr)


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    check_memory(args.volatile_memory)
    shop = StoreFiles(args.db or args.data / "store.sqlite", args.data / "store_seed.sqlite")
    if args.restore:
        restore(shop.seed_path, shop.db_path)
    service = Service()
    server = serve(service, args.port)  # antes de cargar: /health contesta desde el principio
    print(f"[escuchando en http://{HOST}:{args.port}; cargando modelos…]", file=sys.stderr)

    loaded = voice_chat.load_everything(args, voice_chat.AUDIO)
    with open_memory(volatile=args.volatile_memory) as memory:
        graph = build_graph(loaded.models.llm, loaded.models.search, shop.db_path, memory.checkpointer, memory.store)
        setup = {"note": NOTE, "mode": voice_chat.AUDIO, **voice_chat.load_record(loaded), "memory_backend": memory.backend}
        service.chat = LiveChat(graph, loaded.asr, loaded.tts, shop, args.user, setup)
        print(f"[listo en {loaded.seconds:.1f} s; VRAM del proceso: {loaded.vram_mib['loaded']} MiB; hilo {service.chat.thread}]", file=sys.stderr)
        wait_until_stopped()
        server.shutdown()


if __name__ == "__main__":
    main()
