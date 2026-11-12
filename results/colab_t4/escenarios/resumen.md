# Evaluación con escenarios: resumen

Cada corrida tiene una ficha por escenario en su carpeta.

## Escenarios correctos por corrida

| Corrida | Entrada | Reranker | Escenarios | Correctos | % correctos |
|---|---|---|---|---|---|
| `texto` | texto | control | 20 | 20 | 100.0 % |
| `texto_sage` | texto | sage | 20 | 20 | 100.0 % |
| `texto_sin_reranker` | texto | sin reranker | 20 | 20 | 100.0 % |
| `voz` | audio | control | 6 | 6 | 100.0 % |
| `voz_texto_correcto` | texto | control | 6 | 6 | 100.0 % |
| `voz_velocidad_1_15` | audio | control | 6 | 6 | 100.0 % |
| `voz_referencia_anterior` | audio | control | 6 | 6 | 100.0 % |
| `voz_sintetica` | audio | control | 6 | 6 | 100.0 % |
| `reserva` | texto | control | 4 | 3 | 75.0 % |
| `reserva_cifras` | texto | control | 2 | 2 | 100.0 % |
| `reserva_cifras_sage` | texto | sage | 2 | 2 | 100.0 % |
| `reserva_cifras_sin_reranker` | texto | sin reranker | 2 | 2 | 100.0 % |
| `reserva_sage` | texto | sage | 4 | 4 | 100.0 % |
| `reserva_sin_reranker` | texto | sin reranker | 4 | 3 | 75.0 % |

| Escenario | `texto` | `texto_sage` | `texto_sin_reranker` | `voz` | `voz_texto_correcto` | `voz_velocidad_1_15` | `voz_referencia_anterior` | `voz_sintetica` | `reserva` | `reserva_cifras` | `reserva_cifras_sage` | `reserva_cifras_sin_reranker` | `reserva_sage` | `reserva_sin_reranker` |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `01_compra_confirmada` | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |  |  |  |  |  |  |
| `02_pedido_ambiguo` | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |  |  |  |  |  |  |
| `03_cambio_cantidad` | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |  |  |  |  |  |  |
| `04_sin_existencias` | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |  |  |  |  |  |  |
| `05_correccion_transcripcion` | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |  |  |  |  |  |  |
| `06_cambio_stock_confirmacion_repetida` | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |  |  |  |  |  |  |
| `07_presupuesto_excedido` | ✔ | ✔ | ✔ |  |  |  |  |  |  |  |  |  |  |  |
| `08_cantidad_invalida` | ✔ | ✔ | ✔ |  |  |  |  |  |  |  |  |  |  |  |
| `09_producto_inexistente` | ✔ | ✔ | ✔ |  |  |  |  |  |  |  |  |  |  |  |
| `10_atributo_no_verificable` | ✔ | ✔ | ✔ |  |  |  |  |  |  |  |  |  |  |  |
| `11_rechazo_confirmacion` | ✔ | ✔ | ✔ |  |  |  |  |  |  |  |  |  |  |  |
| `12_memoria_preferencias` | ✔ | ✔ | ✔ |  |  |  |  |  |  |  |  |  |  |  |
| `13_confirmacion_con_cambio` | ✔ | ✔ | ✔ |  |  |  |  |  |  |  |  |  |  |  |
| `14_pregunta_sin_cambios` | ✔ | ✔ | ✔ |  |  |  |  |  |  |  |  |  |  |  |
| `15_stock_insuficiente` | ✔ | ✔ | ✔ |  |  |  |  |  |  |  |  |  |  |  |
| `16_quitar_del_carrito` | ✔ | ✔ | ✔ |  |  |  |  |  |  |  |  |  |  |  |
| `17_cambio_presupuesto` | ✔ | ✔ | ✔ |  |  |  |  |  |  |  |  |  |  |  |
| `18_cierre_sin_carrito` | ✔ | ✔ | ✔ |  |  |  |  |  |  |  |  |  |  |  |
| `19_presupuesto_compartido` | ✔ | ✔ | ✔ |  |  |  |  |  |  |  |  |  |  |  |
| `20_agotado_al_confirmar` | ✔ | ✔ | ✔ |  |  |  |  |  |  |  |  |  |  |  |
| `21_cierre_otras_palabras` |  |  |  |  |  |  |  |  | ✔ |  |  |  | ✔ | ✔ |
| `22_agotado_otro_candidato` |  |  |  |  |  |  |  |  | ✔ |  |  |  | ✔ | ✔ |
| `23_candidato_fuera_de_lista` |  |  |  |  |  |  |  |  | ✔ |  |  |  | ✔ | ✔ |
| `24_dato_que_no_consta` |  |  |  |  |  |  |  |  | ✘ |  |  |  | ✔ | ✘ |
| `25_correccion_con_cifras` |  |  |  |  |  |  |  |  |  | ✔ | ✔ | ✔ |  |  |
| `26_presupuesto_con_carrito` |  |  |  |  |  |  |  |  |  | ✔ | ✔ | ✔ |  |  |

