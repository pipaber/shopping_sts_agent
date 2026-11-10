"""Texto apto para leer en voz alta.

Las respuestas del agente llevan importes ("7,74 €"), identificadores de producto
y títulos de catálogo largos. Aquí se convierten en algo que un TTS pronuncia
bien: importes y cantidades en palabras, sin identificadores ni símbolos. El
texto original no se toca: es el que queda en la transcripción.
"""

from __future__ import annotations

import re
import unicodedata

# --- Números en palabras --------------------------------------------------------------

_UNITS = (
    "cero uno dos tres cuatro cinco seis siete ocho nueve diez once doce trece catorce quince "
    "dieciséis diecisiete dieciocho diecinueve veinte veintiuno veintidós veintitrés veinticuatro "
    "veinticinco veintiséis veintisiete veintiocho veintinueve"
).split()
_TENS = {3: "treinta", 4: "cuarenta", 5: "cincuenta", 6: "sesenta", 7: "setenta", 8: "ochenta", 9: "noventa"}
_HUNDREDS = {
    1: "ciento", 2: "doscientos", 3: "trescientos", 4: "cuatrocientos", 5: "quinientos",
    6: "seiscientos", 7: "setecientos", 8: "ochocientos", 9: "novecientos",
}
_ONE = {"uno": ("uno", "veintiuno"), "un": ("un", "veintiún"), "una": ("una", "veintiuna")}


def _under_100(number: int, form: str) -> str:
    one, twenty_one = _ONE[form]
    if number == 1:
        return one
    if number == 21:
        return twenty_one
    if number < 30:
        return _UNITS[number]
    tens, unit = divmod(number, 10)
    return _TENS[tens] + (f" y {one if unit == 1 else _UNITS[unit]}" if unit else "")


def _under_1000(number: int, form: str) -> str:
    if number == 100:
        return "cien"
    hundreds, rest = divmod(number, 100)
    parts = []
    if hundreds:
        word = _HUNDREDS[hundreds]
        parts.append(word[:-2] + "as" if form == "una" and hundreds > 1 else word)
    if rest:
        parts.append(_under_100(rest, form))
    return " ".join(parts)


def number_to_words(number: int, form: str = "uno") -> str:
    """Entero en palabras. ``form`` decide cómo acaba un número terminado en uno:
    ``"uno"`` suelto, ``"un"`` ante sustantivo masculino ("veintiún euros") y
    ``"una"`` ante femenino ("una unidad", "doscientas unidades")."""
    if number < 0:
        return "menos " + number_to_words(-number, form)
    if number == 0:
        return "cero"
    if number >= 10**9:  # fuera de lo que aparece en una tienda: se lee cifra a cifra
        return " ".join(_UNITS[int(digit)] for digit in str(number))
    millions, rest = divmod(number, 10**6)
    thousands, units = divmod(rest, 1000)
    parts = []
    if millions:
        parts.append("un millón" if millions == 1 else f"{_under_1000(millions, 'un')} millones")
    if thousands:
        parts.append("mil" if thousands == 1 else f"{_under_1000(thousands, 'una' if form == 'una' else 'un')} mil")
    if units:
        parts.append(_under_1000(units, form))
    return " ".join(parts)


def euros_to_words(euros: int, cents: int = 0) -> str:
    """``(14, 55)`` → "catorce euros con cincuenta y cinco céntimos"."""
    euro_part = "un euro" if euros == 1 else f"{number_to_words(euros, 'un')} euros"
    if not cents:
        return euro_part
    cent_part = "un céntimo" if cents == 1 else f"{number_to_words(cents, 'un')} céntimos"
    return cent_part if euros == 0 else f"{euro_part} con {cent_part}"


# --- Reglas de sustitución ------------------------------------------------------------

_FEMININE = frozenset(
    "unidad unidades hora horas pieza piezas caja cajas botella botellas semana semanas persona personas "
    "taza tazas capsula capsulas pulgada pulgadas pila pilas bolsa bolsas lata latas talla tallas "
    "opcion opciones cafetera cafeteras libra libras vez veces".split()
)
_MASCULINE = frozenset(
    "euro euros centimo centimos producto productos articulo articulos minuto minutos dia dias metro metros "
    "centimetro centimetros milimetro milimetros kilometro kilometros litro litros mililitro mililitros "
    "gramo gramos kilo kilos kilogramo kilogramos vatio vatios voltio voltios ano anos mes meses paquete "
    "paquetes par pares modelo modelos color colores auricular auriculares pedido pedidos resultado "
    "resultados miliamperio miliamperios gigabyte gigabytes megabyte megabytes terabyte terabytes "
    "hercio hercios kilohercio kilohercios".split()
)

