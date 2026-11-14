# Comparación de formas de clonar la voz

Experimento aparte del proyecto: no cambia el agente, la voz por defecto, las dependencias ni los resultados guardados. Compara, con las mismas frases y la misma medida, la voz actual del agente con otras formas de clonar la voz del autor. **La decisión se toma de oído**: los audios quedan en `audio/comparacion_voz/` (sin versionar, porque son la voz clonada de una persona) y aquí solo están los scripts y las cifras.

Las tablas con todas las cifras están en [RESULTADOS.md](RESULTADOS.md) (las genera `medir.py`; el detalle por frase, en `resultados.json`).

## Qué se compara

| Variante | Qué es |
|---|---|
| `A_xtts_actual` | La voz del agente hoy: XTTS-v2, grabación de referencia nueva, velocidad 1,10 |
| `B1_xtts_ritmo30` | XTTS-v2 con el ritmo condicionado por 30 s de la referencia (hoy son 6 s), velocidad 1,0 |
| `B2_xtts_varias` | B1 con el timbre promediado de 14 grabaciones reales (las dos de referencia y 12 turnos) |
| `B3_xtts_varias_t075` | B2 con temperatura 0,75 (la que trae XTTS-v2; el agente usa 0,65) |
| `B5_xtts_todo` | Timbre y ritmo de las 14 grabaciones (113 s) |
| `B4_xtts_turnos` | XTTS-v2 solo con los 12 turnos reales, sin las grabaciones de referencia |
| `C_f5_spanish` | F5-TTS con el ajuste al español `jpgallegoar/F5-Spanish`, 7 s de la referencia y su transcripción |
| `C2_f5_turnos` | F5-Spanish clonando de dos turnos reales (11,5 s) |
| `D1_chatterbox_v3` | Chatterbox multilingüe V3 (Resemble AI), idioma «es», referencia nueva |
| `D2_chatterbox_latam` | Chatterbox, ajuste al español de Latinoamérica, referencia nueva |
| `D3_chatterbox_latam_turnos` | D2 clonando de los 12 turnos reales seguidos |
| `E_xtts_conversion` | Conversión de voz de Chatterbox aplicada a los audios de A |

## Resultados (13 de noviembre, RTX A2000 de 12 GB)

Semejanza: cuanto más cerca del techo de la voz real, mejor. Las demás columnas completas están en [RESULTADOS.md](RESULTADOS.md).

| Variante | Semejanza con la voz real reservada | WER | Tono (Hz) | Sílabas/s | Síntesis / audio | VRAM (MiB) |
|---|---|---|---|---|---|---|
| **Techo: la voz real consigo misma** (turnos de otro grupo / grabación de referencia) | **0,378 / 0,413** | — | 105 / 120 | 4,8 / 5,7 | — | — |
| `A_xtts_actual` (la voz de hoy) | 0,245 | 9,6 % | 115 | 4,95 | 0,25 | 1 958 |
| `B1_xtts_ritmo30` | 0,252 | 6,3 % | 119 | 5,47 | 0,23 | 1 958 |
| `B2_xtts_varias` | 0,300 | 5,4 % | 119 | 5,47 | 0,23 | 1 960 |
| `B3_xtts_varias_t075` | 0,291 | 1,8 % | 121 | 5,66 | 0,23 | 1 960 |
| `B5_xtts_todo` | 0,321 | 4,8 % | 107 | 5,78 | 0,23 | 1 960 |
| `B4_xtts_turnos` | 0,312 | 2,4 % | 114 | 6,06 | 0,23 | 1 960 |
| `C_f5_spanish` | 0,312 | 9,9 % | 120 | 5,31 | 0,30 | 1 308 |
| `C2_f5_turnos` | **0,369** | 7,5 % | 108 | 6,18 | 0,40 | 1 354 |
| `D1_chatterbox_v3` | 0,271 | 3,6 % | 122 | 5,71 | 0,62 | 4 546 |
| `D2_chatterbox_latam` | 0,278 | 5,4 % | 115 | 6,47 | 0,61 | 4 700 |
| `D3_chatterbox_latam_turnos` | 0,328 | 2,7 % | 112 | 6,49 | 0,62 | 4 920 |
| `E_xtts_conversion` | 0,287 | 13,3 % | 117 | 5,08 | 0,19 (más el 0,25 de A) | 4 012 |

