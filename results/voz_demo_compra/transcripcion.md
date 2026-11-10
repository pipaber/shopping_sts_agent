# Transcripción de una compra por voz

- Fecha: 2026-11-10T14:58:05
- Nota: Prueba de flujo, no evaluación: los audios de entrada y la voz de referencia son sintéticos (hablantes incluidos en XTTS-v2: «Luis Moray» para el usuario y «Alma María» para la referencia que clona el agente).
- LLM: `qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf`; ASR: `large-v3-turbo`; TTS: `XTTS-v2`; embeddings: `intfloat/multilingual-e5-small`
- Voz del agente: clonada de la grabación de referencia `audio/sinteticos/referencia_prueba.wav`
- Carga inicial: catálogo y recuperadores 16.3 s, LLM 0.7 s, ASR 1.0 s, TTS 8.0 s; total 26.6 s
- VRAM del proceso: 9532 MiB con todo cargado, 9808 MiB al terminar la conversación
- Memoria del agente: postgres; hilo `voz-cd0be185`

## Latencia por turno (segundos)

| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total | Audio de respuesta |
|---|---|---|---|---|---|---|---|
| 1 | 0.59 | 0.04 | 10.69 | 0.04 | 6.03 | 17.39 | 25.8 s |
| 2 | 0.40 | 0.00 | 8.54 | 0.03 | 2.69 | 11.67 | 11.0 s |
| 3 | 0.34 | 0.00 | 8.83 | 0.03 | 5.72 | 14.93 | 24.5 s |
| 4 | 0.34 | 0.00 | 5.47 | 0.05 | 6.54 | 12.40 | 27.9 s |
| 5 | 0.33 | 0.00 | 5.53 | 0.05 | 6.78 | 12.69 | 27.6 s |
| 6 | 0.34 | 0.00 | 2.69 | 0.04 | 6.28 | 9.36 | 25.8 s |
| 7 | 0.34 | 0.00 | 0.00 | 0.04 | 3.87 | 4.25 | 15.8 s |
| 8 | 0.33 | 0.00 | 0.00 | 0.04 | 2.03 | 2.39 | 8.3 s |
| **Media de los turnos con LLM (6)** | 0.39 | 0.01 | 6.96 | 0.04 | 5.67 | 13.07 | |
| **Media de los turnos sin LLM (2)** | 0.33 | 0.00 | 0.00 | 0.04 | 2.95 | 3.32 | |

## Turno 1 (17.4 s)

**Usuario (transcripción del ASR):** Hola, busco unos auriculares Bluetooth para hacer deporte. Tengo un presupuesto de 60 euros.

**Texto correcto:** Hola, busco unos auriculares bluetooth para hacer deporte. Tengo un presupuesto de 60 euros.

