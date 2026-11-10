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
| `reserva` | texto | control | 4 | 3 | 75.0 % |
| `reserva_sage` | texto | sage | 4 | 4 | 100.0 % |
| `reserva_sin_reranker` | texto | sin reranker | 4 | 3 | 75.0 % |

| Escenario | `texto` | `texto_sage` | `texto_sin_reranker` | `voz` | `voz_texto_correcto` | `reserva` | `reserva_sage` | `reserva_sin_reranker` |
|---|---|---|---|---|---|---|---|---|
| `01_compra_confirmada` | ✔ | ✔ | ✔ | ✔ | ✔ |  |  |  |
| `02_pedido_ambiguo` | ✔ | ✔ | ✔ | ✔ | ✔ |  |  |  |
| `03_cambio_cantidad` | ✔ | ✔ | ✔ | ✔ | ✔ |  |  |  |
| `04_sin_existencias` | ✔ | ✔ | ✔ | ✔ | ✔ |  |  |  |
| `05_correccion_transcripcion` | ✔ | ✔ | ✔ | ✔ | ✔ |  |  |  |
| `06_cambio_stock_confirmacion_repetida` | ✔ | ✔ | ✔ | ✔ | ✔ |  |  |  |
| `07_presupuesto_excedido` | ✔ | ✔ | ✔ |  |  |  |  |  |
| `08_cantidad_invalida` | ✔ | ✔ | ✔ |  |  |  |  |  |
| `09_producto_inexistente` | ✔ | ✔ | ✔ |  |  |  |  |  |
| `10_atributo_no_verificable` | ✔ | ✔ | ✔ |  |  |  |  |  |
| `11_rechazo_confirmacion` | ✔ | ✔ | ✔ |  |  |  |  |  |
| `12_memoria_preferencias` | ✔ | ✔ | ✔ |  |  |  |  |  |
| `13_confirmacion_con_cambio` | ✔ | ✔ | ✔ |  |  |  |  |  |
| `14_pregunta_sin_cambios` | ✔ | ✔ | ✔ |  |  |  |  |  |
| `15_stock_insuficiente` | ✔ | ✔ | ✔ |  |  |  |  |  |
| `16_quitar_del_carrito` | ✔ | ✔ | ✔ |  |  |  |  |  |
| `17_cambio_presupuesto` | ✔ | ✔ | ✔ |  |  |  |  |  |
| `18_cierre_sin_carrito` | ✔ | ✔ | ✔ |  |  |  |  |  |
| `19_presupuesto_compartido` | ✔ | ✔ | ✔ |  |  |  |  |  |
| `20_agotado_al_confirmar` | ✔ | ✔ | ✔ |  |  |  |  |  |
| `21_cierre_otras_palabras` |  |  |  |  |  | ✔ | ✔ | ✔ |
| `22_agotado_otro_candidato` |  |  |  |  |  | ✔ | ✔ | ✔ |
| `23_candidato_fuera_de_lista` |  |  |  |  |  | ✔ | ✔ | ✔ |
| `24_dato_que_no_consta` |  |  |  |  |  | ✘ | ✔ | ✘ |

## Antes y después de corregir el agente

Línea base: `results/escenarios_base`.

| Corrida | Antes | Después | Arreglados | Regresiones |
|---|---|---|---|---|
| `texto` | 14 de 20 | 20 de 20 | 03, 04, 06, 09, 10, 20 | ninguno |
| `texto_sage` | 16 de 20 | 20 de 20 | 03, 04, 06, 09 | ninguno |
| `texto_sin_reranker` | 16 de 20 | 20 de 20 | 03, 04, 09, 10 | ninguno |
| `voz` | 3 de 6 | 6 de 6 | 03, 04, 06 | ninguno |
| `voz_texto_correcto` | 3 de 6 | 6 de 6 | 03, 04, 06 | ninguno |

