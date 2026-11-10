"""Escenarios de evaluación: formato, comprobaciones, violaciones, ejecutor e informe.

Sin GPU ni modelos: el agente corre con el LLM guionizado y, por voz, con un ASR
y un TTS simulados.
"""

import copy
import json
import shutil

import numpy as np
import pytest

from shopping_agent.agent import tools
from shopping_agent.eval import scenario_format as fmt
from shopping_agent.eval import scenario_violations as violations
from shopping_agent.eval import scenarios as command
from shopping_agent.eval.scenario_checks import View, match_lines, resolve, run_check
from shopping_agent.eval.scenario_report import before_after, compare_with_text, failed_checks, ficha, run_summary, summarize, to_markdown
from shopping_agent.eval.scenario_runner import AUDIO, TEXT, AudioInputs, Bench, ScenarioRun
from shopping_agent.voice.audio import write_wav
from test_agent import Shop, call, say
from test_voice_pipeline import FakeASR, FakeTTS

REQUIRED_VOICE_KINDS = {
    "compra_confirmada",
    "pedido_ambiguo",
    "cambio_cantidad",
    "sin_existencias",
    "correccion_transcripcion",
    "cambio_stock_confirmacion_repetida",
}


def check(name, **params):
    return {"check": name, **params}


def line(product, quantity):
    return {"product": product, "quantity": quantity}


PURCHASE = {
    "id": "compra",
    "title": "Compra de prueba",
    "kind": "compra_confirmada",
    "voice": True,
    "description": "Busca, añade dos, cierra, confirma y repite el sí.",
    "steps": [
        {"say": "Busco auriculares bluetooth y tengo 50 euros", "terms": ["auriculares bluetooth"],
         "expect": [check("budget", cents=5000), check("cart", empty=True)]},
        {"remember": {"elegido": "candidate:1"}},
        {"event": "set_offer", "product": "@elegido", "price_cents": 1000, "stock": 6},
        {"say": "Añade dos del primero", "expect": [check("cart", lines=[line("@elegido", 2)])]},
        {"say": "Ciérralo", "expect": [check("awaiting_confirmation", value=True), check("orders", count=0)]},
        {"say": "Sí", "expect": [check("orders", count=1)]},
        {"say": "Sí", "expect": [check("orders", count=1)]},
    ],
    "expect": [
        check("order", lines=[line("@elegido", 2)], total_cents=2000),
        check("stock", product="@elegido", equals=4),
        check("cart", empty=True),
    ],
}


def on_known(tool, position=0, **args):
    """Decisión guionizada sobre el producto que ocupa esa posición entre los que el LLM conoce."""

    def decide(messages, schema):
        option = next(option for option in schema["anyOf"] if option["properties"]["herramienta"]["const"] == tool)
        return call(tool, product_id=option["properties"]["product_id"]["enum"][position], **args)

    return decide


def purchase_script(quantity=2):
    return [
        call(tools.SET_BUDGET, importe_eur=50),
        call(tools.SEARCH, consulta="auriculares bluetooth"),
        say("Tengo varios modelos."),
        on_known(tools.ADD, cantidad=quantity),
        say("Añadidos."),
        call(tools.QUOTE),
    ]


@pytest.fixture
def shop(tmp_path):
    return Shop(tmp_path)


def bench_for(shop, tmp_path, asr=None, tts=None):
    """El banco de pruebas de una corrida: la tienda del guion es también la semilla."""
    seed = tmp_path / "seed.sqlite"
    if not seed.exists():
        shutil.copyfile(shop.db_path, seed)
    return Bench(shop.graph, shop.search, shop.db_path, seed, asr, tts)


def run(shop, tmp_path, raw, script, run_id="corrida"):
    shop.llm.extend(script)
    return ScenarioRun(fmt.parse_scenario(raw), bench_for(shop, tmp_path), run_id).run()


# --- Formato --------------------------------------------------------------------------


def test_evaluation_scenarios_cover_the_assignment():
    scenarios = fmt.load_scenarios()
    voice = [scenario for scenario in scenarios if scenario.voice]
    assert len(scenarios) == 20 and len({scenario.kind for scenario in scenarios}) == 20
    assert {scenario.kind for scenario in voice} == REQUIRED_VOICE_KINDS
    assert sum(len(scenario.says) > 1 for scenario in voice) >= 3
    assert all(scenario.expect for scenario in scenarios)


