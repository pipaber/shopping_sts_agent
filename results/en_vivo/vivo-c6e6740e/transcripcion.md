# Transcripción de una compra por voz

- Fecha: 2026-11-12T10:40:52
- Nota: conversación en vivo
- LLM: `qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf`; ASR: `large-v3-turbo`; TTS: `XTTS-v2`; embeddings: `intfloat/multilingual-e5-small`
- Voz del agente: clonada de la grabación de referencia `audio/referencia/referencia.wav`
- Carga inicial: catálogo y recuperadores 149.8 s, LLM 0.7 s, ASR 1.0 s, TTS 8.2 s; total 160.3 s
- VRAM del proceso: 9532 MiB con todo cargado, 9824 MiB al terminar la conversación
- Memoria del agente: postgres; hilo `vivo-c6e6740e`

## Latencia por turno (segundos)

| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total | Audio de respuesta |
|---|---|---|---|---|---|---|---|
| 1 | 0.58 | 0.03 | 9.37 | 0.03 | 7.80 | 17.82 | 34.4 s |
| 2 | 0.33 | 0.00 | 4.83 | 0.05 | 9.79 | 14.99 | 41.9 s |
| 3 | 0.32 | 0.00 | 4.91 | 0.06 | 5.73 | 11.02 | 25.4 s |
| 4 | 0.32 | 0.00 | 2.03 | 0.04 | 7.29 | 9.67 | 30.9 s |
| 5 | 0.31 | 0.00 | 0.00 | 0.04 | 4.76 | 5.12 | 20.9 s |
| **Media de los turnos con LLM (4)** | 0.39 | 0.01 | 5.29 | 0.04 | 7.65 | 13.38 | |
| **Media de los turnos sin LLM (1)** | 0.31 | 0.00 | 0.00 | 0.04 | 4.76 | 5.12 | |

## Turno 1 (17.8 s)

**Usuario (transcripción del ASR):** Busco una botella de agua de acero inoxidable. Mi presupuesto es de 45 euros.

- `fijar_presupuesto(importe_eur=45)` → OK: presupuesto fijado en 45,00 €.
- `buscar_productos(consulta="botella de agua acero inoxidable")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B07VQNY8PK | Newdora Botella de Agua Acero Inoxidable 500ml, Aislamiento de Vacío de Doble Pared, Botellas de Frío/Caliente, con 1 un Cepillo de Limpieza, para Niños, Deporte, Oficina, Gimnasio, Ciclismo, Negro | marca: Newdora | col…

**Agente:** Tengo la botella de agua de Newdora por 6,72 euros, la de KOSAD por 12,37, la de KOUAJ por 18,29 y las de ion8 por 4,97 y 10,79 euros. ¿Te interesa alguna? He anotado un presupuesto de 45,00 €.

**Enviado al TTS:** Tengo la botella de agua de Newdora por seis euros con setenta y dos céntimos, la de KOSAD por doce coma treinta y siete, la de KOUAJ por dieciocho coma veintinueve y las de ion8 por cuatro coma noventa y siete y diez euros con setenta y nueve céntimos. ¿Te interesa alguna? He anotado un presupuesto de cuarenta y cinco euros.

## Turno 2 (15.0 s)

**Usuario (transcripción del ASR):** Añade dos de la primera.

- `agregar_al_carrito(product_id="B07VQNY8PK", cantidad=2)` → OK: hecho. Así queda el carrito. CARRITO: - id=B07VQNY8PK | Newdora Botella de Agua Acero Inoxidable 500ml, Aislamiento de Vacío… | 2 unidades × 9,50 € = 19,00 € | existencias: 20 Total del carrito: 19,00 €

**Agente:** Hecho, añadidas dos unidades. El total es 19,00 €. En el carrito hay 2 unidades de «Newdora Botella de Agua Acero Inoxidable 500ml, Aislamiento de Vacío…» a 9,50 € cada una, 19,00 €. Total: 19,00 €. Tu presupuesto es de 45,00 € y te quedan 26,00 €.

**Enviado al TTS:** Hecho, añadidas dos unidades. El total es diecinueve euros. En el carrito hay dos unidades de Newdora Botella de Agua Acero Inoxidable quinientos mililitros a nueve euros con cincuenta céntimos cada una, diecinueve euros. Total: diecinueve euros. Tu presupuesto es de cuarenta y cinco euros y te quedan veintiséis euros.

## Turno 3 (11.0 s)

**Usuario (transcripción del ASR):** Mejor que sean cuatro.

- `cambiar_cantidad(product_id="B07VQNY8PK", cantidad=4)` → OK: hecho. Así queda el carrito. CARRITO: - id=B07VQNY8PK | Newdora Botella de Agua Acero Inoxidable 500ml, Aislamiento de Vacío… | 4 unidades × 9,50 € = 38,00 € | existencias: 20 Total del carrito: 38,00 €

**Agente:** Hecho, el total es 38,00 €. En el carrito hay 4 unidades de «Newdora Botella de Agua Acero Inoxidable 500ml, Aislamiento de Vacío…» a 9,50 € cada una, 38,00 €. Total: 38,00 €. Tu presupuesto es de 45,00 € y te quedan 7,00 €.

**Enviado al TTS:** Hecho, el total es treinta y ocho euros. En el carrito hay cuatro unidades de Newdora Botella de Agua Acero Inoxidable quinientos mililitros a nueve euros con cincuenta céntimos cada una, treinta y ocho euros. Total: treinta y ocho euros. Tu presupuesto es de cuarenta y cinco euros y te quedan siete euros.

## Turno 4 (9.7 s)

**Usuario (transcripción del ASR):** Cierralo.

- `cotizar()` → OK: cotización creada; falta la confirmación del usuario.

**Agente:** Te repito el pedido antes de registrarlo: 4 unidades de «Newdora Botella de Agua Acero Inoxidable 500ml, Aislamiento de Vacío…» a 9,50 € cada una, 38,00 €. Total: 38,00 €. Tu presupuesto es de 45,00 € y te quedan 7,00 €. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar. *(esperando confirmación)*

**Enviado al TTS:** Te repito el pedido antes de registrarlo: cuatro unidades de Newdora Botella de Agua Acero Inoxidable quinientos mililitros a nueve euros con cincuenta céntimos cada una, treinta y ocho euros. Total: treinta y ocho euros. Tu presupuesto es de cuarenta y cinco euros y te quedan siete euros. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar.

## Turno 5 (5.1 s)

**Usuario (transcripción del ASR):** Sí.

- `confirmar_pedido(quote_id="ef244fd60b194062bc8e230b32c82ed5")` → OK: pedido registrado

**Agente:** Pedido número 1 registrado: 4 unidades de «Newdora Botella de Agua Acero Inoxidable 500ml, Aislamiento de Vacío…» a 9,50 € cada una, 38,00 €. Total: 38,00 €. Gracias por tu compra.

**Enviado al TTS:** Pedido número uno registrado: cuatro unidades de Newdora Botella de Agua Acero Inoxidable quinientos mililitros a nueve euros con cincuenta céntimos cada una, treinta y ocho euros. Total: treinta y ocho euros. Gracias por tu compra.

## Estado final de la tienda

- Pedido 1: total 38,00 €
  - pedido 1: 4 × `B07VQNY8PK` a 9,50 €
- Inventario `B07VQNY8PK`: 46 → 16
- Líneas de carrito pendientes: 0