## Antes y después de corregir el agente

Línea base: `results/escenarios_base`.

| Corrida | Antes | Después | Arreglados | Regresiones |
|---|---|---|---|---|
| `texto` | 14 de 20 | 20 de 20 | 03, 04, 06, 09, 10, 20 | ninguno |
| `texto_sage` | 16 de 20 | 20 de 20 | 03, 04, 06, 09 | ninguno |
| `texto_sin_reranker` | 16 de 20 | 20 de 20 | 03, 04, 09, 10 | ninguno |
| `voz_texto_correcto` | 3 de 6 | 6 de 6 | 03, 04, 06 | ninguno |
| `voz_sintetica` | 3 de 6 | 6 de 6 | 03, 04, 06 | ninguno |

| Escenario (antes → después) | `texto` | `texto_sage` | `texto_sin_reranker` | `voz_texto_correcto` | `voz_sintetica` |
|---|---|---|---|---|---|
| `01_compra_confirmada` | ✔ → ✔ | ✔ → ✔ | ✔ → ✔ | ✔ → ✔ | ✔ → ✔ |
| `02_pedido_ambiguo` | ✔ → ✔ | ✔ → ✔ | ✔ → ✔ | ✔ → ✔ | ✔ → ✔ |
| `03_cambio_cantidad` | ✘ → ✔ | ✘ → ✔ | ✘ → ✔ | ✘ → ✔ | ✘ → ✔ |
| `04_sin_existencias` | ✘ → ✔ | ✘ → ✔ | ✘ → ✔ | ✘ → ✔ | ✘ → ✔ |
| `05_correccion_transcripcion` | ✔ → ✔ | ✔ → ✔ | ✔ → ✔ | ✔ → ✔ | ✔ → ✔ |
| `06_cambio_stock_confirmacion_repetida` | ✘ → ✔ | ✘ → ✔ | ✔ → ✔ | ✘ → ✔ | ✘ → ✔ |
| `07_presupuesto_excedido` | ✔ → ✔ | ✔ → ✔ | ✔ → ✔ |  |  |
| `08_cantidad_invalida` | ✔ → ✔ | ✔ → ✔ | ✔ → ✔ |  |  |
| `09_producto_inexistente` | ✘ → ✔ | ✘ → ✔ | ✘ → ✔ |  |  |
| `10_atributo_no_verificable` | ✘ → ✔ | ✔ → ✔ | ✘ → ✔ |  |  |
| `11_rechazo_confirmacion` | ✔ → ✔ | ✔ → ✔ | ✔ → ✔ |  |  |
| `12_memoria_preferencias` | ✔ → ✔ | ✔ → ✔ | ✔ → ✔ |  |  |
| `13_confirmacion_con_cambio` | ✔ → ✔ | ✔ → ✔ | ✔ → ✔ |  |  |
| `14_pregunta_sin_cambios` | ✔ → ✔ | ✔ → ✔ | ✔ → ✔ |  |  |
| `15_stock_insuficiente` | ✔ → ✔ | ✔ → ✔ | ✔ → ✔ |  |  |
| `16_quitar_del_carrito` | ✔ → ✔ | ✔ → ✔ | ✔ → ✔ |  |  |
| `17_cambio_presupuesto` | ✔ → ✔ | ✔ → ✔ | ✔ → ✔ |  |  |
| `18_cierre_sin_carrito` | ✔ → ✔ | ✔ → ✔ | ✔ → ✔ |  |  |
| `19_presupuesto_compartido` | ✔ → ✔ | ✔ → ✔ | ✔ → ✔ |  |  |
| `20_agotado_al_confirmar` | ✘ → ✔ | ✔ → ✔ | ✔ → ✔ |  |  |

