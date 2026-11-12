# Transcripción de una compra por voz

- Fecha: 2026-11-12T10:41:51
- Nota: conversación en vivo
- LLM: `qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf`; ASR: `large-v3-turbo`; TTS: `XTTS-v2`; embeddings: `intfloat/multilingual-e5-small`
- Voz del agente: clonada de la grabación de referencia `audio/referencia/referencia.wav`
- Carga inicial: catálogo y recuperadores 149.8 s, LLM 0.7 s, ASR 1.0 s, TTS 8.2 s; total 160.3 s
- VRAM del proceso: 9532 MiB con todo cargado, 9824 MiB al terminar la conversación
- Memoria del agente: postgres; hilo `vivo-b2a21e1c`

## Latencia por turno (segundos)

| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total | Audio de respuesta |
|---|---|---|---|---|---|---|---|
| 1 | 0.01 | 0.00 | 0.00 | 0.00 | 1.12 | 1.13 | 5.1 s |
| 2 | 0.01 | 0.00 | 0.00 | 0.00 | 1.11 | 1.12 | 5.1 s |
| 3 | 0.00 | 0.03 | 6.90 | 0.03 | 6.50 | 13.46 | 28.1 s |
| 4 | 0.00 | 0.00 | 2.80 | 0.03 | 0.80 | 3.62 | 3.6 s |
| 5 | 0.00 | 0.00 | 2.40 | 0.03 | 1.03 | 3.47 | 4.7 s |
| 6 | 0.00 | 0.00 | 4.45 | 0.03 | 1.43 | 5.91 | 6.4 s |
| **Media de los turnos con LLM (4)** | 0.00 | 0.01 | 4.14 | 0.03 | 2.44 | 6.61 | |
| **Media de los turnos sin LLM (2)** | 0.01 | 0.00 | 0.00 | 0.00 | 1.12 | 1.12 | |

## Turno 1 (1.1 s)

**Usuario (transcripción del ASR):** 

**Agente:** No te he oído bien. ¿Puedes repetirlo?

**Enviado al TTS:** No te he oído bien. ¿Puedes repetirlo?

## Turno 2 (1.1 s)

**Usuario (transcripción del ASR):** 

**Agente:** No te he oído bien. ¿Puedes repetirlo?

**Enviado al TTS:** No te he oído bien. ¿Puedes repetirlo?

## Turno 3 (13.5 s)

**Usuario (texto):** Hola, busco una taza de cerámica.

- `buscar_productos(consulta="taza cerámica")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B082DCGNR3 | zhqingyu Figura Abstracta Creativa - Bicicleta Amor Taza Gran Capacidad Personalidad Creativa Tendencia Taza de cerámica hogar con Tapa Taza de Regalo Femenina | marca: zhqingyu | color: desconocido | precio: 7,70 € | ex…

**Agente:** Tengo una taza de cerámica de zhqingyu por 7,70 euros, una de View Show por 117,22 euros, una de AmyNovelty por 24,63 euros, una de AN por 7,48 euros y una de DrMugCollection por 32,09 euros. ¿Te interesa alguna?

**Enviado al TTS:** Tengo una taza de cerámica de zhqingyu por siete euros con setenta céntimos, una de View Show por ciento diecisiete euros con veintidós céntimos, una de AmyNovelty por veinticuatro euros con sesenta y tres céntimos, una de AN por siete euros con cuarenta y ocho céntimos y una de DrMugCollection por treinta y dos euros con nueve céntimos. ¿Te interesa alguna?

## Turno 4 (3.6 s)

**Usuario (texto):** ¿Cuánto cuesta la primera?

**Agente:** Cuesta 7,70 euros.

**Enviado al TTS:** Cuesta siete euros con setenta céntimos.

## Turno 5 (3.5 s)

**Usuario (texto):** ¿Qué hay en el carrito?

**Agente:** El carrito está vacío.

**Enviado al TTS:** El carrito está vacío.

## Turno 6 (5.9 s)

**Usuario (texto):** ¿Cuál es mi presupuesto?

- `consultar_precio_stock(product_id="B082DCGNR3")` → OK: precio 7,70 €; quedan 17 unidades. Esta herramienta no da características: para color, batería, medidas u otros datos del producto usa detalle_producto.

**Agente:** La primera taza cuesta 7,70 euros.

**Enviado al TTS:** La primera taza cuesta siete euros con setenta céntimos.

## Estado final de la tienda

- Líneas de carrito pendientes: 0