Qué dicen las cifras:

- **La voz de hoy es la que menos se parece** (0,245 frente a un techo de 0,38–0,41). Condicionar el ritmo con 30 s en vez de 6 casi no cambia el parecido (0,252).
- **Lo que más mueve el parecido es de qué grabaciones se clona, más que el modelo.** Con los turnos reales en vez de la grabación de referencia suben los tres modelos: XTTS-v2 de 0,252 a 0,312, F5-Spanish de 0,312 a 0,369 y Chatterbox de 0,278 a 0,328. La grabación de referencia está leída con un tono más agudo (120 Hz) que el del autor cuando habla en los turnos (105 Hz), y las voces clonadas de ella heredan ese tono.
- **F5-Spanish clonando de dos turnos (`C2`) es la única que llega al techo** (0,369 frente a 0,378), pero habla más rápido que el autor (6,2 sílabas por segundo frente a 4,8), con el tono más plano (3,3 semitonos frente a 5,5) y en la frase corta 5 se saltó la primera mitad: de «Pedido número uno registrado. ¡Gracias por tu compra!» Whisper solo oyó «Gracias por tu compra».
- **XTTS-v2 con todas las grabaciones (`B5`) es la mejor de las que no cuestan nada**: 0,321, el tono del autor (107 Hz) y la misma velocidad de síntesis y memoria que hoy.
- **Chatterbox** no mejora a XTTS-v2 bien usado, tarda unas 2,5 veces más y ocupa 2,4 veces más memoria. El ajuste latinoamericano no cambia el parecido (0,278 frente a 0,271).
- **La conversión de voz (`E`)** sube algo el parecido de A (0,287) y empeora la inteligibilidad (13,3 %).
- En la frase 7 (marcas difíciles) ninguna variante dice bien todas las marcas; las de XTTS-v2 con la referencia nueva se atascan (WER del 22 al 37 %) y las demás la dicen entera con las marcas deformadas (6–10 %).

Reservas: una sola semilla y diez frases (unas 330 palabras), así que diferencias de pocos puntos de WER o de 0,02 de semejanza pueden ser azar. Los turnos de clonar y los de medir se grabaron en la misma sesión y con el mismo micrófono: parte de la subida al clonar de turnos puede ser parecido de la grabación y no de la voz. Por eso manda el oído.

## Qué costaría adoptar cada una

| | XTTS-v2 con más grabaciones (B) | F5-Spanish (C) | Chatterbox (D) |
|---|---|---|---|
| Dependencias | Ninguna nueva: unas líneas en `XttsTTS` para aceptar varias grabaciones y `gpt_cond_len` | Paquete `f5-tts` (probado con torch 2.6 en un entorno aparte; sin probar junto a las dependencias del proyecto) y la transcripción de la referencia | Fija `torch==2.6.0`, `transformers==4.46.3` y `numpy<1.26`, incompatibles con las del proyecto: pediría un proceso aparte. El V3 y los ajustes por idioma solo están en el repositorio, no en PyPI, y su README lo da por retirado desde agosto de 2026 |
| Licencia | La de hoy (CPML, no comercial) | Código MIT; pesos CC-BY-NC-4.0 (no comercial) según los metadatos, aunque el texto de la ficha dice CC0 | MIT; marca cada audio con una marca de agua inaudible |
| VRAM del proceso | 1 960 MiB (igual que hoy) | 1 350 MiB | 4 550–4 920 MiB |
| Junto al LLM y Whisper | Como hoy: 9 532 MiB en la A2000 y 9 152 MiB en la T4 | Algo menos que hoy (estimado) | Unos 12,5 GB (estimado): no cabe en la A2000 de 12 GB; en la T4 de 15 GB cabría justo |
| Latencia | Igual que hoy (0,23 s de síntesis por segundo de audio) | 1,3–1,7 veces la de hoy; genera cada fragmento entero antes de sonar | Unas 2,5 veces la de hoy |

