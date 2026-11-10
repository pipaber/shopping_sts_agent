# Transcripción de una compra por voz

- Fecha: 2026-11-10T11:21:54
- Nota: La voz del agente se clona de la grabación de referencia del usuario. Los audios de entrada siguen siendo sintéticos (hablante «Luis Moray» incluido en XTTS-v2): todavía no hay grabaciones de los turnos.
- LLM: `qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf`; ASR: `large-v3-turbo`; TTS: `XTTS-v2`; embeddings: `intfloat/multilingual-e5-small`
- Voz del agente: clonada de la grabación de referencia `audio/referencia/referencia.wav`
- Carga inicial: catálogo y recuperadores 19.9 s, LLM 0.8 s, ASR 1.1 s, TTS 9.3 s; total 41.6 s
- VRAM del proceso: 9460 MiB con todo cargado, 9738 MiB al terminar la conversación
- Memoria del agente: postgres; hilo `voz-4ebd6f16`

## Latencia por turno (segundos)

| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total | Audio de respuesta |
|---|---|---|---|---|---|---|---|
| 1 | 0.84 | 0.04 | 10.46 | 0.04 | 8.44 | 19.84 | 35.4 s |
| 2 | 0.36 | 0.00 | 7.95 | 0.04 | 1.73 | 10.08 | 7.1 s |
| 3 | 0.37 | 0.00 | 8.29 | 0.03 | 6.52 | 15.20 | 26.1 s |
| 4 | 0.38 | 0.00 | 5.54 | 0.05 | 10.46 | 16.42 | 42.2 s |
| 5 | 0.36 | 0.00 | 5.68 | 0.04 | 8.39 | 14.48 | 35.0 s |
| 6 | 0.35 | 0.00 | 2.58 | 0.03 | 11.61 | 14.56 | 47.2 s |
| 7 | 0.33 | 0.00 | 0.00 | 0.03 | 5.79 | 6.15 | 22.7 s |
| 8 | 0.32 | 0.00 | 0.00 | 0.04 | 3.10 | 3.47 | 12.4 s |
| **Media de los turnos con LLM (6)** | 0.44 | 0.01 | 6.75 | 0.04 | 7.86 | 15.10 | |
| **Media de los turnos sin LLM (2)** | 0.33 | 0.00 | 0.00 | 0.03 | 4.45 | 4.81 | |

## Turno 1 (19.8 s)

**Usuario (transcripción del ASR):** Hola, busco unos auriculares Bluetooth para hacer deporte. Tengo un presupuesto de 60 euros.

**Texto correcto:** Hola, busco unos auriculares bluetooth para hacer deporte. Tengo un presupuesto de 60 euros.

