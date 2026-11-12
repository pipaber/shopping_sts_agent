"""El servidor de conversación en vivo, con ASR, TTS y LLM simulados: sin GPU ni modelos."""

import json
import shutil
import threading
import time
import urllib.error
import urllib.request

import numpy as np
import pytest

from shopping_agent.agent import tools
from shopping_agent.voice import live
from shopping_agent.voice.audio import write_wav
from shopping_agent.voice.pipeline import NOT_HEARD, STAGES, TOTAL
from test_agent import Shop, call, say
from test_voice_pipeline import FakeASR, FakeTTS, purchase_script

SETUP = {
    "note": live.NOTE, "mode": "audio",
    "models": {"llm": "guion", "asr": "simulado", "tts": "simulado", "embeddings": "ninguno"},
    "voice": {"reference": None, "speaker": "Prueba", "speed": 1.1},
    "load": {"search_seconds": 1.0, "llm_seconds": 2.0, "asr_seconds": 3.0, "tts_seconds": 4.0, "total_seconds": 10.0,
             "vram_mib": {"loaded": 100}},
    "memory_backend": "memoria",
}


class Client:
    """Peticiones al servidor; devuelve el código y el JSON, también en los errores."""

    def __init__(self, port):
        self.base = f"http://{live.HOST}:{port}"

    def send(self, path, body=None, raw=None):
        """Sin ``body`` ni ``raw`` es un GET; con cualquiera de los dos, un POST."""
        data = raw if raw is not None else (json.dumps(body).encode("utf-8") if body is not None else None)
        request = urllib.request.Request(self.base + path, data=data, method="GET" if data is None else "POST")
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            return error.code, json.loads(error.read().decode("utf-8"))


class Running:
    """El servidor con una tienda de prueba y los modelos simulados."""

    def __init__(self, folder, transcripts=()):
        self.shop = Shop(folder)
        self.files = live.StoreFiles(self.shop.db_path, folder / "store_seed.sqlite")
        shutil.copyfile(self.files.db_path, self.files.seed_path)
        self.asr, self.tts = FakeASR(transcripts), FakeTTS()
        self.service = live.Service(live.LiveChat(self.shop.graph, self.asr, self.tts, self.files, "ana", dict(SETUP)))
        self.server = live.serve(self.service, 0)
        self.client = Client(self.server.server_address[1])

    def turn(self, **body):
        return self.client.send("/turn", body)