## Violaciones de restricciones

| Corrida | cantidad | presupuesto | existencias | pedido_duplicado | cambio_parcial |
|---|---|---|---|---|---|
| `texto` | 0 | 0 | 0 | 0 | 0 |
| `texto_sage` | 0 | 0 | 0 | 0 | 0 |
| `texto_sin_reranker` | 0 | 0 | 0 | 0 | 0 |
| `voz` | 0 | 0 | 0 | 0 | 0 |
| `voz_texto_correcto` | 0 | 0 | 0 | 0 | 0 |
| `voz_velocidad_1_15` | 0 | 0 | 0 | 0 | 0 |
| `voz_referencia_anterior` | 0 | 0 | 0 | 0 | 0 |
| `voz_sintetica` | 0 | 0 | 0 | 0 | 0 |
| `reserva` | 0 | 0 | 0 | 0 | 0 |
| `reserva_cifras` | 0 | 0 | 0 | 0 | 0 |
| `reserva_cifras_sage` | 0 | 0 | 0 | 0 | 0 |
| `reserva_cifras_sin_reranker` | 0 | 0 | 0 | 0 | 0 |
| `reserva_sage` | 0 | 0 | 0 | 0 | 0 |
| `reserva_sin_reranker` | 0 | 0 | 0 | 0 | 0 |

## Voz

| Corrida | Voz del agente | Correctos | Inteligibilidad (WER) | Semejanza con la referencia | Semejanza con las grabaciones reales | Audio de respuesta (s) | TTS (s por turno) | Total (s por turno) | Total con LLM (s) |
|---|---|---|---|---|---|---|---|---|---|
| `voz` | clonada de la grabación de referencia `audio/referencia/referencia.wav`, velocidad del habla 1,10 | 6 de 6 | 5.6 % | 0.709 | 0.272 | 21.44 | 12.44 | 18.96 | 21.38 |
| `voz_velocidad_1_15` | clonada de la grabación de referencia `audio/referencia/referencia.wav`, velocidad del habla 1,15 | 6 de 6 | 7.0 % | 0.709 | 0.270 | 20.68 | 5.61 | 9.92 | 11.35 |
| `voz_referencia_anterior` | clonada de la grabación de referencia `audio/referencia/referencia_anterior.wav` | 6 de 6 | 3.4 % | 0.741 | 0.259 | 24.78 | 6.07 | 10.36 | 11.97 |
| `voz_sintetica` | clonada de la grabación de referencia `audio/referencia/referencia_anterior.wav` | 6 de 6 | 3.9 % | 0.741 | — | 24.77 | 5.88 | 10.19 | 11.75 |

La semejanza con la referencia compara con la misma grabación de la que se clonó la voz y sale optimista (misma toma, mismo micrófono); la semejanza con las grabaciones reales compara con audios del mismo hablante que el modelo no usó y dice mejor cuánto se parece a su voz de otro momento.

### `voz`

**Audios de entrada: grabaciones del usuario.** Escenarios 01, 02, 03, 04, 05, 06: 6 de 6 correctos.