def test_reserve_scenarios_are_well_formed_and_kept_apart():
    """Los de reserva no entran en las corridas normales: están en otra carpeta."""
    reserve = fmt.load_scenarios(command.RESERVE_DIR)
    assert len(reserve) == 4 and not any(scenario.voice for scenario in reserve)
    assert not {scenario.id for scenario in reserve} & {scenario.id for scenario in fmt.load_scenarios()}


def test_recording_script_matches_the_scenarios():
    written = (fmt.DEFAULT_DIR / command.SCRIPT_FILE).read_text(encoding="utf-8")
    assert written == fmt.recording_script(fmt.load_scenarios(), str(command.RECORDINGS_DIR))
    assert "| `audio/escenarios/01_compra_confirmada/02.wav` | Añade dos de la primera al carrito. |" in written


@pytest.mark.parametrize(
    "change",
    [
        {"expect": [check("no_existe")]},
        {"expect": [check("orders", cuenta=1)]},
        {"steps": [{"decir": "hola"}]},
        {"steps": [{"event": "set_offer", "product": "@x"}]},
        {"steps": [{"remember": {"x": "candidate:1"}}]},
        {"extra": 1},
    ],
)
def test_malformed_scenarios_are_rejected(change):
    with pytest.raises(fmt.ScenarioError):
        fmt.parse_scenario({**PURCHASE, **change})


# --- Ejecutor -------------------------------------------------------------------------


def test_purchase_scenario_passes_and_keeps_everything(shop, tmp_path):
    record = run(shop, tmp_path, PURCHASE, purchase_script())
    assert record["passed"] and not record["violations"] and not record["problems"]
    assert record["input"] == TEXT and len(record["threads"]) == 1
    assert [step["kind"] for step in record["steps"]] == ["turn", "remember", "event", "turn", "turn", "turn", "turn"]
    chosen = record["names"]["elegido"]
    store = record["final"]["snapshot"]["store"]
    assert [(item["product_id"], item["quantity"]) for item in store["order_items"]] == [(chosen, 2)]
    assert len(store["orders"]) == 1  # el segundo sí no duplicó el pedido
    turn = record["steps"][3]
    assert turn["operations"][0]["tool"] == tools.ADD and set(turn["timings"]) >= {"llm", "retrieval", "tools", "total"}
    assert turn["before"]["offers"][chosen] == {"price_cents": 1000, "stock": 6}
    json.dumps(record)  # se puede guardar tal cual
    text = ficha(record)
    assert "Veredicto: **correcto**" in text and "Suceso externo" in text and "Estado final de la tienda" in text


def test_wrong_quantity_is_reported_as_a_failure(shop, tmp_path):
    record = run(shop, tmp_path, PURCHASE, purchase_script(quantity=3))
    assert not record["passed"] and not record["violations"]
    assert [(failed["turn"], failed["check"]) for failed in failed_checks(record)] == [(2, "cart"), ("final", "order"), ("final", "stock")]
    assert "Veredicto: **fallo**" in ficha(record)


def test_every_scenario_starts_from_the_seed_with_fresh_memory(shop, tmp_path):
    first = run(shop, tmp_path, PURCHASE, purchase_script(), run_id="a")
    second = run(shop, tmp_path, PURCHASE, purchase_script(), run_id="b")
    assert first["passed"] and second["passed"]  # el pedido de la primera no queda en la segunda
    assert first["threads"] != second["threads"] and first["user_id"] != second["user_id"]


def test_stock_change_between_quote_and_confirmation(shop, tmp_path):
    raw = copy.deepcopy(PURCHASE)
    raw["steps"][5:] = [
        {"event": "set_offer", "product": "@elegido", "stock": 1},
        {"say": "Sí", "expect": [
            check("orders", count=0), check("rejected", code="stock_insuficiente"),
            check("cart", lines=[line("@elegido", 2)]), check("stock", product="@elegido", equals=1),
        ]},
    ]
    raw["expect"] = [check("orders", count=0)]
    record = run(shop, tmp_path, raw, purchase_script())
    assert record["passed"] and not record["violations"]


def test_unresolved_reference_fails_the_scenario(shop, tmp_path):
    raw = {**PURCHASE, "steps": [{"say": "Hola"}, {"remember": {"elegido": "candidate:1"}}], "expect": []}
    record = run(shop, tmp_path, raw, [say("Hola, ¿qué buscas?")])
    assert not record["passed"] and "candidate:1" in record["problems"][0]