_UNIT_WORDS = {
    "mAh": "miliamperios hora", "ml": "mililitros", "cl": "centilitros", "cm": "centímetros", "mm": "milímetros",
    "km": "kilómetros", "kg": "kilos", "mg": "miligramos", "GB": "gigabytes", "MB": "megabytes", "TB": "terabytes",
    "kHz": "kilohercios", "Hz": "hercios", "min": "minutos", "W": "vatios", "V": "voltios", "g": "gramos",
    "l": "litros", "L": "litros", "m": "metros", "h": "horas",
}
_UNIT_SINGULAR = {
    "mililitros": "mililitro", "centilitros": "centilitro", "centímetros": "centímetro", "milímetros": "milímetro",
    "kilómetros": "kilómetro", "kilos": "kilo", "miligramos": "miligramo", "gigabytes": "gigabyte",
    "megabytes": "megabyte", "terabytes": "terabyte", "kilohercios": "kilohercio", "hercios": "hercio",
    "minutos": "minuto", "vatios": "vatio", "voltios": "voltio", "gramos": "gramo", "litros": "litro",
    "metros": "metro", "horas": "hora", "miliamperios hora": "miliamperio hora",
}

_INTEGER = r"\d{1,3}(?:\.\d{3})+|\d+"
_AMOUNT = re.compile(rf"(?<![\w,.])({_INTEGER})(?:,(\d{{1,2}}))?\s*(?:€|euros?\b|EUR\b)")
_PERCENT = re.compile(rf"(?<![\w,.])({_INTEGER})(?:,(\d+))?\s*%")
_WITH_UNIT = re.compile(
    rf"(?<![\w,.])({_INTEGER})(?:[.,](\d+))?\s?({'|'.join(sorted(_UNIT_WORDS, key=len, reverse=True))})(?![\w])"
)
_THOUSANDS = re.compile(r"(?<![\w,.])\d{1,3}(?:\.\d{3})+(?![\w]|[.,]\d)")
_DECIMAL_COMMA = re.compile(rf"(?<![\w,.])({_INTEGER}),(\d+)(?![\w]|[.,]\d)")
_DECIMAL_DOT = re.compile(r"(?<![\w,.])(\d+)\.(\d+)(?![\w]|[.,]\d)")
_PLAIN = re.compile(r"(?<![\w])(\d+)(?![\w])(\s+[^\W\d_]+)?")
# Identificadores: mayúsculas y cifras mezcladas (ASIN, referencias de modelo).
_IDENTIFIER = re.compile(r"(?<![\w-])(?=[A-Z0-9-]*\d)(?=[A-Z0-9-]*[A-Z])[A-Z0-9][A-Z0-9-]{4,}(?![\w-])")
_LONG_DIGITS = re.compile(r"(?<![\w,.])\d{6,}(?![\w,.])")
_QUOTED_TITLE = re.compile(r"«([^»]*)»")
_TITLE_CUT = re.compile(r"\s[-–—|/]\s|[,;:(\[]")
_TITLE_TAIL = frozenset("de del para con y e o la el los las en a por un una al sin".split())
MAX_TITLE_WORDS = 7


def _fold(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.lower())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def _to_int(digits: str) -> int:
    return int(digits.replace(".", ""))


def _digits_after_separator(digits: str) -> str:
    """Decimales tal como se dicen: "05" → "cero cinco", "5" → "cinco", "25" → "veinticinco"."""
    zeros = len(digits) - len(digits.lstrip("0"))
    rest = digits.lstrip("0")
    words = ["cero"] * zeros + ([number_to_words(int(rest))] if rest else [])
    return " ".join(words)


def spoken_title(title: str) -> str:
    """Título de catálogo reducido a lo que se diría en voz alta: la primera parte,
    sin referencias de modelo y con pocas palabras."""
    title = title.replace("…", " ").strip()
    title = _TITLE_CUT.split(title, maxsplit=1)[0]
    title = _LONG_DIGITS.sub(" ", _IDENTIFIER.sub(" ", title))
    words = title.split()[:MAX_TITLE_WORDS]
    while words and _fold(words[-1]) in _TITLE_TAIL:
        words.pop()
    return " ".join(words)


def _amount(match: re.Match[str]) -> str:
    cents = match.group(2) or ""
    return euros_to_words(_to_int(match.group(1)), int(cents.ljust(2, "0")) if cents else 0)


def _percent(match: re.Match[str]) -> str:
    words = number_to_words(_to_int(match.group(1)))
    if match.group(2):
        words += " coma " + _digits_after_separator(match.group(2))
    return words + " por ciento"


def _with_unit(match: re.Match[str]) -> str:
    whole, decimals, unit = _to_int(match.group(1)), match.group(2), _UNIT_WORDS[match.group(3)]
    form = "una" if unit in ("horas",) else "un"
    words = number_to_words(whole, form)
    if decimals:
        return f"{number_to_words(whole)} coma {_digits_after_separator(decimals)} {unit}"
    return f"{words} {_UNIT_SINGULAR.get(unit, unit) if whole == 1 else unit}"