- ASR: 31 turnos, 29 idénticos tras normalizar; WER 1.4 %.
- Errores del ASR en importes: 0 de 3 (0.0 %).
- Errores del ASR en cantidades: 0 de 8 (0.0 %).
- Errores del ASR en nombres de producto: 1 de 13 (7.7 %).
- Turnos en los que el ASR cambió palabras: 2.
  - `01_compra_confirmada`, turno 1: se dijo «Hola, busco una cafetera italiana. Tengo un presupuesto de 60 euros.» y entendió «Hola, busco una cafetería italiana. Tengo un presupuesto de 60 euros.».
  - `05_correccion_transcripcion`, turno 1: se dijo «Busco un ratón inalámbrico.» y entendió «Busca un ratón inalámbrico.».
- Inteligibilidad de la voz generada (WER de Whisper sobre 31 respuestas): 5.6 %.
- Semejanza con la referencia (coseno ECAPA): media 0.709, mínima 0.636.
- Semejanza con las grabaciones reales (coseno ECAPA): media 0.272, mínima 0.235.
- Como techo, las 31 grabaciones reales se parecen entre sí 0.377.
- Latencia media por turno con LLM (24 turnos, segundos): ASR 0.41, Recuperación 0.02, LLM 7.85, Herramientas 0.04, TTS 13.07, Total 21.38; máximo 36.26.

### `voz_velocidad_1_15`

**Audios de entrada: grabaciones del usuario.** Escenarios 01, 02, 03, 04, 05, 06: 6 de 6 correctos.

- ASR: 31 turnos, 29 idénticos tras normalizar; WER 1.4 %.
- Errores del ASR en importes: 0 de 3 (0.0 %).
- Errores del ASR en cantidades: 0 de 8 (0.0 %).
- Errores del ASR en nombres de producto: 1 de 13 (7.7 %).
- Turnos en los que el ASR cambió palabras: 2.
  - `01_compra_confirmada`, turno 1: se dijo «Hola, busco una cafetera italiana. Tengo un presupuesto de 60 euros.» y entendió «Hola, busco una cafetería italiana. Tengo un presupuesto de 60 euros.».
  - `05_correccion_transcripcion`, turno 1: se dijo «Busco un ratón inalámbrico.» y entendió «Busca un ratón inalámbrico.».
- Inteligibilidad de la voz generada (WER de Whisper sobre 31 respuestas): 7.0 %.
- Semejanza con la referencia (coseno ECAPA): media 0.709, mínima 0.593.
- Semejanza con las grabaciones reales (coseno ECAPA): media 0.270, mínima 0.191.
- Como techo, las 31 grabaciones reales se parecen entre sí 0.377.
- Latencia media por turno con LLM (24 turnos, segundos): ASR 0.35, Recuperación 0.01, LLM 5.05, Herramientas 0.04, TTS 5.89, Total 11.35; máximo 18.63.

### `voz_referencia_anterior`

**Audios de entrada: grabaciones del usuario.** Escenarios 01, 02, 03, 04, 05, 06: 6 de 6 correctos.

- ASR: 31 turnos, 29 idénticos tras normalizar; WER 1.4 %.
- Errores del ASR en importes: 0 de 3 (0.0 %).
- Errores del ASR en cantidades: 0 de 8 (0.0 %).
- Errores del ASR en nombres de producto: 1 de 13 (7.7 %).
- Turnos en los que el ASR cambió palabras: 2.
  - `01_compra_confirmada`, turno 1: se dijo «Hola, busco una cafetera italiana. Tengo un presupuesto de 60 euros.» y entendió «Hola, busco una cafetería italiana. Tengo un presupuesto de 60 euros.».
  - `05_correccion_transcripcion`, turno 1: se dijo «Busco un ratón inalámbrico.» y entendió «Busca un ratón inalámbrico.».
