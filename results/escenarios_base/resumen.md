# Evaluación con escenarios: resumen

Cada corrida tiene una ficha por escenario en su carpeta.

## Escenarios correctos por corrida

| Corrida | Entrada | Reranker | Escenarios | Correctos | % correctos |
|---|---|---|---|---|---|
| `texto` | texto | control | 20 | 14 | 70.0 % |
| `texto_sage` | texto | sage | 20 | 16 | 80.0 % |
| `texto_sin_reranker` | texto | sin reranker | 20 | 16 | 80.0 % |
| `voz` | audio | control | 6 | 3 | 50.0 % |
| `voz_texto_correcto` | texto | control | 6 | 3 | 50.0 % |

| Escenario | `texto` | `texto_sage` | `texto_sin_reranker` | `voz` | `voz_texto_correcto` |
|---|---|---|---|---|---|
| `01_compra_confirmada` | ✔ | ✔ | ✔ | ✔ | ✔ |
| `02_pedido_ambiguo` | ✔ | ✔ | ✔ | ✔ | ✔ |
| `03_cambio_cantidad` | ✘ | ✘ | ✘ | ✘ | ✘ |
| `04_sin_existencias` | ✘ | ✘ | ✘ | ✘ | ✘ |
| `05_correccion_transcripcion` | ✔ | ✔ | ✔ | ✔ | ✔ |
| `06_cambio_stock_confirmacion_repetida` | ✘ | ✘ | ✔ | ✘ | ✘ |
| `07_presupuesto_excedido` | ✔ | ✔ | ✔ |  |  |
| `08_cantidad_invalida` | ✔ | ✔ | ✔ |  |  |
| `09_producto_inexistente` | ✘ | ✘ | ✘ |  |  |
| `10_atributo_no_verificable` | ✘ | ✔ | ✘ |  |  |
| `11_rechazo_confirmacion` | ✔ | ✔ | ✔ |  |  |
| `12_memoria_preferencias` | ✔ | ✔ | ✔ |  |  |
| `13_confirmacion_con_cambio` | ✔ | ✔ | ✔ |  |  |
| `14_pregunta_sin_cambios` | ✔ | ✔ | ✔ |  |  |
| `15_stock_insuficiente` | ✔ | ✔ | ✔ |  |  |
| `16_quitar_del_carrito` | ✔ | ✔ | ✔ |  |  |
| `17_cambio_presupuesto` | ✔ | ✔ | ✔ |  |  |
| `18_cierre_sin_carrito` | ✔ | ✔ | ✔ |  |  |
| `19_presupuesto_compartido` | ✔ | ✔ | ✔ |  |  |
| `20_agotado_al_confirmar` | ✘ | ✔ | ✔ |  |  |

## Violaciones de restricciones

| Corrida | cantidad | presupuesto | existencias | pedido_duplicado | cambio_parcial |
|---|---|---|---|---|---|
| `texto` | 0 | 0 | 0 | 0 | 0 |
| `texto_sage` | 0 | 0 | 0 | 0 | 0 |
| `texto_sin_reranker` | 0 | 0 | 0 | 0 | 0 |
| `voz` | 0 | 0 | 0 | 0 | 0 |
| `voz_texto_correcto` | 0 | 0 | 0 | 0 | 0 |

## Voz

- Audios de entrada: sintéticos, hablante de prueba «Luis Moray» de XTTS-v2 (no es la voz del usuario).
- ASR: 31 turnos, 28 idénticos tras normalizar; WER 2.1 %.
- Errores del ASR en importes: 0 de 3 (0.0 %).
- Errores del ASR en cantidades: 0 de 8 (0.0 %).
- Errores del ASR en nombres de producto: 0 de 13 (0.0 %).
- Inteligibilidad de la voz generada (WER de Whisper sobre 31 respuestas): 3.8 %.
- Semejanza con la voz de referencia (coseno ECAPA): media 0.742, mínima 0.589.

## Audio frente a transcripción correcta