- `fijar_presupuesto(importe_eur=60)` → OK: presupuesto fijado en 60,00 €.
- `buscar_productos(consulta="auriculares Bluetooth deporte")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B08K91F1M4 | LYCHL Auriculares Inalambricos Deportivos, Auriculares Bluetooth 5.0 Sport IP7 Impermeable Cascos Bluetooth In-Ear Auriculares Wireless Running con Mic, 100 Horas y Pantalla LED, Viajes, Deporte | marca: LYCHL | color: N…

**Agente:** Tengo varios modelos para ti. El primero son los de LYCHL por 4,85 euros, el segundo de Andfive por 45,70 euros, el tercero de bakibo por 26,79 euros, el cuarto de Bowost por 13,80 euros y el quinto también de bakibo por 13,16 euros. ¿Te interesa alguno? He anotado un presupuesto de 60,00 €.

**Enviado al TTS:** Tengo varios modelos para ti. El primero son los de LYCHL por cuatro euros con ochenta y cinco céntimos, el segundo de Andfive por cuarenta y cinco euros con setenta céntimos, el tercero de bakibo por veintiséis euros con setenta y nueve céntimos, el cuarto de Bowost por trece euros con ochenta céntimos y el quinto también de bakibo por trece euros con dieciséis céntimos. ¿Te interesa alguno? He anotado un presupuesto de sesenta euros.

## Turno 2 (10.1 s)

**Usuario (transcripción del ASR):** ¿De qué color es el segundo y cuánto le dura la batería?

- `consultar_precio_stock(product_id="B08VD6781Z")` → OK: precio 45,70 €; quedan 18 unidades. Esta herramienta no da características: para color, batería, medidas u otros datos del producto usa detalle_producto.
- `detalle_producto(product_id="B08VD6781Z")` → OK: [1] id=B08VD6781Z | Auriculares Inalambricos Deporte, Andfive Auriculares Bluetooth 5.1 con Microfono Cascos Inalambricos IP7 Impermeable, Carga Rápida USB-C, CVC8.0 Cancelación de Ruido Auriculares Running [Actualizado] | marca: andfive | color: Negro | precio: 45,70 € | existencias: 18 | caracterí…

**Agente:** El segundo auricular es de color Negro y tiene 42 horas de reproducción.

**Enviado al TTS:** El segundo auricular es de color Negro y tiene cuarenta y dos horas de reproducción.

## Turno 3 (15.2 s)

**Usuario (transcripción del ASR):** Compárame el primero con el tercero.

- `comparar(product_ids=["B08K91F1M4", "B08HLX41W1"])` → OK: [1] id=B08K91F1M4 | LYCHL Auriculares Inalambricos Deportivos, Auriculares Bluetooth 5.0 Sport IP7 Impermeable Cascos Bluetooth In-Ear Auriculares Wireless Running con Mic, 100 Horas y Pantalla LED, Viajes, Deporte | marca: LYCHL | color: Negro | precio: 4,85 € | existencias: 36 | características (e…

**Agente:** El primero, los auriculares de LYCHL, cuestan 4,85 euros y tienen 100 horas de reproducción. El tercero, de bakibo, son 26,79 euros y duran 30 horas. ¿Te interesa alguna opción?

**Enviado al TTS:** El primero, los auriculares de LYCHL, cuestan cuatro euros con ochenta y cinco céntimos y tienen cien horas de reproducción. El tercero, de bakibo, son veintiséis euros con setenta y nueve céntimos y duran treinta horas. ¿Te interesa alguna opción?

## Turno 4 (16.4 s)

**Usuario (transcripción del ASR):** Añade dos del primero al carrito.

- `agregar_al_carrito(product_id="B08K91F1M4", cantidad=2)` → OK: hecho. Así queda el carrito. CARRITO: - id=B08K91F1M4 | LYCHL Auriculares Inalambricos Deportivos, Auriculares Bluetooth 5.0… | 2 unidades × 4,85 € = 9,70 € | existencias: 36 Total del carrito: 9,70 €

**Agente:** Hecho, añadidas dos unidades. El total del carrito es 9,70 €. En el carrito hay 2 unidades de «LYCHL Auriculares Inalambricos Deportivos, Auriculares Bluetooth 5.0…» a 4,85 € cada una, 9,70 €. Total: 9,70 €. Tu presupuesto es de 60,00 € y te quedan 50,30 €.

**Enviado al TTS:** Hecho, añadidas dos unidades. El total del carrito es nueve euros con setenta céntimos. En el carrito hay dos unidades de LYCHL Auriculares Inalambricos Deportivos a cuatro euros con ochenta y cinco céntimos cada una, nueve euros con setenta céntimos. Total: nueve euros con setenta céntimos. Tu presupuesto es de sesenta euros y te quedan cincuenta euros con treinta céntimos.

## Turno 5 (14.5 s)

**Usuario (transcripción del ASR):** Mejor que sean tres.

- `cambiar_cantidad(product_id="B08K91F1M4", cantidad=3)` → OK: hecho. Así queda el carrito. CARRITO: - id=B08K91F1M4 | LYCHL Auriculares Inalambricos Deportivos, Auriculares Bluetooth 5.0… | 3 unidades × 4,85 € = 14,55 € | existencias: 36 Total del carrito: 14,55 €

**Agente:** Hecho, añadidas dos unidades más. El total del carrito es 14,55 €. En el carrito hay 3 unidades de «LYCHL Auriculares Inalambricos Deportivos, Auriculares Bluetooth 5.0…» a 4,85 € cada una, 14,55 €. Total: 14,55 €. Tu presupuesto es de 60,00 € y te quedan 45,45 €.

**Enviado al TTS:** Hecho, añadidas dos unidades más. El total del carrito es catorce euros con cincuenta y cinco céntimos. En el carrito hay tres unidades de LYCHL Auriculares Inalambricos Deportivos a cuatro euros con ochenta y cinco céntimos cada una, catorce euros con cincuenta y cinco céntimos. Total: catorce euros con cincuenta y cinco céntimos. Tu presupuesto es de sesenta euros y te quedan cuarenta y cinco euros con cuarenta y cinco céntimos.

## Turno 6 (14.6 s)

**Usuario (transcripción del ASR):** Vale, pues quiero cerrar el pedido.

- `cotizar()` → OK: cotización creada; falta la confirmación del usuario.

**Agente:** Te repito el pedido antes de registrarlo: 3 unidades de «LYCHL Auriculares Inalambricos Deportivos, Auriculares Bluetooth 5.0…» a 4,85 € cada una, 14,55 €. Total: 14,55 €. Tu presupuesto es de 60,00 € y te quedan 45,45 €. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar. *(esperando confirmación)*

**Enviado al TTS:** Te repito el pedido antes de registrarlo: tres unidades de LYCHL Auriculares Inalambricos Deportivos a cuatro euros con ochenta y cinco céntimos cada una, catorce euros con cincuenta y cinco céntimos. Total: catorce euros con cincuenta y cinco céntimos. Tu presupuesto es de sesenta euros y te quedan cuarenta y cinco euros con cuarenta y cinco céntimos. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar.

## Turno 7 (6.2 s)

**Usuario (transcripción del ASR):** Sí, confirmo.

- `confirmar_pedido(quote_id="01ce0d650a014b3c963d44f8e7cf02eb")` → OK: pedido registrado

**Agente:** Pedido número 1 registrado: 3 unidades de «LYCHL Auriculares Inalambricos Deportivos, Auriculares Bluetooth 5.0…» a 4,85 € cada una, 14,55 €. Total: 14,55 €. Gracias por tu compra.

**Enviado al TTS:** Pedido número uno registrado: tres unidades de LYCHL Auriculares Inalambricos Deportivos a cuatro euros con ochenta y cinco céntimos cada una, catorce euros con cincuenta y cinco céntimos. Total: catorce euros con cincuenta y cinco céntimos. Gracias por tu compra.

## Turno 8 (3.5 s)

**Usuario (transcripción del ASR):** Sí.

- `confirmar_pedido(quote_id="01ce0d650a014b3c963d44f8e7cf02eb")` → OK: el pedido ya estaba registrado; no se duplicó

**Agente:** Ese pedido ya estaba registrado con el número 1, así que no lo he duplicado. Total: 14,55 €.

**Enviado al TTS:** Ese pedido ya estaba registrado con el número uno, así que no lo he duplicado. Total: catorce euros con cincuenta y cinco céntimos.

## Estado final de la tienda

- Pedido 1: total 14,55 €
  - pedido 1: 3 × `B08K91F1M4` a 4,85 €
- Inventario `B08K91F1M4`: 36 → 33
- Líneas de carrito pendientes: 0