| Escenario (antes → después) | `texto` | `texto_sage` | `texto_sin_reranker` | `voz` | `voz_texto_correcto` |
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
| `reserva` | 0 | 0 | 0 | 0 | 0 |
| `reserva_sage` | 0 | 0 | 0 | 0 | 0 |
| `reserva_sin_reranker` | 0 | 0 | 0 | 0 | 0 |

## Voz

- Audios de entrada: sintéticos, hablante de prueba «Luis Moray» de XTTS-v2 (no es la voz del usuario).
- ASR: 31 turnos, 28 idénticos tras normalizar; WER 2.1 %.
- Errores del ASR en importes: 0 de 3 (0.0 %).
- Errores del ASR en cantidades: 0 de 8 (0.0 %).
- Errores del ASR en nombres de producto: 0 de 13 (0.0 %).
- Inteligibilidad de la voz generada (WER de Whisper sobre 31 respuestas): 3.9 %.
- Semejanza con la voz de referencia (coseno ECAPA): media 0.741, mínima 0.501.

## Audio frente a transcripción correcta

| Escenario | Con audio | Con el texto correcto | Turnos con palabras cambiadas por el ASR | Turnos con operaciones distintas | Misma tienda final |
|---|---|---|---|---|---|
| `01_compra_confirmada` | ✔ | ✔ | [2] | ninguno | sí |
| `02_pedido_ambiguo` | ✔ | ✔ | ninguno | [2] | sí |
| `03_cambio_cantidad` | ✔ | ✔ | ninguno | ninguno | sí |
| `04_sin_existencias` | ✔ | ✔ | [3] | ninguno | sí |
| `05_correccion_transcripcion` | ✔ | ✔ | ninguno | ninguno | sí |
| `06_cambio_stock_confirmacion_repetida` | ✔ | ✔ | [1] | ninguno | sí |

## Latencia por etapa (segundos por turno, media y máximo)