| Escenario | Con audio | Con el texto correcto | Turnos con palabras cambiadas por el ASR | Turnos con operaciones distintas | Misma tienda final |
|---|---|---|---|---|---|
| `01_compra_confirmada` | ✔ | ✔ | [2] | ninguno | sí |
| `02_pedido_ambiguo` | ✔ | ✔ | ninguno | [2] | sí |
| `03_cambio_cantidad` | ✘ | ✘ | ninguno | ninguno | sí |
| `04_sin_existencias` | ✘ | ✘ | [3] | ninguno | sí |
| `05_correccion_transcripcion` | ✔ | ✔ | ninguno | ninguno | sí |
| `06_cambio_stock_confirmacion_repetida` | ✘ | ✘ | [1] | [5] | no |

## Latencia por etapa (segundos por turno, media y máximo)

| Corrida | Turnos | ASR | Recuperación | LLM | Herramientas | TTS | Total |
|---|---|---|---|---|---|---|---|
| `texto`, con LLM | 74 | 0.00 (máx. 0.00) | 0.01 (máx. 0.03) | 5.38 (máx. 10.21) | 0.04 (máx. 0.08) | 0.00 (máx. 0.00) | 5.43 (máx. 10.27) |
| `texto`, sin LLM | 13 | 0.00 (máx. 0.00) | 0.00 (máx. 0.03) | 0.00 (máx. 0.00) | 0.02 (máx. 0.03) | 0.00 (máx. 0.00) | 0.03 (máx. 0.04) |
| `texto_sage`, con LLM | 76 | 0.00 (máx. 0.00) | 0.01 (máx. 0.06) | 5.24 (máx. 12.22) | 0.04 (máx. 0.07) | 0.00 (máx. 0.00) | 5.29 (máx. 12.24) |
| `texto_sage`, sin LLM | 11 | 0.00 (máx. 0.00) | 0.01 (máx. 0.03) | 0.00 (máx. 0.00) | 0.02 (máx. 0.03) | 0.00 (máx. 0.00) | 0.03 (máx. 0.04) |
| `texto_sin_reranker`, con LLM | 74 | 0.00 (máx. 0.00) | 0.01 (máx. 0.03) | 5.09 (máx. 9.57) | 0.04 (máx. 0.07) | 0.00 (máx. 0.00) | 5.13 (máx. 9.63) |
| `texto_sin_reranker`, sin LLM | 13 | 0.00 (máx. 0.00) | 0.00 (máx. 0.02) | 0.00 (máx. 0.00) | 0.03 (máx. 0.03) | 0.00 (máx. 0.00) | 0.03 (máx. 0.04) |
| `voz`, con LLM | 25 | 0.35 (máx. 0.54) | 0.01 (máx. 0.03) | 5.14 (máx. 9.76) | 0.04 (máx. 0.09) | 6.42 (máx. 17.33) | 11.96 (máx. 25.57) |
| `voz`, sin LLM | 6 | 0.33 (máx. 0.36) | 0.00 (máx. 0.03) | 0.00 (máx. 0.00) | 0.03 (máx. 0.04) | 5.22 (máx. 10.69) | 5.59 (máx. 11.05) |
| `voz_texto_correcto`, con LLM | 25 | 0.00 (máx. 0.00) | 0.01 (máx. 0.05) | 5.47 (máx. 9.72) | 0.04 (máx. 0.07) | 0.00 (máx. 0.00) | 5.51 (máx. 9.77) |
| `voz_texto_correcto`, sin LLM | 6 | 0.00 (máx. 0.00) | 0.00 (máx. 0.03) | 0.00 (máx. 0.00) | 0.02 (máx. 0.04) | 0.00 (máx. 0.00) | 0.03 (máx. 0.04) |

Carga inicial de los modelos, aparte de los turnos:

- `texto`: catálogo y recuperadores 16.4 s, LLM 0.8 s; total 17.6 s.
- `texto_sage`: catálogo y recuperadores 16.0 s, LLM 0.7 s; total 17.1 s.
- `texto_sin_reranker`: catálogo y recuperadores 151.6 s, LLM 0.8 s; total 152.7 s.
- `voz`: catálogo y recuperadores 16.2 s, LLM 0.8 s, ASR 1.0 s, TTS 8.8 s; total 27.4 s.
- `voz_texto_correcto`: catálogo y recuperadores 16.2 s, LLM 0.8 s, ASR 1.0 s, TTS 8.8 s; total 27.4 s.

## Comprobaciones que fallaron

- `texto` / [03_cambio_cantidad](texto/03_cambio_cantidad.md):
  - turno 4: `awaiting_confirmation` — esperando confirmación: no
  - turno 5: `orders` — pedidos registrados: 0
  - al final: `orders` — pedidos registrados: 0
  - al final: `order` — no hay ningún pedido
  - al final: `stock` — existencias de B07VQNY8PK: 20
  - al final: `cart` — carrito: 4 × B07VQNY8PK
- `texto` / [04_sin_existencias](texto/04_sin_existencias.md):
  - turno 2: `cart` — carrito: 1 × B09738BXB2
  - turno 3: `cart` — carrito: 2 × B09738BXB2
  - al final: `order` — pedido 1: 2 × B09738BXB2; total 3600 céntimos
- `texto` / [06_cambio_stock_confirmacion_repetida](texto/06_cambio_stock_confirmacion_repetida.md):
  - turno 5: `cart` — carrito: 1 × B07ZCY9XZ9
  - al final: `order` — pedido 1: 1 × B07ZCY9XZ9; total 2323 céntimos
  - al final: `stock` — existencias de B085CHJ9BD: 1
- `texto` / [09_producto_inexistente](texto/09_producto_inexistente.md):
  - turno 2: `cart` — carrito: 2 × B07TY4VMZ3
  - turno 3: `cart` — carrito: 2 × B07TY4VMZ3
  - al final: `cart` — carrito: 2 × B07TY4VMZ3
- `texto` / [10_atributo_no_verificable](texto/10_atributo_no_verificable.md):
  - turno 2: `declares_unknown` — dato en el catálogo: no; la respuesta dice que no consta: no
- `texto` / [20_agotado_al_confirmar](texto/20_agotado_al_confirmar.md):
  - turno 5: `cart` — carrito: 2 × B07XCPXLBW
- `texto_sage` / [03_cambio_cantidad](texto_sage/03_cambio_cantidad.md):
  - turno 4: `awaiting_confirmation` — esperando confirmación: no
  - turno 5: `orders` — pedidos registrados: 0
  - al final: `orders` — pedidos registrados: 0
  - al final: `order` — no hay ningún pedido
  - al final: `stock` — existencias de B07VQNY8PK: 20
  - al final: `cart` — carrito: 4 × B07VQNY8PK
- `texto_sage` / [04_sin_existencias](texto_sage/04_sin_existencias.md):
  - turno 2: `cart` — carrito: 1 × B09738BXB2
  - turno 3: `cart` — carrito: 2 × B09738BXB2
  - al final: `order` — pedido 1: 2 × B09738BXB2; total 3600 céntimos
- `texto_sage` / [06_cambio_stock_confirmacion_repetida](texto_sage/06_cambio_stock_confirmacion_repetida.md):
  - turno 5: `cart` — carrito: vacío
  - turno 6: `awaiting_confirmation` — esperando confirmación: no
  - turno 7: `orders` — pedidos registrados: 0
  - turno 8: `orders` — pedidos registrados: 0
  - al final: `orders` — pedidos registrados: 0
  - al final: `order` — no hay ningún pedido
  - al final: `stock` — existencias de B085CHJ9BD: 1
- `texto_sage` / [09_producto_inexistente](texto_sage/09_producto_inexistente.md):
  - turno 2: `cart` — carrito: 2 × B08YDXKTTQ
  - turno 3: `cart` — carrito: 2 × B08YDXKTTQ
  - al final: `cart` — carrito: 2 × B08YDXKTTQ