def test_an_error_in_the_agent_is_a_result(shop, tmp_path):
    def broken(messages, schema):
        raise RuntimeError("sin memoria en la GPU")

    record = run(shop, tmp_path, {**PURCHASE, "steps": [{"say": "Hola"}], "expect": []}, [broken])
    assert not record["passed"] and "sin memoria en la GPU" in record["problems"][0]
    assert record["steps"][-1]["kind"] == "error"


def test_new_conversation_keeps_the_user_and_changes_the_thread(shop, tmp_path):
    raw = {
        **PURCHASE,
        "steps": [
            {"say": "Recuerda que prefiero el azul", "expect": [check("preference", contains="azul")]},
            {"new_conversation": True},
            {"say": "¿Qué color prefiero?", "expect": [check("preference", contains="AZUL"), check("response_contains", text="azul")]},
        ],
        "expect": [check("orders", count=0)],
    }
    script = [call(tools.SAVE_PREFERENCE, preferencia="color azul"), say("Anotado."), say("Prefieres el azul.")]
    record = run(shop, tmp_path, raw, script)
    assert record["passed"] and len(record["threads"]) == 2


def test_voice_run_goes_through_asr_and_tts(shop, tmp_path):
    scenario = fmt.parse_scenario(PURCHASE)
    heard = [say.text for say in scenario.says]
    heard[1] = "Añade dos del primero."  # el ASR puntúa a su manera
    files = [write_wav(tmp_path / "entradas" / f"{n:02d}.wav", np.zeros(800, dtype=np.float32), 16000) for n in range(1, 6)]
    bench = bench_for(shop, tmp_path, FakeASR(heard), FakeTTS())
    shop.llm.extend(purchase_script())
    out = tmp_path / "audio"
    record = ScenarioRun(scenario, bench, "voz", AudioInputs("sintéticos de prueba", files), out).run()
    assert record["passed"] and record["input"] == AUDIO and record["audio_source"] == "sintéticos de prueba"
    turn = record["steps"][3]
    assert turn["transcript"] == "Añade dos del primero." and turn["expected_text"] == "Añade dos del primero"
    assert (out / turn["input_audio"]).is_file() and (out / turn["output_audio"]).is_file()
    assert turn["timings"]["asr"] > 0 and turn["timings"]["tts"] > 0


# --- Comprobaciones -------------------------------------------------------------------


def snapshot(orders=(), order_items=(), cart_items=(), offers=None, candidates=(), budget=None, quote=None, awaiting=False):
    state = {"budget_cents": budget, "preferences": [], "candidates": list(candidates), "quote": quote, "awaiting_confirmation": awaiting}
    store = {"orders": list(orders), "order_items": list(order_items), "cart_items": list(cart_items), "inventory_changes": []}
    return {"cart_id": "hilo", "state": state, "store": store, "offers": offers or {}}


def candidate(product_id, brand, price_cents, stock):
    return {"product_id": product_id, "title": f"Producto {product_id}", "brand": brand, "price_cents": price_cents, "stock": stock}


def view(snap, response="", names=None, catalog=""):
    return View(snap, {"response": response, "operations": []}, names or {}, lambda product_id: catalog)


def test_references_resolve_against_the_snapshot():
    snap = snapshot(candidates=[candidate("A", None, 100, 1)], cart_items=[{"cart_id": "hilo", "product_id": "B", "quantity": 1}])
    seen = view(snap, names={"x": "C"})
    assert [resolve(ref, seen) for ref in ("candidate:1", "cart:1", "@x")] == ["A", "B", "C"]
    assert [resolve(ref, seen) for ref in ("candidate:2", "cart:0", "@y", "otro:1")] == [None] * 4


def test_lines_match_exactly_in_any_order():
    seen = view(snapshot(), names={"a": "A"})
    actual = [{"product_id": "B", "quantity": 1}, {"product_id": "A", "quantity": 2}]
    assert match_lines([line("@a", 2), {"not": "@a", "quantity": 1}], actual, seen)
    assert not match_lines([line("@a", 2)], actual, seen)  # sobra una línea
    assert not match_lines([line("@a", 1), {"not": "@a", "quantity": 1}], actual, seen)  # otra cantidad
    assert not match_lines([{"not": "@nadie", "quantity": 1}], actual[:1], seen)  # referencia sin resolver


def test_carts_of_other_conversations_do_not_count():
    snap = snapshot(cart_items=[{"cart_id": "otro-hilo", "product_id": "A", "quantity": 1}])
    assert run_check("cart", {"empty": True}, view(snap))["ok"]