def _decimal(separator: str):
    def replace(match: re.Match[str]) -> str:
        return f"{number_to_words(_to_int(match.group(1)))} {separator} {_digits_after_separator(match.group(2))}"

    return replace


def _plain(match: re.Match[str]) -> str:
    following = match.group(2) or ""
    noun = _fold(following.strip())
    form = "una" if noun in _FEMININE else "un" if noun in _MASCULINE else "uno"
    return number_to_words(int(match.group(1)), form) + following


def _spell_figures(text: str) -> str:
    """Importes, porcentajes, medidas y números sueltos, en palabras."""
    text = _AMOUNT.sub(_amount, text)
    text = _PERCENT.sub(_percent, text)
    text = _WITH_UNIT.sub(_with_unit, text)
    text = re.sub(r"(?<=\d)\s*[x×]\s*(?=\d)", " por ", text)
    text = _DECIMAL_COMMA.sub(_decimal("coma"), text)
    text = _THOUSANDS.sub(lambda match: str(_to_int(match.group(0))), text)
    text = _DECIMAL_DOT.sub(_decimal("punto"), text)
    return _PLAIN.sub(_plain, text)


def _drop_symbols(text: str) -> str:
    """Símbolos que un TTS leería mal: unos se dicen con palabras y otros sobran."""
    text = text.replace("€", " euros ").replace("%", " por ciento ").replace("&", " y ").replace("…", " ")
    text = re.sub(r"\s\+\s", " más ", text)
    text = re.sub(r"\s=\s", " igual a ", text)
    text = re.sub(r"[«»\"“”‘’`*_#~^|<>\\]", " ", text)
    text = re.sub(r"(?<![^\W\d_])'|'(?![^\W\d_])", " ", text)  # comillas simples, no apóstrofos (De'Longhi)
    text = re.sub(r"\s*[(\[{]\s*", ", ", text)
    text = re.sub(r"\s*[)\]}]", ",", text)
    text = text.replace(";", ",")
    return re.sub(r"\s[-–—]\s", ", ", text)


def _tidy_punctuation(text: str) -> str:
    """Espacios y signos que quedan sueltos al quitar o sustituir trozos."""
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([,.:?!])", r"\1", text)
    text = re.sub(r",(?:\s*,)+", ",", text)
    text = re.sub(r",\s*([.:?!])", r"\1", text)
    text = re.sub(r"([.:?!])\s*,", r"\1", text)
    text = re.sub(r"\.{2,}", ".", text).strip(" ,")
    # Una frase puede empezar ahora por una cifra en palabras: se le devuelve la mayúscula.
    return re.sub(r"(?:^|(?<=[.?!]\s))([^\W\d_])", lambda match: match.group(1).upper(), text)


def to_speech(text: str) -> str:
    """Versión del texto para el TTS: sin símbolos ni identificadores y con las cifras en palabras."""
    text = unicodedata.normalize("NFC", text)
    text = _QUOTED_TITLE.sub(lambda match: spoken_title(match.group(1)), text)
    text = _LONG_DIGITS.sub(" ", _IDENTIFIER.sub(" ", text))  # referencias, no cantidades
    text = re.sub(r"\bn\.?\s?º|\bnº|\bnúm\.", "número", text)
    return _tidy_punctuation(_drop_symbols(_spell_figures(text)))


# --- Troceado para el TTS -------------------------------------------------------------

_SENTENCE_END = re.compile(r"(?<=[.?!])\s+")


_CLAUSE_END = re.compile(r"(?<=,)\s+")


def _pack(pieces: list[str], max_chars: int) -> list[str]:
    """Une piezas consecutivas mientras quepan en ``max_chars``; una que no cabe queda sola."""
    packed, current = [], ""
    for piece in pieces:
        candidate = f"{current} {piece}" if current else piece
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            packed.append(current)
        current = piece
    return [*packed, current] if current else packed


def _fit(sentence: str, max_chars: int) -> list[str]:
    """Una frase que no cabe se parte por comas y, en último caso, por palabras."""
    if len(sentence) <= max_chars:
        return [sentence]
    pieces: list[str] = []
    for clause in _pack(_CLAUSE_END.split(sentence), max_chars):
        pieces += [clause] if len(clause) <= max_chars else _pack(clause.split(), max_chars)
    return pieces


def split_for_tts(text: str, max_chars: int = 200) -> list[str]:
    """Parte el texto en fragmentos de como mucho ``max_chars``: por frases y, si una
    frase no cabe, por comas (y en último caso por palabras). XTTS-v2 recorta las
    frases largas, y sintetizar por fragmentos permite empezar a reproducir antes."""
    chunks: list[str] = []
    for sentence in _pack(_SENTENCE_END.split(text.strip()), max_chars):
        chunks += _fit(sentence, max_chars)
    return [chunk.strip() for chunk in chunks if chunk.strip()]