- `texto_sin_reranker` / [03_cambio_cantidad](texto_sin_reranker/03_cambio_cantidad.md):
  - turno 4: `awaiting_confirmation` — esperando confirmación: no
  - turno 5: `orders` — pedidos registrados: 0
  - al final: `orders` — pedidos registrados: 0
  - al final: `order` — no hay ningún pedido
  - al final: `stock` — existencias de B07VQNY8PK: 20
  - al final: `cart` — carrito: 4 × B07VQNY8PK
- `texto_sin_reranker` / [04_sin_existencias](texto_sin_reranker/04_sin_existencias.md):
  - turno 2: `cart` — carrito: 1 × B08GPGJY8M
  - turno 3: `cart` — carrito: 2 × B08GPGJY8M
  - al final: `order` — pedido 1: 2 × B08GPGJY8M; total 3600 céntimos
- `texto_sin_reranker` / [09_producto_inexistente](texto_sin_reranker/09_producto_inexistente.md):
  - turno 2: `cart` — carrito: 2 × B07QG82RGM
  - turno 3: `cart` — carrito: 2 × B07QG82RGM
  - al final: `cart` — carrito: 2 × B07QG82RGM
- `texto_sin_reranker` / [10_atributo_no_verificable](texto_sin_reranker/10_atributo_no_verificable.md):
  - turno 2: `declares_unknown` — dato en el catálogo: no; la respuesta dice que no consta: no
- `voz` / [03_cambio_cantidad](voz/03_cambio_cantidad.md):
  - turno 4: `awaiting_confirmation` — esperando confirmación: no
  - turno 5: `orders` — pedidos registrados: 0
  - al final: `orders` — pedidos registrados: 0
  - al final: `order` — no hay ningún pedido
  - al final: `stock` — existencias de B07VQNY8PK: 20
  - al final: `cart` — carrito: 4 × B07VQNY8PK
- `voz` / [04_sin_existencias](voz/04_sin_existencias.md):
  - turno 2: `cart` — carrito: 1 × B09738BXB2
  - turno 3: `cart` — carrito: 2 × B09738BXB2
  - al final: `order` — pedido 1: 2 × B09738BXB2; total 3600 céntimos
- `voz` / [06_cambio_stock_confirmacion_repetida](voz/06_cambio_stock_confirmacion_repetida.md):
  - turno 5: `cart` — carrito: 1 × B08NNZ6NC2
  - al final: `order` — pedido 1: 1 × B08NNZ6NC2; total 2386 céntimos
  - al final: `stock` — existencias de B085CHJ9BD: 1
- `voz_texto_correcto` / [03_cambio_cantidad](voz_texto_correcto/03_cambio_cantidad.md):
  - turno 4: `awaiting_confirmation` — esperando confirmación: no
  - turno 5: `orders` — pedidos registrados: 0
  - al final: `orders` — pedidos registrados: 0
  - al final: `order` — no hay ningún pedido
  - al final: `stock` — existencias de B07VQNY8PK: 20
  - al final: `cart` — carrito: 4 × B07VQNY8PK
- `voz_texto_correcto` / [04_sin_existencias](voz_texto_correcto/04_sin_existencias.md):
  - turno 2: `cart` — carrito: 1 × B09738BXB2
  - turno 3: `cart` — carrito: 2 × B09738BXB2
  - al final: `order` — pedido 1: 2 × B09738BXB2; total 3600 céntimos
- `voz_texto_correcto` / [06_cambio_stock_confirmacion_repetida](voz_texto_correcto/06_cambio_stock_confirmacion_repetida.md):
  - turno 5: `cart` — carrito: 1 × B07ZCY9XZ9
  - al final: `order` — pedido 1: 1 × B07ZCY9XZ9; total 2323 céntimos
  - al final: `stock` — existencias de B085CHJ9BD: 1