@pytest.mark.parametrize(
    ("response", "catalog", "ok"),
    [
        ("El catálogo no indica la valoración de los clientes.", "Sartén de 24 cm", True),
        ("No tengo ese dato.", "Sartén de 24 cm", True),
        ("Tiene muy buena valoración.", "Sartén de 24 cm", False),
        ("Tiene 4,5 estrellas.", "Sartén con valoración de 4,5 estrellas", True),
        ("No consta.", "Sartén con valoración de 4,5 estrellas", False),
    ],
)
def test_unknown_attribute_must_be_declared_unknown(response, catalog, ok):
    seen = view(snapshot(), response, {"x": "A"}, catalog)
    assert run_check("declares_unknown", {"product": "@x", "keywords": ["valoraci", "estrellas"]}, seen)["ok"] is ok


def test_alternative_is_another_candidate_in_stock_cited_by_price_or_brand():
    candidates = [candidate("A", "Acme", 1000, 0), candidate("B", "Borealis", 1250, 4), candidate("C", "Cumbre", 900, 0)]
    offers = {item["product_id"]: {"price_cents": item["price_cents"], "stock": item["stock"]} for item in candidates}
    snap = snapshot(candidates=candidates, offers=offers)

    def offered(response):
        return run_check("offered_alternative", {"instead_of": "@a"}, view(snap, response, {"a": "A"}))["ok"]

    assert offered("Ese está agotado, pero tengo otro por 12,50 euros.")
    assert offered("Está agotado. ¿Te vale el de Borealis?")
    assert not offered("Está agotado. Tengo el de Cumbre por 9 euros.")  # también agotado
    assert not offered("Lo siento, está agotado.")


def test_price_mention_uses_the_store_price():
    snap = snapshot(offers={"A": {"price_cents": 1450, "stock": 3}})
    assert run_check("mentions_price", {"product": "@a"}, view(snap, "Cuesta 14,50 euros.", {"a": "A"}))["ok"]
    assert not run_check("mentions_price", {"product": "@a"}, view(snap, "Cuesta 15 euros.", {"a": "A"}))["ok"]


# --- Violaciones ----------------------------------------------------------------------

ORDER = {"order_id": 1, "quote_id": "q", "total_cents": 2000}
ITEM = {"order_id": 1, "product_id": "A", "quantity": 2, "unit_price_cents": 1000}
QUOTE = {"quote_id": "q", "items": [{"product_id": "A", "quantity": 2}]}
CART = [{"cart_id": "hilo", "product_id": "A", "quantity": 2}]


def turn(before, after, operations=()):
    return {"turn": 1, "before": before, "after": after, "operations": list(operations)}


def bought(**changes):
    """Un turno en el que se confirma un pedido de 2 × A; ``changes`` altera el antes o el después."""
    before = {"cart_items": CART, "offers": {"A": {"price_cents": 1000, "stock": 5}}, "quote": QUOTE, "awaiting": True}
    after = {"orders": [ORDER], "order_items": [ITEM], "offers": {"A": {"price_cents": 1000, "stock": 3}}}
    for key, value in changes.items():
        side, _, field = key.partition("_")
        (before if side == "before" else after)[field] = value
    return turn(snapshot(**before), snapshot(**after))


def kinds(turns):
    return sorted({found["kind"] for found in violations.find_violations(turns)})


def test_a_clean_purchase_has_no_violations():
    assert kinds([bought()]) == []


def test_each_kind_of_violation_is_detected():
    assert kinds([bought(before_awaiting=False)]) == [violations.DUPLICATE]
    assert kinds([bought(before_budget=1500)]) == [violations.BUDGET]
    assert kinds([bought(before_quote={"quote_id": "q", "items": [{"product_id": "A", "quantity": 1}]})]) == [violations.QUANTITY]
    assert kinds([bought(after_cart_items=CART)]) == [violations.PARTIAL]
    assert kinds([bought(after_offers={"A": {"price_cents": 1000, "stock": 5}})]) == [violations.PARTIAL]
    low_stock = bought(before_offers={"A": {"price_cents": 1000, "stock": 1}}, after_offers={"A": {"price_cents": 1000, "stock": -1}})
    assert kinds([low_stock]) == [violations.STOCK]