En Colab (T4) no se midió ninguna: allí XTTS-v2 ya tarda 2,2 veces más que en la workstation.

## Qué no se verificó

- Nadie ha escuchado los audios: las cifras no sustituyen al oído.
- Una sola semilla por variante.
- La memoria junto al LLM y Whisper de F5-Spanish y Chatterbox es una suma, no una medida; en la T4 no se probó nada.
- Que `f5-tts` conviva con las dependencias del proyecto.
- La licencia de F5-Spanish tiene dos versiones en su propia ficha; no pide aceptar condiciones para descargarlo.

## Cómo se mide

- **Grabaciones reales en dos grupos.** Para clonar: `audio/referencia/referencia.wav` (39,6 s), `audio/referencia/referencia_anterior.wav` (30,2 s) y los 12 turnos de los escenarios 01, 02 y 03 (43 s). Solo para medir: los 19 turnos de los escenarios 04, 05 y 06 (50 s); ninguna variante los usa como referencia.
- **Frases** ([frases.txt](frases.txt)): las seis de la comparación de voces anterior y cuatro respuestas reales del agente: la de las marcas difíciles del escenario 02 (frase 7), una confirmación con «Di sí» (8), la más larga (9, 544 caracteres) y un pedido registrado (10).
- **Semejanza**: ECAPA-TDNN (`speechbrain/spkrec-ecapa-voxceleb`), media del coseno de cada audio con los 19 turnos del grupo de medida. Las filas «Voz real» son el techo: lo que saca la propia voz del autor con la misma medida.
- **WER**: Whisper `large-v3-turbo` sobre cada audio, con la normalización de `shopping_agent.eval.voice`.
- **Ritmo y tono**: sílabas (grupos de vocales) por segundo hablando, sin las pausas; mediana del tono (pYIN, 60–350 Hz) y su desviación en semitonos. Se comparan con las filas de la voz real.
- **Coste**: segundos de síntesis de las diez frases, síntesis entre duración del audio, y memoria de GPU del proceso al terminar (`nvidia-smi`), en la RTX A2000 de 12 GB con la GPU libre.
- **Una sola semilla** (0) por variante: las diferencias pequeñas entre variantes pueden ser azar del muestreo.

## Cómo se obtuvo

```bash
# Entorno del proyecto (XTTS-v2, preparación y medida)
PYTHONPATH=src:experiments/comparacion_voz python experiments/comparacion_voz/xtts_variantes.py
PYTHONPATH=src:experiments/comparacion_voz python experiments/comparacion_voz/preparar.py
# Entornos temporales, uno por modelo, fuera del repositorio
uv venv --python 3.11 /tmp/f5 && uv pip install --python /tmp/f5/bin/python torch==2.6.0 torchaudio==2.6.0 f5-tts
uv venv --python 3.11 /tmp/chatterbox && uv pip install --python /tmp/chatterbox/bin/python "chatterbox-tts @ git+https://github.com/resemble-ai/chatterbox.git"
PYTHONPATH=experiments/comparacion_voz /tmp/f5/bin/python experiments/comparacion_voz/f5_spanish.py C_f5_spanish
PYTHONPATH=experiments/comparacion_voz /tmp/chatterbox/bin/python experiments/comparacion_voz/chatterbox_es.py D2_chatterbox_latam /tmp/latam
# Medida de todo lo que haya en audio/comparacion_voz
PYTHONPATH=src:experiments/comparacion_voz python experiments/comparacion_voz/medir.py
```

Todo corre en local: las grabaciones no salen de la máquina y de internet solo se descargan los pesos de los modelos.