- Inteligibilidad de la voz generada (WER de Whisper sobre 31 respuestas): 3.4 %.
- Semejanza con la referencia (coseno ECAPA): media 0.741, mínima 0.501.
- Semejanza con las grabaciones reales (coseno ECAPA): media 0.259, mínima 0.221.
- Como techo, las 31 grabaciones reales se parecen entre sí 0.377.
- Latencia media por turno con LLM (24 turnos, segundos): ASR 0.35, Recuperación 0.01, LLM 5.03, Herramientas 0.04, TTS 6.54, Total 11.97; máximo 25.55.

### `voz_sintetica`

**Audios de entrada: sintéticos, hablante de prueba «Luis Moray» de XTTS-v2 (no es la voz del usuario).** Escenarios 01, 02, 03, 04, 05, 06: 6 de 6 correctos.

- ASR: 31 turnos, 28 idénticos tras normalizar; WER 2.1 %.
- Errores del ASR en importes: 0 de 3 (0.0 %).
- Errores del ASR en cantidades: 0 de 8 (0.0 %).
- Errores del ASR en nombres de producto: 0 de 13 (0.0 %).
- Turnos en los que el ASR cambió palabras: 3.
  - `01_compra_confirmada`, turno 2: se dijo «Añade dos de la primera al carrito.» y entendió «Añade dos de la primera al carrito E.».
  - `04_sin_existencias`, turno 3: se dijo «Entonces ponme una de la segunda.» y entendió «Entonces ponme una de la segunda. De.».
  - `06_cambio_stock_confirmacion_repetida`, turno 1: se dijo «Busco una lámpara de escritorio LED.» y entendió «Busco una lámpara de escritorio LED. Lo.».
- Inteligibilidad de la voz generada (WER de Whisper sobre 31 respuestas): 3.9 %.
- Semejanza con la referencia (coseno ECAPA): media 0.741, mínima 0.501.
- Latencia media por turno con LLM (24 turnos, segundos): ASR 0.35, Recuperación 0.01, LLM 5.05, Herramientas 0.04, TTS 6.30, Total 11.75; máximo 20.62.

## Audio frente a transcripción correcta

### `voz`

| Escenario | Con audio | Con el texto correcto | Turnos con palabras cambiadas por el ASR | Turnos con operaciones distintas | Misma tienda final |
|---|---|---|---|---|---|
| `01_compra_confirmada` | ✔ | ✔ | [1] | [1, 2] | no |
| `02_pedido_ambiguo` | ✔ | ✔ | ninguno | [2] | sí |
| `03_cambio_cantidad` | ✔ | ✔ | ninguno | ninguno | sí |
| `04_sin_existencias` | ✔ | ✔ | ninguno | ninguno | sí |
| `05_correccion_transcripcion` | ✔ | ✔ | [1] | ninguno | sí |
| `06_cambio_stock_confirmacion_repetida` | ✔ | ✔ | ninguno | ninguno | sí |

### `voz_velocidad_1_15`

| Escenario | Con audio | Con el texto correcto | Turnos con palabras cambiadas por el ASR | Turnos con operaciones distintas | Misma tienda final |
|---|---|---|---|---|---|
| `01_compra_confirmada` | ✔ | ✔ | [1] | [1, 2] | no |
| `02_pedido_ambiguo` | ✔ | ✔ | ninguno | [1, 2] | sí |
| `03_cambio_cantidad` | ✔ | ✔ | ninguno | ninguno | sí |
| `04_sin_existencias` | ✔ | ✔ | ninguno | ninguno | sí |
| `05_correccion_transcripcion` | ✔ | ✔ | [1] | ninguno | sí |
| `06_cambio_stock_confirmacion_repetida` | ✔ | ✔ | ninguno | ninguno | sí |

### `voz_referencia_anterior`

