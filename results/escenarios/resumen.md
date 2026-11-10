# Evaluación con escenarios: resumen

Cada corrida tiene una ficha por escenario en su carpeta.

## Escenarios correctos por corrida

| Corrida | Entrada | Reranker | Escenarios | Correctos | % correctos |
|---|---|---|---|---|---|
| `texto` | texto | control | 20 | 15 | 75.0 % |

| Escenario | `texto` |
|---|---|
| `01_compra_confirmada` | ✔ |
| `02_pedido_ambiguo` | ✔ |
| `03_cambio_cantidad` | ✘ |
| `04_sin_existencias` | ✘ |
| `05_correccion_transcripcion` | ✔ |
| `06_cambio_stock_confirmacion_repetida` | ✘ |
| `07_presupuesto_excedido` | ✔ |
| `08_cantidad_invalida` | ✔ |
| `09_producto_inexistente` | ✔ |
| `10_atributo_no_verificable` | ✘ |
| `11_rechazo_confirmacion` | ✔ |
| `12_memoria_preferencias` | ✔ |
| `13_confirmacion_con_cambio` | ✔ |
| `14_pregunta_sin_cambios` | ✔ |
| `15_stock_insuficiente` | ✔ |
| `16_quitar_del_carrito` | ✔ |
| `17_cambio_presupuesto` | ✔ |
| `18_cierre_sin_carrito` | ✔ |
| `19_presupuesto_compartido` | ✔ |
| `20_agotado_al_confirmar` | ✘ |

## Violaciones de restricciones

| Corrida | cantidad | presupuesto | existencias | pedido_duplicado | cambio_parcial |
|---|---|---|---|---|---|
| `texto` | 0 | 0 | 0 | 0 | 0 |

## Latencia por etapa (segundos por turno, media y máximo)

| Corrida | Turnos | ASR | Recuperación | LLM | Herramientas | TTS | Total |
|---|---|---|---|---|---|---|---|
| `texto`, con LLM | 74 | 0.00 (máx. 0.00) | 0.01 (máx. 0.09) | 5.45 (máx. 10.50) | 0.04 (máx. 0.08) | 0.00 (máx. 0.00) | 5.50 (máx. 10.55) |
| `texto`, sin LLM | 13 | 0.00 (máx. 0.00) | 0.00 (máx. 0.03) | 0.00 (máx. 0.00) | 0.02 (máx. 0.04) | 0.00 (máx. 0.00) | 0.03 (máx. 0.04) |

Carga inicial de los modelos, aparte de los turnos:

- `texto`: catálogo y recuperadores 17.0 s, LLM 0.8 s; total 18.3 s.

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
- `texto` / [10_atributo_no_verificable](texto/10_atributo_no_verificable.md):
  - turno 2: `declares_unknown` — dato en el catálogo: no; la respuesta dice que no consta: no
- `texto` / [20_agotado_al_confirmar](texto/20_agotado_al_confirmar.md):
  - turno 5: `cart` — carrito: 2 × B07XCPXLBW