def test_rejected_confirmation_must_not_change_the_store():
    failed = [{"tool": violations.CONFIRM_TOOL, "ok": False, "issues": []}]
    same = snapshot(cart_items=CART, awaiting=True)
    assert kinds([turn(same, snapshot(cart_items=CART), failed)]) == []
    assert kinds([turn(same, snapshot(), failed)]) == [violations.PARTIAL]


def test_cart_over_budget_after_an_accepted_operation():
    added = [{"tool": "agregar_al_carrito", "ok": True, "issues": []}]
    after = snapshot(cart_items=CART, offers={"A": {"price_cents": 1000, "stock": 5}}, budget=1500)
    assert kinds([turn(snapshot(budget=1500), after, added)]) == [violations.BUDGET]
    assert kinds([turn(snapshot(budget=1500), after)]) == []  # el presupuesto bajó después; cotizar lo rechazará


# --- Informe y comando ----------------------------------------------------------------


def test_summary_counts_passes_violations_and_differences(shop, tmp_path):
    good = run(shop, tmp_path, PURCHASE, purchase_script(), run_id="a")
    bad = run(shop, tmp_path, {**PURCHASE, "id": "otra"}, purchase_script(quantity=3), run_id="b")
    summary = run_summary([good, bad])
    assert (summary["scenarios"], summary["passed"], summary["failed"]) == (2, 1, ["otra"])
    assert summary["turns"] == 10 and set(summary["violations"]) == set(violations.KINDS)
    same = compare_with_text(good, run(shop, tmp_path, PURCHASE, purchase_script(), run_id="c"))
    assert same["same_store"] and not same["asr_changed_words"] and not same["different_operations"]
    assert not compare_with_text(good, bad)["same_store"]


def test_summary_markdown_lists_runs_and_failures(shop, tmp_path):
    info = {
        "date": "2026-11-10", "commit": "abc", "input": TEXT, "audio_sources": {}, "memory_backend": "memoria volátil",
        "models": {"reranker": "sage"}, "voice": {}, "load": {"search_seconds": 1, "llm_seconds": 1, "total_seconds": 2},
    }
    records = [run(shop, tmp_path, PURCHASE, purchase_script(quantity=3))]
    text = to_markdown(summarize([{"name": "texto", "info": info, "records": records, "voice_metrics": None}]))
    assert "| `texto` | texto | sage | 1 | 0 | 0.0 % |" in text
    assert "[compra](texto/compra.md)" in text and "turno 2: `cart`" in text


def test_recordings_are_preferred_over_synthetic_audio(tmp_path):
    scenario = fmt.parse_scenario(PURCHASE)
    recordings, synthetic = tmp_path / "escenarios", tmp_path / "sinteticos"
    for number in range(1, 6):
        write_wav(synthetic / "compra" / f"{number:02d}.wav", np.zeros(8, dtype=np.float32), 16000)
    (synthetic / "compra" / command.SOURCE_FILE).write_text('{"speaker": "Luis Moray"}', encoding="utf-8")
    write_wav(recordings / "compra" / "01.wav", np.zeros(8, dtype=np.float32), 16000)  # grabación a medias
    found = command.audio_inputs(scenario, recordings, synthetic)
    assert "Luis Moray" in found.source and "no es la voz del usuario" in found.source and len(found.files) == 5
    for number in range(2, 6):
        write_wav(recordings / "compra" / f"{number:02d}.wav", np.zeros(8, dtype=np.float32), 16000)
    assert command.audio_inputs(scenario, recordings, synthetic).source == command.USER_RECORDING
    with pytest.raises(SystemExit):
        command.audio_inputs(scenario, tmp_path / "nada", tmp_path / "nada")


def test_before_and_after_lists_what_was_fixed_and_what_broke():
    def runs(**verdicts):
        return {"runs": {"texto": {"verdicts": verdicts}}}

    current = runs(a=True, b=True, c=False, nuevo=True)
    current["runs"]["solo_ahora"] = {"verdicts": {"a": True}}
    rows = before_after(current, runs(a=True, b=False, c=True))
    assert len(rows) == 1  # solo las corridas que están en los dos
    row = rows[0]
    assert (row["before"], row["after"], row["scenarios"]) == (2, 2, 3)
    assert row["fixed"] == ["b"] and row["regressions"] == ["c"]
    text = to_markdown({"runs": {}, "audio_vs_correct_text": [], "baseline": "base", "before_after": rows})
    assert "| `texto` | 2 de 3 | 2 de 3 | b | c |" in text and "| `b` | ✘ → ✔ |" in text