| Escenario | Con audio | Con el texto correcto | Turnos con palabras cambiadas por el ASR | Turnos con operaciones distintas | Misma tienda final |
|---|---|---|---|---|---|
| `01_compra_confirmada` | ✔ | ✔ | [1] | [1, 2] | no |
| `02_pedido_ambiguo` | ✔ | ✔ | ninguno | [1, 2] | sí |
| `03_cambio_cantidad` | ✔ | ✔ | ninguno | ninguno | sí |
| `04_sin_existencias` | ✔ | ✔ | ninguno | ninguno | sí |
| `05_correccion_transcripcion` | ✔ | ✔ | [1] | ninguno | sí |
| `06_cambio_stock_confirmacion_repetida` | ✔ | ✔ | ninguno | ninguno | sí |

### `voz_sintetica`

| Escenario | Con audio | Con el texto correcto | Turnos con palabras cambiadas por el ASR | Turnos con operaciones distintas | Misma tienda final |
|---|---|---|---|---|---|
| `01_compra_confirmada` | ✔ | ✔ | [2] | ninguno | sí |
| `02_pedido_ambiguo` | ✔ | ✔ | ninguno | [1, 2] | sí |
| `03_cambio_cantidad` | ✔ | ✔ | ninguno | ninguno | sí |
| `04_sin_existencias` | ✔ | ✔ | [3] | ninguno | sí |
| `05_correccion_transcripcion` | ✔ | ✔ | ninguno | ninguno | sí |
| `06_cambio_stock_confirmacion_repetida` | ✔ | ✔ | [1] | ninguno | sí |

## Latencia por etapa (segundos por turno, media y máximo)

