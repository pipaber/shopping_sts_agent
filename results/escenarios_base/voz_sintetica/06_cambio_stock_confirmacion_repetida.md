# 06_cambio_stock_confirmacion_repetida — Cambio de stock entre cotización y confirmación, y confirmación repetida

- Veredicto: **fallo**
- Entrada: audio (sintéticos, hablante de prueba «Luis Moray» de XTTS-v2 (no es la voz del usuario))
- Tipo: `cambio_stock_confirmacion_repetida`
- Qué se prueba: Con la cotización de tres unidades pendiente, la tienda se queda con una sola. La confirmación debe rechazarse sin tocar nada y ofrecer una salida. El usuario lo deja en una unidad, confirma y repite el sí: debe haber un único pedido.

## Turno 1 (15.3 s)

**Usuario (transcripción del ASR):** Busco una lámpara de escritorio LED. Lo.

**Texto correcto:** Busco una lámpara de escritorio LED.

- `buscar_productos(consulta="lámpara escritorio LED")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B085CHJ9BD | Lámpara Escritorio LED, Flexo de Escritorio, La luz natural protege los ojos, Lampara led Escritorio regulable con puerto de carga USB, 5 Modos, 10 Niveles de Brillo,Temporizador de 30/60min | marca: SLATOR | color: Negr…

**Agente:** Tengo la lámpara de escritorio LED SLATOR por 44,20 €, la SENXINGYAN por 36,61 €, la SOFIL por 38,74 €, la Prtukyt por 23,86 € y la HyAdierTech por 11,87 €. ¿Te interesa alguna?

**Enviado al TTS:** Tengo la lámpara de escritorio LED SLATOR por cuarenta y cuatro euros con veinte céntimos, la SENXINGYAN por treinta y seis euros con sesenta y un céntimos, la SOFIL por treinta y ocho euros con setenta y cuatro céntimos, la Prtukyt por veintitrés euros con ochenta y seis céntimos y la HyAdierTech por once euros con ochenta y siete céntimos. ¿Te interesa alguna?

- ✔ `cart(empty=true)` — carrito: vacío

> `@elegida` = `B085CHJ9BD` (candidate:1): Lámpara Escritorio LED, Flexo de Escritorio, La luz natural protege los ojos, Lampara led Escritorio regulable con puerto de carga USB, 5 Modos, 10 Niveles de Brillo,Temporizador de 30/60min

> **Suceso externo:** la tienda deja `B085CHJ9BD` (@elegida) con precio 15,00 € y existencias 10.

## Turno 2 (10.3 s)

**Usuario (transcripción del ASR):** Añade 3 de la primera.

**Texto correcto:** Añade tres de la primera.

- `agregar_al_carrito(product_id="B085CHJ9BD", cantidad=3)` → OK: hecho. Así queda el carrito. CARRITO: - id=B085CHJ9BD | Lámpara Escritorio LED, Flexo de Escritorio, La luz natural protege… | 3 unidades × 15,00 € = 45,00 € | existencias: 10 Total del carrito: 45,00 €

**Agente:** Hecho, añadidas tres unidades. El total es 45,00 €. En el carrito hay 3 unidades de «Lámpara Escritorio LED, Flexo de Escritorio, La luz natural protege…» a 15,00 € cada una, 45,00 €. Total: 45,00 €.

**Enviado al TTS:** Hecho, añadidas tres unidades. El total es cuarenta y cinco euros. En el carrito hay tres unidades de Lámpara Escritorio LED a quince euros cada una, cuarenta y cinco euros. Total: cuarenta y cinco euros.

- ✔ `cart(lines=[{"product": "@elegida", "quantity": 3}])` — carrito: 3 × B085CHJ9BD

## Turno 3 (7.7 s)

**Usuario (transcripción del ASR):** Quiero cerrar el pedido.

- `cotizar()` → OK: cotización creada; falta la confirmación del usuario.

**Agente:** Te repito el pedido antes de registrarlo: 3 unidades de «Lámpara Escritorio LED, Flexo de Escritorio, La luz natural protege…» a 15,00 € cada una, 45,00 €. Total: 45,00 €. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar. *(esperando confirmación)*

**Enviado al TTS:** Te repito el pedido antes de registrarlo: tres unidades de Lámpara Escritorio LED a quince euros cada una, cuarenta y cinco euros. Total: cuarenta y cinco euros. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar.

- ✔ `awaiting_confirmation(value=true)` — esperando confirmación: sí
- ✔ `orders(count=0)` — pedidos registrados: 0

> **Suceso externo:** la tienda deja `B085CHJ9BD` (@elegida) con existencias 1.

## Turno 4 (11.1 s)

**Usuario (transcripción del ASR):** Sí.

- `confirmar_pedido(quote_id="f2beccb7f47544c9b6448d685da1e91b")` → RECHAZADO: [stock_insuficiente] Solo queda 1 unidad del producto B085CHJ9BD y se pidieron 3.

**Agente:** No he registrado el pedido porque la tienda cambió después de la cotización. De «Lámpara Escritorio LED, Flexo de Escritorio, La luz natural protege…» solo queda 1 unidad y habías pedido 3. Puedo dejarlo en 1. Como alternativa tengo: «Lámpara Escritorio LED, Flexo de Escritorio (Cuidado Ocular, Puerto…» a 23,23 €, con 16 en existencias; «Lámpara Escritorio LED,JUKSTG 5 Modos 10 Niveles de Brillo Lámpara de…» a 34,86 €, con 25 en existencias; «Lámpara de escritorio LED Lámpara de lectura de brazo Eye-Care…» a 23,86 €, con 34 en existencias. ¿Qué prefieres?

**Enviado al TTS:** No he registrado el pedido porque la tienda cambió después de la cotización. De Lámpara Escritorio LED solo queda una unidad y habías pedido tres. Puedo dejarlo en uno. Como alternativa tengo: Lámpara Escritorio LED a veintitrés euros con veintitrés céntimos, con dieciséis en existencias, Lámpara Escritorio LED a treinta y cuatro euros con ochenta y seis céntimos, con veinticinco en existencias, Lámpara de escritorio LED Lámpara de lectura a veintitrés euros con ochenta y seis céntimos, con treinta y cuatro en existencias. ¿Qué prefieres?

- ✔ `orders(count=0)` — pedidos registrados: 0
- ✔ `rejected(code="stock_insuficiente")` — rechazos del turno: ['stock_insuficiente']
- ✔ `cart(lines=[{"product": "@elegida", "quantity": 3}])` — carrito: 3 × B085CHJ9BD
- ✔ `stock(product="@elegida", equals=1)` — existencias de B085CHJ9BD: 1

## Turno 5 (12.2 s)

**Usuario (transcripción del ASR):** Vale, déjalo en una.

- `quitar_del_carrito(product_id="B085CHJ9BD")` → OK: hecho. Así queda el carrito. CARRITO: vacío
- `agregar_al_carrito(product_id="B08NNZ6NC2", cantidad=1)` → OK: hecho. Así queda el carrito. CARRITO: - id=B08NNZ6NC2 | Lámpara de escritorio LED Lámpara de lectura de brazo Eye-Care… | 1 unidad × 23,86 € = 23,86 € | existencias: 34 Total del carrito: 23,86 €
- `cotizar()` → OK: cotización creada; falta la confirmación del usuario.

**Agente:** Te repito el pedido antes de registrarlo: 1 unidad de «Lámpara de escritorio LED Lámpara de lectura de brazo Eye-Care…» a 23,86 € cada una, 23,86 €. Total: 23,86 €. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar. *(esperando confirmación)*

**Enviado al TTS:** Te repito el pedido antes de registrarlo: una unidad de Lámpara de escritorio LED Lámpara de lectura a veintitrés euros con ochenta y seis céntimos cada una, veintitrés euros con ochenta y seis céntimos. Total: veintitrés euros con ochenta y seis céntimos. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar.

- ✘ `cart(lines=[{"product": "@elegida", "quantity": 1}])` — carrito: 1 × B08NNZ6NC2
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 6 (9.2 s)

**Usuario (transcripción del ASR):** Cierra el pedido.

- `cotizar()` → OK: cotización creada; falta la confirmación del usuario.

**Agente:** Te repito el pedido antes de registrarlo: 1 unidad de «Lámpara de escritorio LED Lámpara de lectura de brazo Eye-Care…» a 23,86 € cada una, 23,86 €. Total: 23,86 €. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar. *(esperando confirmación)*

**Enviado al TTS:** Te repito el pedido antes de registrarlo: una unidad de Lámpara de escritorio LED Lámpara de lectura a veintitrés euros con ochenta y seis céntimos cada una, veintitrés euros con ochenta y seis céntimos. Total: veintitrés euros con ochenta y seis céntimos. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar.

- ✔ `awaiting_confirmation(value=true)` — esperando confirmación: sí
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 7 (5.0 s)

**Usuario (transcripción del ASR):** Sí.

- `confirmar_pedido(quote_id="0e46b13607f149b3ae41b43f850f94dd")` → OK: pedido registrado

**Agente:** Pedido número 1 registrado: 1 unidad de «Lámpara de escritorio LED Lámpara de lectura de brazo Eye-Care…» a 23,86 € cada una, 23,86 €. Total: 23,86 €. Gracias por tu compra.

**Enviado al TTS:** Pedido número uno registrado: una unidad de Lámpara de escritorio LED Lámpara de lectura a veintitrés euros con ochenta y seis céntimos cada una, veintitrés euros con ochenta y seis céntimos. Total: veintitrés euros con ochenta y seis céntimos. Gracias por tu compra.

- ✔ `orders(count=1)` — pedidos registrados: 1

## Turno 8 (4.5 s)

**Usuario (transcripción del ASR):** Sí.

- `confirmar_pedido(quote_id="0e46b13607f149b3ae41b43f850f94dd")` → OK: el pedido ya estaba registrado; no se duplicó

**Agente:** Ese pedido ya estaba registrado con el número 1, así que no lo he duplicado. Total: 23,86 €.

**Enviado al TTS:** Ese pedido ya estaba registrado con el número uno, así que no lo he duplicado. Total: veintitrés euros con ochenta y seis céntimos.

- ✔ `orders(count=1)` — pedidos registrados: 1

## Comprobaciones finales

- ✔ `orders(count=1)` — pedidos registrados: 1
- ✘ `order(lines=[{"product": "@elegida", "quantity": 1}], total_cents=1500)` — pedido 1: 1 × B08NNZ6NC2; total 2386 céntimos
- ✘ `stock(product="@elegida", equals=0)` — existencias de B085CHJ9BD: 1
- ✔ `cart(empty=true)` — carrito: vacío

## Violaciones de restricciones

- Ninguna.

## Estado final de la tienda

- Pedido 1: total 23,86 €
  - pedido 1: 1 × `B08NNZ6NC2` a 23,86 €
- Inventario `B085CHJ9BD`: 34 → 1
- Inventario `B08NNZ6NC2`: 34 → 33
- Líneas de carrito pendientes: 0

## Latencia por turno (segundos)

| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total | Audio de respuesta |
|---|---|---|---|---|---|---|---|
| 1 | 0.37 | 0.03 | 7.43 | 0.03 | 7.42 | 15.29 | 31.1 s |
| 2 | 0.34 | 0.00 | 5.20 | 0.05 | 4.74 | 10.33 | 19.9 s |
| 3 | 0.35 | 0.00 | 2.29 | 0.04 | 4.99 | 7.67 | 21.2 s |
| 4 | 0.32 | 0.03 | 0.00 | 0.01 | 10.69 | 11.05 | 44.6 s |
| 5 | 0.34 | 0.00 | 5.27 | 0.09 | 6.53 | 12.22 | 28.3 s |
| 6 | 0.33 | 0.00 | 2.04 | 0.04 | 6.77 | 9.18 | 28.3 s |
| 7 | 0.36 | 0.00 | 0.00 | 0.03 | 4.63 | 5.02 | 18.4 s |
| 8 | 0.32 | 0.00 | 0.00 | 0.04 | 4.10 | 4.46 | 15.9 s |
| **Media de los turnos con LLM (5)** | 0.34 | 0.01 | 4.45 | 0.05 | 6.09 | 10.94 | |
| **Media de los turnos sin LLM (3)** | 0.33 | 0.01 | 0.00 | 0.03 | 6.47 | 6.84 | |

