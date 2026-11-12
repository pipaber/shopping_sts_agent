# 06_cambio_stock_confirmacion_repetida — Cambio de stock entre cotización y confirmación, y confirmación repetida

- Veredicto: **correcto**
- Entrada: audio (grabaciones del usuario)
- Tipo: `cambio_stock_confirmacion_repetida`
- Qué se prueba: Con la cotización de tres unidades pendiente, la tienda se queda con una sola. La confirmación debe rechazarse sin tocar nada y ofrecer una salida. El usuario lo deja en una unidad, confirma y repite el sí: debe haber un único pedido.

## Turno 1 (26.0 s)

**Usuario (transcripción del ASR):** Busco una lámpara de escritorio LED.

- `buscar_productos(consulta="lámpara escritorio LED")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B085CHJ9BD | Lámpara Escritorio LED, Flexo de Escritorio, La luz natural protege los ojos, Lampara led Escritorio regulable con puerto de carga USB, 5 Modos, 10 Niveles de Brillo,Temporizador de 30/60min | marca: SLATOR | color: Negr…

**Agente:** Tengo la lámpara de escritorio LED de SLATOR por 44,20 €, la de SENXINGYAN por 36,61 €, la de SOFIL por 38,74 €, la de Prtukyt por 23,86 € y la de HyAdierTech por 11,87 €. ¿Te interesa alguna?

**Enviado al TTS:** Tengo la lámpara de escritorio LED de SLATOR por cuarenta y cuatro euros con veinte céntimos, la de SENXINGYAN por treinta y seis euros con sesenta y un céntimos, la de SOFIL por treinta y ocho euros con setenta y cuatro céntimos, la de Prtukyt por veintitrés euros con ochenta y seis céntimos y la de HyAdierTech por once euros con ochenta y siete céntimos. ¿Te interesa alguna?

- ✔ `cart(empty=true)` — carrito: vacío

> `@elegida` = `B085CHJ9BD` (candidate:1): Lámpara Escritorio LED, Flexo de Escritorio, La luz natural protege los ojos, Lampara led Escritorio regulable con puerto de carga USB, 5 Modos, 10 Niveles de Brillo,Temporizador de 30/60min

> **Suceso externo:** la tienda deja `B085CHJ9BD` (@elegida) con precio 15,00 € y existencias 10.

## Turno 2 (24.7 s)

**Usuario (transcripción del ASR):** Añade 3 de la primera.

**Texto correcto:** Añade tres de la primera.

- `agregar_al_carrito(product_id="B085CHJ9BD", cantidad=3)` → OK: hecho. Así queda el carrito. CARRITO: - id=B085CHJ9BD | Lámpara Escritorio LED, Flexo de Escritorio, La luz natural protege… | 3 unidades × 15,00 € = 45,00 € | existencias: 10 Total del carrito: 45,00 €

**Agente:** Hecho, añadidas tres unidades. El total es 45,00 €. En el carrito hay 3 unidades de «Lámpara Escritorio LED, Flexo de Escritorio, La luz natural protege…» a 15,00 € cada una, 45,00 €. Total: 45,00 €.

**Enviado al TTS:** Hecho, añadidas tres unidades. El total es cuarenta y cinco euros. En el carrito hay tres unidades de Lámpara Escritorio LED a quince euros cada una, cuarenta y cinco euros. Total: cuarenta y cinco euros.

- ✔ `cart(lines=[{"product": "@elegida", "quantity": 3}])` — carrito: 3 × B085CHJ9BD

## Turno 3 (14.2 s)

**Usuario (transcripción del ASR):** Quiero cerrar el pedido.

- `cotizar()` → OK: cotización creada; falta la confirmación del usuario.

**Agente:** Te repito el pedido antes de registrarlo: 3 unidades de «Lámpara Escritorio LED, Flexo de Escritorio, La luz natural protege…» a 15,00 € cada una, 45,00 €. Total: 45,00 €. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar. *(esperando confirmación)*

**Enviado al TTS:** Te repito el pedido antes de registrarlo: tres unidades de Lámpara Escritorio LED a quince euros cada una, cuarenta y cinco euros. Total: cuarenta y cinco euros. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar.

- ✔ `awaiting_confirmation(value=true)` — esperando confirmación: sí
- ✔ `orders(count=0)` — pedidos registrados: 0

> **Suceso externo:** la tienda deja `B085CHJ9BD` (@elegida) con existencias 1.

## Turno 4 (23.7 s)

**Usuario (transcripción del ASR):** Sí.

- `confirmar_pedido(quote_id="37869a4a31e04b2d944a1a5c9db95871")` → RECHAZADO: [stock_insuficiente] Solo queda 1 unidad del producto B085CHJ9BD y se pidieron 3.

**Agente:** No he registrado el pedido porque la tienda cambió después de la cotización. De «Lámpara Escritorio LED, Flexo de Escritorio, La luz natural protege…» solo queda 1 unidad y habías pedido 3. Puedo dejarlo en 1. Como alternativa tengo: «Lámpara Escritorio LED, Flexo de Escritorio (Cuidado Ocular, Puerto…» a 23,23 €, con 16 en existencias; «Lámpara Escritorio LED,JUKSTG 5 Modos 10 Niveles de Brillo Lámpara de…» a 34,86 €, con 25 en existencias; «Lámpara de escritorio LED Lámpara de lectura de brazo Eye-Care…» a 23,86 €, con 34 en existencias. ¿Qué prefieres?

**Enviado al TTS:** No he registrado el pedido porque la tienda cambió después de la cotización. De Lámpara Escritorio LED solo queda una unidad y habías pedido tres. Puedo dejarlo en uno. Como alternativa tengo: Lámpara Escritorio LED a veintitrés euros con veintitrés céntimos, con dieciséis en existencias, Lámpara Escritorio LED a treinta y cuatro euros con ochenta y seis céntimos, con veinticinco en existencias, Lámpara de escritorio LED Lámpara de lectura a veintitrés euros con ochenta y seis céntimos, con treinta y cuatro en existencias. ¿Qué prefieres?

- ✔ `orders(count=0)` — pedidos registrados: 0
- ✔ `rejected(code="stock_insuficiente")` — rechazos del turno: ['stock_insuficiente']
- ✔ `cart(lines=[{"product": "@elegida", "quantity": 3}])` — carrito: 3 × B085CHJ9BD
- ✔ `stock(product="@elegida", equals=1)` — existencias de B085CHJ9BD: 1

## Turno 5 (23.7 s)

**Usuario (transcripción del ASR):** Vale, déjalo en una.

- `cambiar_cantidad(product_id="B085CHJ9BD", cantidad=1)` → OK: hecho. Así queda el carrito. CARRITO: - id=B085CHJ9BD | Lámpara Escritorio LED, Flexo de Escritorio, La luz natural protege… | 1 unidad × 15,00 € = 15,00 € | existencias: 1 Total del carrito: 15,00 €

**Agente:** Hecho, ahora el carrito tiene 1 unidad de «Lámpara Escritorio LED, Flexo de Escritorio, La luz natural protege…» a 15,00 €, total 15,00 €. En el carrito hay 1 unidad de «Lámpara Escritorio LED, Flexo de Escritorio, La luz natural protege…» a 15,00 € cada una, 15,00 €. Total: 15,00 €.

**Enviado al TTS:** Hecho, ahora el carrito tiene una unidad de Lámpara Escritorio LED a quince euros, total quince euros. En el carrito hay una unidad de Lámpara Escritorio LED a quince euros cada una, quince euros. Total: quince euros.

- ✔ `cart(lines=[{"product": "@elegida", "quantity": 1}])` — carrito: 1 × B085CHJ9BD
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 6 (12.3 s)

**Usuario (transcripción del ASR):** Cierra el pedido.

- `cotizar()` → OK: cotización creada; falta la confirmación del usuario.

**Agente:** Te repito el pedido antes de registrarlo: 1 unidad de «Lámpara Escritorio LED, Flexo de Escritorio, La luz natural protege…» a 15,00 € cada una, 15,00 €. Total: 15,00 €. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar. *(esperando confirmación)*

**Enviado al TTS:** Te repito el pedido antes de registrarlo: una unidad de Lámpara Escritorio LED a quince euros cada una, quince euros. Total: quince euros. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar.

- ✔ `awaiting_confirmation(value=true)` — esperando confirmación: sí
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 7 (10.6 s)

**Usuario (transcripción del ASR):** Sí.

- `confirmar_pedido(quote_id="d64cd3d7224349e3b98e3827b7c2a0cb")` → OK: pedido registrado

**Agente:** Pedido número 1 registrado: 1 unidad de «Lámpara Escritorio LED, Flexo de Escritorio, La luz natural protege…» a 15,00 € cada una, 15,00 €. Total: 15,00 €. Gracias por tu compra.

**Enviado al TTS:** Pedido número uno registrado: una unidad de Lámpara Escritorio LED a quince euros cada una, quince euros. Total: quince euros. Gracias por tu compra.

- ✔ `orders(count=1)` — pedidos registrados: 1

## Turno 8 (5.6 s)

**Usuario (transcripción del ASR):** sí

**Texto correcto:** Sí.

- `confirmar_pedido(quote_id="d64cd3d7224349e3b98e3827b7c2a0cb")` → OK: el pedido ya estaba registrado; no se duplicó

**Agente:** Ese pedido ya estaba registrado con el número 1, así que no lo he duplicado. Total: 15,00 €.

**Enviado al TTS:** Ese pedido ya estaba registrado con el número uno, así que no lo he duplicado. Total: quince euros.

- ✔ `orders(count=1)` — pedidos registrados: 1

## Comprobaciones finales

- ✔ `orders(count=1)` — pedidos registrados: 1
- ✔ `order(lines=[{"product": "@elegida", "quantity": 1}], total_cents=1500)` — pedido 1: 1 × B085CHJ9BD; total 1500 céntimos
- ✔ `stock(product="@elegida", equals=0)` — existencias de B085CHJ9BD: 0
- ✔ `cart(empty=true)` — carrito: vacío

## Violaciones de restricciones

- Ninguna.

## Estado final de la tienda

- Pedido 1: total 15,00 €
  - pedido 1: 1 × `B085CHJ9BD` a 15,00 €
- Inventario `B085CHJ9BD`: 34 → 0
- Líneas de carrito pendientes: 0

## Latencia por turno (segundos)

| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total | Audio de respuesta |
|---|---|---|---|---|---|---|---|
| 1 | 0.42 | 0.08 | 12.01 | 0.03 | 13.46 | 25.99 | 23.4 s |
| 2 | 0.40 | 0.00 | 8.19 | 0.05 | 16.07 | 24.71 | 27.7 s |
| 3 | 0.36 | 0.00 | 3.75 | 0.04 | 10.01 | 14.16 | 17.8 s |
| 4 | 0.33 | 0.05 | 0.00 | 0.02 | 23.29 | 23.69 | 40.1 s |
| 5 | 0.35 | 0.00 | 11.16 | 0.04 | 12.10 | 23.66 | 20.8 s |
| 6 | 0.35 | 0.00 | 2.97 | 0.03 | 8.92 | 12.28 | 15.6 s |
| 7 | 0.37 | 0.00 | 0.00 | 0.04 | 10.15 | 10.56 | 18.2 s |
| 8 | 0.34 | 0.00 | 0.00 | 0.03 | 5.23 | 5.60 | 7.5 s |
| **Media de los turnos con LLM (5)** | 0.38 | 0.02 | 7.62 | 0.04 | 12.11 | 20.16 | |
| **Media de los turnos sin LLM (3)** | 0.35 | 0.02 | 0.00 | 0.03 | 12.89 | 13.28 | |