| Corrida | Turnos | ASR | Recuperación | LLM | Herramientas | TTS | Total |
|---|---|---|---|---|---|---|---|
| `texto`, con LLM | 73 | 0.00 (máx. 0.00) | 0.02 (máx. 0.15) | 8.00 (máx. 15.53) | 0.03 (máx. 0.07) | 0.00 (máx. 0.00) | 8.06 (máx. 15.64) |
| `texto`, sin LLM | 14 | 0.00 (máx. 0.00) | 0.01 (máx. 0.07) | 0.00 (máx. 0.00) | 0.03 (máx. 0.04) | 0.00 (máx. 0.00) | 0.04 (máx. 0.11) |
| `texto_sage`, con LLM | 73 | 0.00 (máx. 0.00) | 0.01 (máx. 0.04) | 4.99 (máx. 10.75) | 0.04 (máx. 0.07) | 0.00 (máx. 0.00) | 5.03 (máx. 10.83) |
| `texto_sage`, sin LLM | 14 | 0.00 (máx. 0.00) | 0.01 (máx. 0.04) | 0.00 (máx. 0.00) | 0.03 (máx. 0.03) | 0.00 (máx. 0.00) | 0.03 (máx. 0.06) |
| `texto_sin_reranker`, con LLM | 73 | 0.00 (máx. 0.00) | 0.01 (máx. 0.03) | 4.97 (máx. 9.42) | 0.04 (máx. 0.07) | 0.00 (máx. 0.00) | 5.02 (máx. 9.50) |
| `texto_sin_reranker`, sin LLM | 14 | 0.00 (máx. 0.00) | 0.00 (máx. 0.02) | 0.00 (máx. 0.00) | 0.03 (máx. 0.03) | 0.00 (máx. 0.00) | 0.03 (máx. 0.03) |
| `voz`, con LLM | 24 | 0.41 (máx. 1.00) | 0.02 (máx. 0.12) | 7.85 (máx. 16.52) | 0.04 (máx. 0.05) | 13.07 (máx. 20.09) | 21.38 (máx. 36.26) |
| `voz`, sin LLM | 7 | 0.35 (máx. 0.37) | 0.01 (máx. 0.05) | 0.00 (máx. 0.00) | 0.03 (máx. 0.04) | 10.27 (máx. 23.29) | 10.66 (máx. 23.69) |
| `voz_texto_correcto`, con LLM | 24 | 0.00 (máx. 0.00) | 0.02 (máx. 0.12) | 7.97 (máx. 13.66) | 0.03 (máx. 0.05) | 0.00 (máx. 0.00) | 8.03 (máx. 13.80) |
| `voz_texto_correcto`, sin LLM | 7 | 0.00 (máx. 0.00) | 0.01 (máx. 0.05) | 0.00 (máx. 0.00) | 0.03 (máx. 0.05) | 0.00 (máx. 0.00) | 0.04 (máx. 0.07) |
| `voz_velocidad_1_15`, con LLM | 24 | 0.35 (máx. 0.57) | 0.01 (máx. 0.03) | 5.05 (máx. 10.01) | 0.04 (máx. 0.06) | 5.89 (máx. 9.59) | 11.35 (máx. 18.63) |
| `voz_velocidad_1_15`, sin LLM | 7 | 0.33 (máx. 0.33) | 0.00 (máx. 0.02) | 0.00 (máx. 0.00) | 0.04 (máx. 0.04) | 4.65 (máx. 10.44) | 5.02 (máx. 10.80) |
| `voz_referencia_anterior`, con LLM | 24 | 0.35 (máx. 0.55) | 0.01 (máx. 0.03) | 5.03 (máx. 9.96) | 0.04 (máx. 0.06) | 6.54 (máx. 17.26) | 11.97 (máx. 25.55) |
| `voz_referencia_anterior`, sin LLM | 7 | 0.32 (máx. 0.34) | 0.00 (máx. 0.03) | 0.00 (máx. 0.00) | 0.04 (máx. 0.04) | 4.47 (máx. 10.66) | 4.83 (máx. 11.02) |
| `voz_sintetica`, con LLM | 24 | 0.35 (máx. 0.56) | 0.01 (máx. 0.05) | 5.05 (máx. 9.84) | 0.04 (máx. 0.06) | 6.30 (máx. 11.85) | 11.75 (máx. 20.62) |
| `voz_sintetica`, sin LLM | 7 | 0.32 (máx. 0.33) | 0.00 (máx. 0.03) | 0.00 (máx. 0.00) | 0.04 (máx. 0.04) | 4.46 (máx. 10.64) | 4.82 (máx. 11.01) |
| `reserva`, con LLM | 15 | 0.00 (máx. 0.00) | 0.01 (máx. 0.03) | 4.96 (máx. 8.39) | 0.03 (máx. 0.05) | 0.00 (máx. 0.00) | 5.00 (máx. 8.45) |
| `reserva`, sin LLM | 3 | 0.00 (máx. 0.00) | 0.00 (máx. 0.00) | 0.00 (máx. 0.00) | 0.02 (máx. 0.03) | 0.00 (máx. 0.00) | 0.02 (máx. 0.03) |
| `reserva_cifras`, con LLM | 10 | 0.00 (máx. 0.00) | 0.01 (máx. 0.03) | 5.42 (máx. 8.09) | 0.04 (máx. 0.05) | 0.00 (máx. 0.00) | 5.47 (máx. 8.12) |
| `reserva_cifras`, sin LLM | 2 | 0.00 (máx. 0.00) | 0.00 (máx. 0.00) | 0.00 (máx. 0.00) | 0.03 (máx. 0.03) | 0.00 (máx. 0.00) | 0.03 (máx. 0.03) |
| `reserva_cifras_sage`, con LLM | 10 | 0.00 (máx. 0.00) | 0.01 (máx. 0.04) | 5.30 (máx. 8.97) | 0.04 (máx. 0.06) | 0.00 (máx. 0.00) | 5.35 (máx. 9.05) |
| `reserva_cifras_sage`, sin LLM | 2 | 0.00 (máx. 0.00) | 0.00 (máx. 0.00) | 0.00 (máx. 0.00) | 0.03 (máx. 0.03) | 0.00 (máx. 0.00) | 0.03 (máx. 0.03) |
| `reserva_cifras_sin_reranker`, con LLM | 10 | 0.00 (máx. 0.00) | 0.01 (máx. 0.03) | 5.28 (máx. 9.07) | 0.04 (máx. 0.05) | 0.00 (máx. 0.00) | 5.32 (máx. 9.13) |
| `reserva_cifras_sin_reranker`, sin LLM | 2 | 0.00 (máx. 0.00) | 0.00 (máx. 0.00) | 0.00 (máx. 0.00) | 0.03 (máx. 0.03) | 0.00 (máx. 0.00) | 0.03 (máx. 0.03) |
| `reserva_sage`, con LLM | 15 | 0.00 (máx. 0.00) | 0.01 (máx. 0.04) | 4.94 (máx. 8.16) | 0.04 (máx. 0.06) | 0.00 (máx. 0.00) | 4.99 (máx. 8.24) |
| `reserva_sage`, sin LLM | 3 | 0.00 (máx. 0.00) | 0.00 (máx. 0.00) | 0.00 (máx. 0.00) | 0.03 (máx. 0.03) | 0.00 (máx. 0.00) | 0.03 (máx. 0.03) |
| `reserva_sin_reranker`, con LLM | 15 | 0.00 (máx. 0.00) | 0.01 (máx. 0.03) | 5.02 (máx. 8.45) | 0.04 (máx. 0.06) | 0.00 (máx. 0.00) | 5.07 (máx. 8.52) |
| `reserva_sin_reranker`, sin LLM | 3 | 0.00 (máx. 0.00) | 0.00 (máx. 0.00) | 0.00 (máx. 0.00) | 0.02 (máx. 0.03) | 0.00 (máx. 0.00) | 0.02 (máx. 0.03) |

