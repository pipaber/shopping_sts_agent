# 06_cambio_stock_confirmacion_repetida — Cambio de stock entre cotización y confirmación, y confirmación repetida

- Veredicto: **correcto**
- Entrada: texto
- Tipo: `cambio_stock_confirmacion_repetida`
- Qué se prueba: Con la cotización de tres unidades pendiente, la tienda se queda con una sola. La confirmación debe rechazarse sin tocar nada y ofrecer una salida. El usuario lo deja en una unidad, confirma y repite el sí: debe haber un único pedido.

## Turno 1 (7.0 s)

**Usuario (texto):** Busco una lámpara de escritorio LED.

- `buscar_productos(consulta="lámpara escritorio LED")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B08GWGJR9S | Lámpara Escritorio LED, La lamparas de escritorio tiene cuentas de lámpara 60LED, 5 niveles de brillo, 3 modos de colo, USB para cargar, Batería 4000mAh, Temporizador de 45min, [Clase energética A++] | marca: SENXINGYAN …

**Agente:** Tengo la lámpara de escritorio LED de SENXINGYAN por 36,61 €, la de SLATOR por 44,20 €, la de SOFIL por 38,74 € y la de Prtukyt por 23,86 €. ¿Te interesa alguna?

**Enviado al TTS:** Tengo la lámpara de escritorio LED de SENXINGYAN por treinta y seis euros con sesenta y un céntimos, la de SLATOR por cuarenta y cuatro euros con veinte céntimos, la de SOFIL por treinta y ocho euros con setenta y cuatro céntimos y la de Prtukyt por veintitrés euros con ochenta y seis céntimos. ¿Te interesa alguna?

- ✔ `cart(empty=true)` — carrito: vacío

> `@elegida` = `B08GWGJR9S` (candidate:1): Lámpara Escritorio LED, La lamparas de escritorio tiene cuentas de lámpara 60LED, 5 niveles de brillo, 3 modos de colo, USB para cargar, Batería 4000mAh, Temporizador de 45min, [Clase energética A++]

> **Suceso externo:** la tienda deja `B08GWGJR9S` (@elegida) con precio 15,00 € y existencias 10.

## Turno 2 (5.2 s)

**Usuario (texto):** Añade tres de la primera.

- `agregar_al_carrito(product_id="B08GWGJR9S", cantidad=3)` → OK: hecho. Así queda el carrito. CARRITO: - id=B08GWGJR9S | Lámpara Escritorio LED, La lamparas de escritorio tiene cuentas de… | 3 unidades × 15,00 € = 45,00 € | existencias: 10 Total del carrito: 45,00 €

**Agente:** Hecho, añadidas tres unidades. El total es 45,00 €. En el carrito hay 3 unidades de «Lámpara Escritorio LED, La lamparas de escritorio tiene cuentas de…» a 15,00 € cada una, 45,00 €. Total: 45,00 €.

**Enviado al TTS:** Hecho, añadidas tres unidades. El total es cuarenta y cinco euros. En el carrito hay tres unidades de Lámpara Escritorio LED a quince euros cada una, cuarenta y cinco euros. Total: cuarenta y cinco euros.

- ✔ `cart(lines=[{"product": "@elegida", "quantity": 3}])` — carrito: 3 × B08GWGJR9S

## Turno 3 (2.3 s)

**Usuario (texto):** Quiero cerrar el pedido.

- `cotizar()` → OK: cotización creada; falta la confirmación del usuario.

**Agente:** Te repito el pedido antes de registrarlo: 3 unidades de «Lámpara Escritorio LED, La lamparas de escritorio tiene cuentas de…» a 15,00 € cada una, 45,00 €. Total: 45,00 €. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar. *(esperando confirmación)*

**Enviado al TTS:** Te repito el pedido antes de registrarlo: tres unidades de Lámpara Escritorio LED a quince euros cada una, cuarenta y cinco euros. Total: cuarenta y cinco euros. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar.

- ✔ `awaiting_confirmation(value=true)` — esperando confirmación: sí
- ✔ `orders(count=0)` — pedidos registrados: 0

> **Suceso externo:** la tienda deja `B08GWGJR9S` (@elegida) con existencias 1.

## Turno 4 (0.0 s)

**Usuario (texto):** Sí.

- `confirmar_pedido(quote_id="f30d93b28b86493f9242445c9f0e5b3c")` → RECHAZADO: [stock_insuficiente] Solo queda 1 unidad del producto B08GWGJR9S y se pidieron 3.

**Agente:** No he registrado el pedido porque la tienda cambió después de la cotización. De «Lámpara Escritorio LED, La lamparas de escritorio tiene cuentas de…» solo queda 1 unidad y habías pedido 3. Puedo dejarlo en 1. Como alternativa tengo: «Lámpara Escritorio LED, Flexo de Escritorio (Cuidado Ocular, Puerto…» a 23,23 €, con 16 en existencias; «Lámpara Escritorio LED, Flexo de Escritorio, La luz natural protege…» a 44,20 €, con 34 en existencias; «Lámpara de escritorio, HIHIGOU Lámpara de mesa LED 3.2W con Luz de…» a 15,43 €, con 17 en existencias. ¿Qué prefieres?

**Enviado al TTS:** No he registrado el pedido porque la tienda cambió después de la cotización. De Lámpara Escritorio LED solo queda una unidad y habías pedido tres. Puedo dejarlo en uno. Como alternativa tengo: Lámpara Escritorio LED a veintitrés euros con veintitrés céntimos, con dieciséis en existencias, Lámpara Escritorio LED a cuarenta y cuatro euros con veinte céntimos, con treinta y cuatro en existencias, Lámpara de escritorio a quince euros con cuarenta y tres céntimos, con diecisiete en existencias. ¿Qué prefieres?

- ✔ `orders(count=0)` — pedidos registrados: 0
- ✔ `rejected(code="stock_insuficiente")` — rechazos del turno: ['stock_insuficiente']
- ✔ `cart(lines=[{"product": "@elegida", "quantity": 3}])` — carrito: 3 × B08GWGJR9S
- ✔ `stock(product="@elegida", equals=1)` — existencias de B08GWGJR9S: 1

## Turno 5 (6.7 s)

**Usuario (texto):** Vale, déjalo en una.

- `cambiar_cantidad(product_id="B08GWGJR9S", cantidad=1)` → OK: hecho. Así queda el carrito. CARRITO: - id=B08GWGJR9S | Lámpara Escritorio LED, La lamparas de escritorio tiene cuentas de… | 1 unidad × 15,00 € = 15,00 € | existencias: 1 Total del carrito: 15,00 €

**Agente:** Hecho, ahora el carrito tiene 1 unidad de «Lámpara Escritorio LED, La lamparas de escritorio tiene cuentas de…» a 15,00 €, total 15,00 €. En el carrito hay 1 unidad de «Lámpara Escritorio LED, La lamparas de escritorio tiene cuentas de…» a 15,00 € cada una, 15,00 €. Total: 15,00 €.

**Enviado al TTS:** Hecho, ahora el carrito tiene una unidad de Lámpara Escritorio LED a quince euros, total quince euros. En el carrito hay una unidad de Lámpara Escritorio LED a quince euros cada una, quince euros. Total: quince euros.

- ✔ `cart(lines=[{"product": "@elegida", "quantity": 1}])` — carrito: 1 × B08GWGJR9S
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 6 (2.2 s)

**Usuario (texto):** Cierra el pedido.

- `cotizar()` → OK: cotización creada; falta la confirmación del usuario.

**Agente:** Te repito el pedido antes de registrarlo: 1 unidad de «Lámpara Escritorio LED, La lamparas de escritorio tiene cuentas de…» a 15,00 € cada una, 15,00 €. Total: 15,00 €. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar. *(esperando confirmación)*

**Enviado al TTS:** Te repito el pedido antes de registrarlo: una unidad de Lámpara Escritorio LED a quince euros cada una, quince euros. Total: quince euros. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar.

- ✔ `awaiting_confirmation(value=true)` — esperando confirmación: sí
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 7 (0.0 s)

**Usuario (texto):** Sí.

- `confirmar_pedido(quote_id="02be838c2ae14e1ea2dfb2a57b4d85d0")` → OK: pedido registrado

**Agente:** Pedido número 1 registrado: 1 unidad de «Lámpara Escritorio LED, La lamparas de escritorio tiene cuentas de…» a 15,00 € cada una, 15,00 €. Total: 15,00 €. Gracias por tu compra.

**Enviado al TTS:** Pedido número uno registrado: una unidad de Lámpara Escritorio LED a quince euros cada una, quince euros. Total: quince euros. Gracias por tu compra.

- ✔ `orders(count=1)` — pedidos registrados: 1

## Turno 8 (0.0 s)

**Usuario (texto):** Sí.

- `confirmar_pedido(quote_id="02be838c2ae14e1ea2dfb2a57b4d85d0")` → OK: el pedido ya estaba registrado; no se duplicó

**Agente:** Ese pedido ya estaba registrado con el número 1, así que no lo he duplicado. Total: 15,00 €.

**Enviado al TTS:** Ese pedido ya estaba registrado con el número uno, así que no lo he duplicado. Total: quince euros.

- ✔ `orders(count=1)` — pedidos registrados: 1

## Comprobaciones finales

- ✔ `orders(count=1)` — pedidos registrados: 1
- ✔ `order(lines=[{"product": "@elegida", "quantity": 1}], total_cents=1500)` — pedido 1: 1 × B08GWGJR9S; total 1500 céntimos
- ✔ `stock(product="@elegida", equals=0)` — existencias de B08GWGJR9S: 0
- ✔ `cart(empty=true)` — carrito: vacío

## Violaciones de restricciones

- Ninguna.

## Estado final de la tienda

- Pedido 1: total 15,00 €
  - pedido 1: 1 × `B08GWGJR9S` a 15,00 €
- Inventario `B08GWGJR9S`: 8 → 0
- Líneas de carrito pendientes: 0

## Latencia por turno (segundos)

| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total | Audio de respuesta |
|---|---|---|---|---|---|---|---|
| 1 | 0.00 | 0.03 | 6.92 | 0.03 | 0.00 | 6.98 | 0.0 s |
| 2 | 0.00 | 0.00 | 5.12 | 0.05 | 0.00 | 5.17 | 0.0 s |
| 3 | 0.00 | 0.00 | 2.28 | 0.04 | 0.00 | 2.32 | 0.0 s |
| 4 | 0.00 | 0.02 | 0.00 | 0.01 | 0.00 | 0.03 | 0.0 s |
| 5 | 0.00 | 0.00 | 6.69 | 0.06 | 0.00 | 6.75 | 0.0 s |
| 6 | 0.00 | 0.00 | 2.20 | 0.04 | 0.00 | 2.24 | 0.0 s |
| 7 | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 | 0.03 | 0.0 s |
| 8 | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 | 0.03 | 0.0 s |
| **Media de los turnos con LLM (5)** | 0.00 | 0.01 | 4.64 | 0.04 | 0.00 | 4.69 | |
| **Media de los turnos sin LLM (3)** | 0.00 | 0.01 | 0.00 | 0.02 | 0.00 | 0.03 | |