- `fijar_presupuesto(importe_eur=60)` → OK: presupuesto fijado en 60,00 €.
- `buscar_productos(consulta="auriculares Bluetooth deporte")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B08K91F1M4 | LYCHL Auriculares Inalambricos Deportivos, Auriculares Bluetooth 5.0 Sport IP7 Impermeable Cascos Bluetooth In-Ear Auriculares Wireless Running con Mic, 100 Horas y Pantalla LED, Viajes, Deporte | marca: LYCHL | color: N…

**Agente:** Tengo varios modelos para ti. El primero son los de LYCHL por 4,85 euros, el segundo de Bowost por 13,80 euros, el tercero de andfive por 45,70 euros, el cuarto de bakibo por 26,79 euros y el quinto de Tronsmart por 8,32 euros. ¿Te interesa alguno? He anotado un presupuesto de 60,00 €.

**Enviado al TTS:** Tengo varios modelos para ti. El primero son los de LYCHL por cuatro euros con ochenta y cinco céntimos, el segundo de Bowost por trece euros con ochenta céntimos, el tercero de andfive por cuarenta y cinco euros con setenta céntimos, el cuarto de bakibo por veintiséis euros con setenta y nueve céntimos y el quinto de Tronsmart por ocho euros con treinta y dos céntimos. ¿Te interesa alguno? He anotado un presupuesto de sesenta euros.

## Turno 2 (11.7 s)

**Usuario (transcripción del ASR):** ¿De qué color es el segundo y cuánto le dura la batería?

- `consultar_precio_stock(product_id="B09CD97CVT")` → OK: precio 13,80 €; quedan 21 unidades. Esta herramienta no da características: para color, batería, medidas u otros datos del producto usa detalle_producto.
- `detalle_producto(product_id="B09CD97CVT")` → OK: [1] id=B09CD97CVT | Auriculares Inalámbricos Deportivos, Auriculares Bluetooth 5.1 Deporte IPX7 Impermeable Cascos Inalámbricos con Mic 48H Estéreo Cancelación de Ruido In-Ear Auriculares Running/Sport-2021 Actualizado | marca: Bowost | color: Negro | precio: 13,80 € | existencias: 21 | característi…

**Agente:** El segundo auricular es de la marca Bowost, en color negro. Su batería dura hasta 48 horas con una sola carga. ¿Necesitas más información?

**Enviado al TTS:** El segundo auricular es de la marca Bowost, en color negro. Su batería dura hasta cuarenta y ocho horas con una sola carga. ¿Necesitas más información?

## Turno 3 (14.9 s)

**Usuario (transcripción del ASR):** Compárame el primero con el tercero.

- `comparar(product_ids=["B08K91F1M4", "B08VD6781Z"])` → OK: [1] id=B08K91F1M4 | LYCHL Auriculares Inalambricos Deportivos, Auriculares Bluetooth 5.0 Sport IP7 Impermeable Cascos Bluetooth In-Ear Auriculares Wireless Running con Mic, 100 Horas y Pantalla LED, Viajes, Deporte | marca: LYCHL | color: Negro | precio: 4,85 € | existencias: 36 | características (e…

**Agente:** El primero, de LYCHL, cuesta 4,85 euros y el tercero, de Andfive, 45,70 euros. El primero tiene una conexión más rápida y un chip Bluetooth 5.0, mientras que el tercero ofrece una tecnología Bluetooth 5.1 más avanzada y una carga rápida USB-C. ¿Te interesa alguna de estas opciones?

**Enviado al TTS:** El primero, de LYCHL, cuesta cuatro euros con ochenta y cinco céntimos y el tercero, de Andfive, cuarenta y cinco euros con setenta céntimos. El primero tiene una conexión más rápida y un chip Bluetooth cinco punto cero, mientras que el tercero ofrece una tecnología Bluetooth cinco punto uno más avanzada y una carga rápida USB-C. ¿Te interesa alguna de estas opciones?

## Turno 4 (12.4 s)

**Usuario (transcripción del ASR):** Añade dos del primero al carrito.

- `agregar_al_carrito(product_id="B08K91F1M4", cantidad=2)` → OK: hecho. Así queda el carrito. CARRITO: - id=B08K91F1M4 | LYCHL Auriculares Inalambricos Deportivos, Auriculares Bluetooth 5.0… | 2 unidades × 4,85 € = 9,70 € | existencias: 36 Total del carrito: 9,70 €

**Agente:** Hecho, añadidas dos unidades. El total del carrito es 9,70 €. En el carrito hay 2 unidades de «LYCHL Auriculares Inalambricos Deportivos, Auriculares Bluetooth 5.0…» a 4,85 € cada una, 9,70 €. Total: 9,70 €. Tu presupuesto es de 60,00 € y te quedan 50,30 €.

**Enviado al TTS:** Hecho, añadidas dos unidades. El total del carrito es nueve euros con setenta céntimos. En el carrito hay dos unidades de LYCHL Auriculares Inalambricos Deportivos a cuatro euros con ochenta y cinco céntimos cada una, nueve euros con setenta céntimos. Total: nueve euros con setenta céntimos. Tu presupuesto es de sesenta euros y te quedan cincuenta euros con treinta céntimos.

## Turno 5 (12.7 s)

**Usuario (transcripción del ASR):** Mejor que sean tres.

- `cambiar_cantidad(product_id="B08K91F1M4", cantidad=3)` → OK: hecho. Así queda el carrito. CARRITO: - id=B08K91F1M4 | LYCHL Auriculares Inalambricos Deportivos, Auriculares Bluetooth 5.0… | 3 unidades × 4,85 € = 14,55 € | existencias: 36 Total del carrito: 14,55 €

**Agente:** Hecho, añadidas dos unidades más. Ahora tienes 3 unidades en el carrito. En el carrito hay 3 unidades de «LYCHL Auriculares Inalambricos Deportivos, Auriculares Bluetooth 5.0…» a 4,85 € cada una, 14,55 €. Total: 14,55 €. Tu presupuesto es de 60,00 € y te quedan 45,45 €.

**Enviado al TTS:** Hecho, añadidas dos unidades más. Ahora tienes tres unidades en el carrito. En el carrito hay tres unidades de LYCHL Auriculares Inalambricos Deportivos a cuatro euros con ochenta y cinco céntimos cada una, catorce euros con cincuenta y cinco céntimos. Total: catorce euros con cincuenta y cinco céntimos. Tu presupuesto es de sesenta euros y te quedan cuarenta y cinco euros con cuarenta y cinco céntimos.

## Turno 6 (9.4 s)

**Usuario (transcripción del ASR):** Vale, pues quiero cerrar el pedido.

- `cotizar()` → OK: cotización creada; falta la confirmación del usuario.

**Agente:** Te repito el pedido antes de registrarlo: 3 unidades de «LYCHL Auriculares Inalambricos Deportivos, Auriculares Bluetooth 5.0…» a 4,85 € cada una, 14,55 €. Total: 14,55 €. Tu presupuesto es de 60,00 € y te quedan 45,45 €. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar. *(esperando confirmación)*

**Enviado al TTS:** Te repito el pedido antes de registrarlo: tres unidades de LYCHL Auriculares Inalambricos Deportivos a cuatro euros con ochenta y cinco céntimos cada una, catorce euros con cincuenta y cinco céntimos. Total: catorce euros con cincuenta y cinco céntimos. Tu presupuesto es de sesenta euros y te quedan cuarenta y cinco euros con cuarenta y cinco céntimos. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar.

## Turno 7 (4.2 s)

**Usuario (transcripción del ASR):** Sí, confirmo.

- `confirmar_pedido(quote_id="d691792558c244a29dc7221ec9cc1940")` → OK: pedido registrado

**Agente:** Pedido número 1 registrado: 3 unidades de «LYCHL Auriculares Inalambricos Deportivos, Auriculares Bluetooth 5.0…» a 4,85 € cada una, 14,55 €. Total: 14,55 €. Gracias por tu compra.

**Enviado al TTS:** Pedido número uno registrado: tres unidades de LYCHL Auriculares Inalambricos Deportivos a cuatro euros con ochenta y cinco céntimos cada una, catorce euros con cincuenta y cinco céntimos. Total: catorce euros con cincuenta y cinco céntimos. Gracias por tu compra.

## Turno 8 (2.4 s)

**Usuario (transcripción del ASR):** Sí.

- `confirmar_pedido(quote_id="d691792558c244a29dc7221ec9cc1940")` → OK: el pedido ya estaba registrado; no se duplicó

**Agente:** Ese pedido ya estaba registrado con el número 1, así que no lo he duplicado. Total: 14,55 €.

**Enviado al TTS:** Ese pedido ya estaba registrado con el número uno, así que no lo he duplicado. Total: catorce euros con cincuenta y cinco céntimos.

## Estado final de la tienda

- Pedido 1: total 14,55 €
  - pedido 1: 3 × `B08K91F1M4` a 4,85 €
- Inventario `B08K91F1M4`: 36 → 33
- Líneas de carrito pendientes: 0

## Misma conversación con las transcripciones correctas

- Turnos en los que el ASR cambió alguna palabra: ninguno
- Turnos en los que solo cambió la forma de escribirlo (mayúsculas, puntuación, cifras): [1]
- Turnos en los que el agente hizo operaciones distintas: [1]
- Estado final de la tienda igual que con audio: sí