Carga inicial de los modelos, aparte de los turnos:

- `texto`: catálogo y recuperadores 35.9 s, LLM 1.9 s; total 38.2 s.
- `texto_sage`: catálogo y recuperadores 149.8 s, LLM 0.8 s; total 150.9 s.
- `texto_sin_reranker`: catálogo y recuperadores 15.8 s, LLM 0.7 s; total 16.9 s.
- `voz`: catálogo y recuperadores 38.9 s, LLM 9.6 s, ASR 28.3 s, TTS 30.6 s; total 108.7 s.
- `voz_texto_correcto`: catálogo y recuperadores 38.9 s, LLM 9.6 s, ASR 28.3 s, TTS 30.6 s; total 108.7 s.
- `voz_velocidad_1_15`: catálogo y recuperadores 15.1 s, LLM 0.8 s, ASR 0.8 s, TTS 11.3 s; total 28.3 s.
- `voz_referencia_anterior`: catálogo y recuperadores 16.0 s, LLM 0.7 s, ASR 1.0 s, TTS 9.0 s; total 27.3 s.
- `voz_sintetica`: catálogo y recuperadores 16.3 s, LLM 0.7 s, ASR 1.1 s, TTS 10.1 s; total 28.8 s.
- `reserva`: catálogo y recuperadores 149.8 s, LLM 0.8 s; total 160.9 s.
- `reserva_cifras`: catálogo y recuperadores 16.2 s, LLM 0.8 s; total 27.3 s.
- `reserva_cifras_sage`: catálogo y recuperadores 16.2 s, LLM 0.7 s; total 17.2 s.
- `reserva_cifras_sin_reranker`: catálogo y recuperadores 151.6 s, LLM 0.7 s; total 152.7 s.
- `reserva_sage`: catálogo y recuperadores 152.3 s, LLM 0.8 s; total 153.4 s.
- `reserva_sin_reranker`: catálogo y recuperadores 20.8 s, LLM 0.7 s; total 21.9 s.

## Comprobaciones que fallaron

- `reserva` / [24_dato_que_no_consta](reserva/24_dato_que_no_consta.md):
  - turno 2: `declares_unknown` — dato en el catálogo: sí; la respuesta dice que no consta: sí
- `reserva_sin_reranker` / [24_dato_que_no_consta](reserva_sin_reranker/24_dato_que_no_consta.md):
  - turno 3: `declares_unknown` — dato en el catálogo: sí; la respuesta dice que no consta: sí
