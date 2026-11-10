import pytest

from shopping_agent.voice.speech_text import (
    euros_to_words,
    number_to_words,
    split_for_tts,
    spoken_title,
    to_speech,
)


@pytest.mark.parametrize(
    "number, words",
    [
        (0, "cero"), (1, "uno"), (16, "dieciséis"), (21, "veintiuno"), (22, "veintidós"), (30, "treinta"),
        (45, "cuarenta y cinco"), (100, "cien"), (101, "ciento uno"), (555, "quinientos cincuenta y cinco"),
        (1000, "mil"), (1234, "mil doscientos treinta y cuatro"), (21000, "veintiún mil"),
        (1000000, "un millón"), (2500000, "dos millones quinientos mil"), (-3, "menos tres"),
    ],
)
def test_number_to_words(number, words):
    assert number_to_words(number) == words


def test_number_agrees_with_the_noun():
    assert number_to_words(1, "un") == "un"
    assert number_to_words(21, "un") == "veintiún"
    assert number_to_words(31, "una") == "treinta y una"
    assert number_to_words(200, "una") == "doscientas"
    assert number_to_words(21000, "una") == "veintiuna mil"


@pytest.mark.parametrize(
    "euros, cents, words",
    [
        (14, 55, "catorce euros con cincuenta y cinco céntimos"),
        (30, 0, "treinta euros"),
        (1, 0, "un euro"),
        (1, 1, "un euro con un céntimo"),
        (0, 50, "cincuenta céntimos"),
        (21, 0, "veintiún euros"),
        (5, 3, "cinco euros con tres céntimos"),
    ],
)
def test_euros_to_words(euros, cents, words):
    assert euros_to_words(euros, cents) == words


def test_amounts_are_spoken_in_words_whatever_the_notation():
    assert to_speech("Total: 7,74 €.") == "Total: siete euros con setenta y cuatro céntimos."
    assert to_speech("Cuesta 4,85 euros") == "Cuesta cuatro euros con ochenta y cinco céntimos"
    assert to_speech("un presupuesto de 60,00 €") == "Un presupuesto de sesenta euros"
    assert to_speech("vale 1.234,5 €") == "Vale mil doscientos treinta y cuatro euros con cincuenta céntimos"
    assert to_speech("son 60€") == "Son sesenta euros"


def test_quantities_agree_in_gender():
    assert to_speech("Quedan 9 unidades.") == "Quedan nueve unidades."
    assert to_speech("En el carrito hay 1 unidad") == "En el carrito hay una unidad"
    assert to_speech("21 unidades y 21 euros") == "Veintiuna unidades y veintiún euros"
    assert to_speech("Pedido número 1 registrado") == "Pedido número uno registrado"
    assert to_speech("tiene 42 horas de reproducción") == "Tiene cuarenta y dos horas de reproducción"


def test_identifiers_are_not_read_aloud():
    spoken = to_speech("El producto B08K91F1M4 (Sony WH-1000XM4) está disponible.")
    assert "B08" not in spoken and "1000" not in spoken and "(" not in spoken
    assert spoken == "El producto, Sony, está disponible."


def test_catalog_titles_are_shortened():
    assert spoken_title("De'longhi Dedica - Cafetera de Bomba de Acero Inoxidable para Café…") == "De'longhi Dedica"
    assert (
        spoken_title("Princess 249412 Máquina de café para Espresso italiano, Compatible…")
        == "Princess Máquina de café para Espresso italiano"
    )
    spoken = to_speech("1 unidad de «LYCHL Auriculares Inalambricos Deportivos, Auriculares Bluetooth 5.0…» a 4,85 € cada una")
    assert spoken == "Una unidad de LYCHL Auriculares Inalambricos Deportivos a cuatro euros con ochenta y cinco céntimos cada una"


def test_units_decimals_and_symbols():
    assert to_speech("batería de 5000mAh y 250 g") == "Batería de cinco mil miliamperios hora y doscientos cincuenta gramos"
    assert to_speech("Bluetooth 5.0") == "Bluetooth cinco punto cero"
    assert to_speech("pantalla de 6,5 pulgadas") == "Pantalla de seis coma cinco pulgadas"
    assert to_speech("descuento del 15 %") == "Descuento del quince por ciento"
    assert to_speech("2 x 3 cajas") == "Dos por tres cajas"
    assert to_speech("dura 1 h") == "Dura una hora"


def test_no_digits_or_symbols_are_left_in_a_real_answer():
    answer = (
        "Te repito el pedido antes de registrarlo: 1 unidad de «De'longhi Dedica - Cafetera de Bomba de Acero "
        "Inoxidable para Café…» a 5,03 € cada una, 5,03 €; 1 unidad de «Princess 249412 Máquina de café para "
        "Espresso italiano, Compatible…» a 7,74 € cada una, 7,74 €. Total: 12,77 €. Tu presupuesto es de 30,00 € "
        "y te quedan 17,23 €. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar."
    )
    spoken = to_speech(answer)
    assert not any(char.isdigit() for char in spoken)
    assert not set("€«»…;*`") & set(spoken)
    assert "De'longhi Dedica" in spoken  # el apóstrofo de la marca se conserva
    assert spoken.endswith("¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar.")
    assert "Total: doce euros con setenta y siete céntimos." in spoken


def test_text_without_figures_is_left_alone():
    assert to_speech("¿Qué tipo de regalo tienes en mente?") == "¿Qué tipo de regalo tienes en mente?"
    assert to_speech("") == ""


def test_split_for_tts_respects_the_limit_and_loses_nothing():
    text = to_speech(
        "Hecho, añadidas dos unidades. El total del carrito es 9,70 €. En el carrito hay 2 unidades de «LYCHL "
        "Auriculares Inalambricos Deportivos, Auriculares Bluetooth 5.0…» a 4,85 € cada una, 9,70 €. Total: 9,70 €. "
        "Tu presupuesto es de 60,00 € y te quedan 50,30 €."
    )
    chunks = split_for_tts(text, max_chars=120)
    assert all(len(chunk) <= 120 for chunk in chunks)
    assert " ".join(chunks) == text
    assert split_for_tts("Sí.") == ["Sí."]
    assert split_for_tts("") == []
    long_word_run = " ".join(["palabra"] * 60)
    assert all(len(chunk) <= 50 for chunk in split_for_tts(long_word_run, max_chars=50))