@pytest.fixture
def running(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # las carpetas de la conversación se crean aquí
    server = Running(tmp_path)
    yield server
    server.server.shutdown()


@pytest.fixture
def recording(tmp_path):
    return str(write_wav(tmp_path / "turno.wav", np.zeros(16000, dtype=np.float32), 16000))


def test_health_answers_while_the_models_load():
    server = live.serve(live.Service(), 0)
    client = Client(server.server_address[1])
    try:
        status, health = client.send("/health")
        assert status == 200 and health["ready"] is False and health["thread"] is None and health["load"] == {}
        status, body = client.send("/turn", {"text": "hola"})
        assert status == 503 and "cargando" in body["error"]
        assert client.send("/reset", {})[0] == 503
    finally:
        server.shutdown()


def test_health_says_what_is_loaded(running):
    status, health = running.client.send("/health")
    assert status == 200 and health["ready"] is True
    assert health["load"] == {"search": 1.0, "llm": 2.0, "asr": 3.0, "tts": 4.0, "total": 10.0}
    assert health["thread"].startswith("vivo-") and "Prueba" in health["voice"] and "1,10" in health["voice"]
    assert "vram_mib" in health


def test_turn_by_text_follows_the_contract(running, tmp_path):
    running.shop.llm.extend(purchase_script()[:3])
    status, turn = running.turn(text="Busco auriculares bluetooth y tengo 50 euros")

    assert status == 200 and turn["turn"] == 1
    assert turn["heard"] == "Busco auriculares bluetooth y tengo 50 euros"
    assert "20,00 €" in turn["response"] and "veinte euros" in turn["spoken"]
    assert [(operation["tool"], operation["ok"]) for operation in turn["operations"]] == [(tools.SET_BUDGET, True), (tools.SEARCH, True)]
    assert set(turn["operations"][0]) == {"tool", "args", "ok", "summary"}
    assert turn["awaiting_confirmation"] is False
    assert set(turn["seconds"]) == {*STAGES, TOTAL} and turn["seconds"]["asr"] == 0.0 and turn["seconds"]["tts"] == 0.5
    # Lo que deja la conversación: el audio de la respuesta y la transcripción.
    thread = running.service.chat.thread
    assert turn["audio"] == str(tmp_path / live.AUDIO_DIR / thread / "respuesta_01.wav")
    assert (tmp_path / live.AUDIO_DIR / thread / "respuesta_01.wav").is_file()
    record = json.loads((tmp_path / live.RESULTS_DIR / thread / "turnos.json").read_text(encoding="utf-8"))
    assert record["thread_id"] == thread and record["note"] == live.NOTE and len(record["turns"]) == 1
    assert "**Usuario (texto):** Busco auriculares" in (tmp_path / live.RESULTS_DIR / thread / "transcripcion.md").read_text(encoding="utf-8")


def test_turn_by_audio_goes_through_the_asr_and_keeps_the_recording(running, recording, tmp_path):
    running.shop.llm.extend(purchase_script()[:3])
    running.asr.transcripts.append("Busco auriculares bluetooth y tengo 50 euros")
    status, turn = running.turn(audio=recording)

    assert status == 200 and turn["heard"] == "Busco auriculares bluetooth y tengo 50 euros"
    assert turn["seconds"]["asr"] == 0.25
    assert [str(heard) for heard in running.asr.heard] == [recording]
    assert (tmp_path / live.AUDIO_DIR / running.service.chat.thread / "entrada_01.wav").is_file()


def test_purchase_is_confirmed_in_a_second_turn(running, recording):
    running.shop.llm.extend(purchase_script())
    running.asr.transcripts.append("Sí, confirmo.")
    for text in ("Busco auriculares bluetooth y tengo 50 euros", "Añade dos de los Sony"):
        running.turn(text=text)
    _, quote = running.turn(text="Quiero cerrar el pedido")
    assert quote["awaiting_confirmation"] is True and running.shop.orders() == 0

    _, confirmed = running.turn(audio=recording)
    assert confirmed["awaiting_confirmation"] is False and confirmed["turn"] == 4
    assert running.shop.orders() == 1 and running.shop.stock("P1") == 8
    assert confirmed["seconds"]["llm"] == 0.0  # confirmar no pasa por el LLM


def test_an_audio_without_speech_never_reaches_the_agent(running, recording):
    running.shop.llm.extend(purchase_script())
    for text in ("Busco auriculares bluetooth y tengo 50 euros", "Añade dos de los Sony", "Quiero cerrar el pedido"):
        running.turn(text=text)
    running.asr.transcripts.extend(["", "  ", "Sí."])

    for _ in range(2):  # el silencio no confirma ni cancela: se pide repetir
        status, unheard = running.turn(audio=recording)
        assert status == 200 and unheard["heard"] == "" and unheard["response"] == NOT_HEARD
        assert unheard["operations"] == [] and unheard["awaiting_confirmation"] is True
        assert unheard["audio"].endswith(".wav") and running.shop.orders() == 0
    assert running.turn(audio=recording)[1]["awaiting_confirmation"] is False and running.shop.orders() == 1
    assert running.shop.llm.remaining == 0  # el LLM no se consultó de más


def test_reset_opens_another_conversation_and_can_restore_the_shop(running):
    running.shop.llm.extend([*purchase_script()[:5], say("Hola.")])
    for text in ("Busco auriculares bluetooth y tengo 50 euros", "Añade dos de los Sony"):
        running.turn(text=text)
    first = running.service.chat.thread
    assert running.shop.sql("SELECT quantity FROM cart_items") == [(2,)]

    status, kept = running.client.send("/reset", raw=b"")  # sin cuerpo: la tienda no se toca
    assert status == 200 and kept["restored"] is False and kept["thread"] not in (first, None)
    assert running.shop.sql("SELECT quantity FROM cart_items") == [(2,)]
    status, fresh = running.client.send("/reset", {"restore": True})
    assert status == 200 and fresh["restored"] is True and fresh["thread"] != kept["thread"]
    assert running.shop.sql("SELECT quantity FROM cart_items") == []
    assert running.client.send("/health")[1]["thread"] == fresh["thread"]
    assert running.turn(text="Hola")[1]["turn"] == 1  # la conversación nueva empieza de cero


@pytest.mark.parametrize(
    ("path", "body", "raw", "status"),
    [
        ("/turn", {}, None, 400),
        ("/turn", {"audio": "a.wav", "text": "hola"}, None, 400),
        ("/turn", {"text": "   "}, None, 400),
        ("/turn", {"audio": 7}, None, 400),
        ("/turn", {"audio": "/no/existe.wav"}, None, 400),
        ("/turn", None, b"{esto no es json", 400),
        ("/turn", None, b"[1, 2]", 400),
        ("/reset", {"restore": "sí"}, None, 400),
        ("/otra", {}, None, 404),
    ],
)
def test_bad_requests_get_a_readable_json_error(running, path, body, raw, status):
    code, answer = running.client.send(path, body, raw)
    assert code == status and isinstance(answer["error"], str) and answer["error"]


def test_unknown_get_route_is_a_json_404(running):
    code, answer = running.client.send("/turn")
    assert code == 404 and "/health" in answer["error"]


def test_a_failing_turn_does_not_bring_the_server_down(running, recording):
    code, answer = running.turn(audio=recording)  # el ASR simulado no tiene nada que devolver
    assert code == 500 and answer["error"].startswith("IndexError")

    running.shop.llm.extend([say("Hola, ¿qué buscas?")])
    code, turn = running.turn(text="Hola")
    assert code == 200 and turn["response"] == "Hola, ¿qué buscas?" and turn["turn"] == 1


def test_turns_are_served_one_at_a_time(running):
    busy, overlaps = threading.Lock(), []
    synthesize = running.tts.synthesize

    def slow(text):
        overlaps.append(not busy.acquire(blocking=False))
        time.sleep(0.2)
        busy.release()
        return synthesize(text)

    running.tts.synthesize = slow
    running.shop.llm.extend([say("Uno."), say("Dos.")])
    requests = [threading.Thread(target=running.turn, kwargs={"text": text}) for text in ("Hola", "Otra vez")]
    for request in requests:
        request.start()
    for request in requests:
        request.join()
    assert overlaps == [False, False] and len(running.service.chat.pipeline.turns) == 2