| Corrida | Turnos | ASR | Recuperación | LLM | Herramientas | TTS | Total |
|---|---|---|---|---|---|---|---|
| `texto`, con LLM | 73 | 0.00 (máx. 0.00) | 0.01 (máx. 0.03) | 5.04 (máx. 9.79) | 0.04 (máx. 0.08) | 0.00 (máx. 0.00) | 5.08 (máx. 9.86) |
| `texto`, sin LLM | 14 | 0.00 (máx. 0.00) | 0.00 (máx. 0.02) | 0.00 (máx. 0.00) | 0.03 (máx. 0.03) | 0.00 (máx. 0.00) | 0.03 (máx. 0.04) |
| `texto_sage`, con LLM | 73 | 0.00 (máx. 0.00) | 0.01 (máx. 0.04) | 4.99 (máx. 10.75) | 0.04 (máx. 0.07) | 0.00 (máx. 0.00) | 5.03 (máx. 10.83) |
| `texto_sage`, sin LLM | 14 | 0.00 (máx. 0.00) | 0.01 (máx. 0.04) | 0.00 (máx. 0.00) | 0.03 (máx. 0.03) | 0.00 (máx. 0.00) | 0.03 (máx. 0.06) |
| `texto_sin_reranker`, con LLM | 73 | 0.00 (máx. 0.00) | 0.01 (máx. 0.03) | 4.97 (máx. 9.42) | 0.04 (máx. 0.07) | 0.00 (máx. 0.00) | 5.02 (máx. 9.50) |
| `texto_sin_reranker`, sin LLM | 14 | 0.00 (máx. 0.00) | 0.00 (máx. 0.02) | 0.00 (máx. 0.00) | 0.03 (máx. 0.03) | 0.00 (máx. 0.00) | 0.03 (máx. 0.03) |
| `voz`, con LLM | 24 | 0.35 (máx. 0.56) | 0.01 (máx. 0.05) | 5.05 (máx. 9.84) | 0.04 (máx. 0.06) | 6.30 (máx. 11.85) | 11.75 (máx. 20.62) |
| `voz`, sin LLM | 7 | 0.32 (máx. 0.33) | 0.00 (máx. 0.03) | 0.00 (máx. 0.00) | 0.04 (máx. 0.04) | 4.46 (máx. 10.64) | 4.82 (máx. 11.01) |
| `voz_texto_correcto`, con LLM | 24 | 0.00 (máx. 0.00) | 0.01 (máx. 0.03) | 5.04 (máx. 8.93) | 0.04 (máx. 0.10) | 0.00 (máx. 0.00) | 5.09 (máx. 8.99) |
| `voz_texto_correcto`, sin LLM | 7 | 0.00 (máx. 0.00) | 0.00 (máx. 0.02) | 0.00 (máx. 0.00) | 0.03 (máx. 0.03) | 0.00 (máx. 0.00) | 0.03 (máx. 0.04) |
| `reserva`, con LLM | 15 | 0.00 (máx. 0.00) | 0.01 (máx. 0.03) | 4.96 (máx. 8.39) | 0.03 (máx. 0.05) | 0.00 (máx. 0.00) | 5.00 (máx. 8.45) |
| `reserva`, sin LLM | 3 | 0.00 (máx. 0.00) | 0.00 (máx. 0.00) | 0.00 (máx. 0.00) | 0.02 (máx. 0.03) | 0.00 (máx. 0.00) | 0.02 (máx. 0.03) |
| `reserva_sage`, con LLM | 15 | 0.00 (máx. 0.00) | 0.01 (máx. 0.04) | 4.94 (máx. 8.16) | 0.04 (máx. 0.06) | 0.00 (máx. 0.00) | 4.99 (máx. 8.24) |
| `reserva_sage`, sin LLM | 3 | 0.00 (máx. 0.00) | 0.00 (máx. 0.00) | 0.00 (máx. 0.00) | 0.03 (máx. 0.03) | 0.00 (máx. 0.00) | 0.03 (máx. 0.03) |
| `reserva_sin_reranker`, con LLM | 15 | 0.00 (máx. 0.00) | 0.01 (máx. 0.03) | 5.02 (máx. 8.45) | 0.04 (máx. 0.06) | 0.00 (máx. 0.00) | 5.07 (máx. 8.52) |
| `reserva_sin_reranker`, sin LLM | 3 | 0.00 (máx. 0.00) | 0.00 (máx. 0.00) | 0.00 (máx. 0.00) | 0.02 (máx. 0.03) | 0.00 (máx. 0.00) | 0.02 (máx. 0.03) |

Carga inicial de los modelos, aparte de los turnos:

- `texto`: catálogo y recuperadores 16.2 s, LLM 0.7 s; total 17.3 s.
- `texto_sage`: catálogo y recuperadores 149.8 s, LLM 0.8 s; total 150.9 s.
- `texto_sin_reranker`: catálogo y recuperadores 15.8 s, LLM 0.7 s; total 16.9 s.
- `voz`: catálogo y recuperadores 16.3 s, LLM 0.7 s, ASR 1.1 s, TTS 10.1 s; total 28.8 s.
- `voz_texto_correcto`: catálogo y recuperadores 16.3 s, LLM 0.7 s, ASR 1.1 s, TTS 10.1 s; total 28.8 s.
- `reserva`: catálogo y recuperadores 149.8 s, LLM 0.8 s; total 160.9 s.
- `reserva_sage`: catálogo y recuperadores 152.3 s, LLM 0.8 s; total 153.4 s.
- `reserva_sin_reranker`: catálogo y recuperadores 20.8 s, LLM 0.7 s; total 21.9 s.

## Comprobaciones que fallaron

- `reserva` / [24_dato_que_no_consta](reserva/24_dato_que_no_consta.md):
  - turno 2: `declares_unknown` — dato en el catálogo: sí; la respuesta dice que no consta: sí
- `reserva_sin_reranker` / [24_dato_que_no_consta](reserva_sin_reranker/24_dato_que_no_consta.md):
  - turno 3: `declares_unknown` — dato en el catálogo: sí; la respuesta dice que no consta: sí
