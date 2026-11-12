# 26_presupuesto_con_carrito — Presupuesto dicho con el carrito lleno y cantidad con cifras

- Veredicto: **correcto**
- Entrada: texto
- Tipo: `presupuesto_con_carrito`
- Qué se prueba: Escenario de reserva, escrito antes de corregir el agente y sin ejecutarlo. Con productos en el carrito el usuario dice su gasto máximo en euros, y el agente debe fijarlo. Después cambia la cantidad con una cifra suelta («Entonces que sean 4.»): debe cambiar la cantidad y dejar el presupuesto como estaba.

## Turno 1 (7.5 s)

**Usuario (texto):** Busco un cuaderno de tapa dura.

- `buscar_productos(consulta="cuaderno tapa dura")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B08VMR6YL7 | Arteza Cuaderno de Dibujo, 15 x 20 cm [Set de 2, Azul Cobalto y Gris], Pack Cuadernos de Dibujo, Diarios de Tapa Dura con Papel de Escribir en Blanco [96 Hojas] | marca: ARTEZA | color: Azul cobalto y gris | precio: 10,9…

**Agente:** Tengo el Arteza de Azul cobalto y gris por 10,95 €, el Arteza de Rosa y Granate por 10,16 €, el Eachgoo A5 negro por 43,88 €, el Moleskine negro por 7,01 € y el Eachgoo A4 negro por 26,05 €. ¿Te interesa alguno?

**Enviado al TTS:** Tengo el Arteza de Azul cobalto y gris por diez euros con noventa y cinco céntimos, el Arteza de Rosa y Granate por diez euros con dieciséis céntimos, el Eachgoo A5 negro por cuarenta y tres euros con ochenta y ocho céntimos, el Moleskine negro por siete euros con un céntimo y el Eachgoo A4 negro por veintiséis euros con cinco céntimos. ¿Te interesa alguno?

- ✔ `cart(empty=true)` — carrito: vacío

> `@elegido` = `B08VMR6YL7` (candidate:1): Arteza Cuaderno de Dibujo, 15 x 20 cm [Set de 2, Azul Cobalto y Gris], Pack Cuadernos de Dibujo, Diarios de Tapa Dura con Papel de Escribir en Blanco [96 Hojas]

> **Suceso externo:** la tienda deja `B08VMR6YL7` (@elegido) con precio 6,00 € y existencias 20.

## Turno 2 (4.7 s)

**Usuario (texto):** Añade dos del primero.

- `agregar_al_carrito(product_id="B08VMR6YL7", cantidad=2)` → OK: hecho. Así queda el carrito. CARRITO: - id=B08VMR6YL7 | Arteza Cuaderno de Dibujo, 15 x 20 cm [Set de 2, Azul Cobalto y… | 2 unidades × 6,00 € = 12,00 € | existencias: 20 Total del carrito: 12,00 €

**Agente:** Hecho, añadidas dos unidades. En el carrito hay 2 unidades de «Arteza Cuaderno de Dibujo, 15 x 20 cm [Set de 2, Azul Cobalto y…» a 6,00 € cada una, 12,00 €. Total: 12,00 €.

**Enviado al TTS:** Hecho, añadidas dos unidades. En el carrito hay dos unidades de Arteza Cuaderno de Dibujo a seis euros cada una, doce euros. Total: doce euros.

- ✔ `cart(lines=[{"product": "@elegido", "quantity": 2}])` — carrito: 2 × B08VMR6YL7

## Turno 3 (7.7 s)

**Usuario (texto):** Por cierto, no quiero gastar más de 30 euros.

- `fijar_presupuesto(importe_eur=30)` → OK: presupuesto fijado en 30,00 €.
- `consultar_precio_stock(product_id="B08VMR6YL7")` → OK: precio 6,00 €; quedan 20 unidades. Esta herramienta no da características: para color, batería, medidas u otros datos del producto usa detalle_producto.

**Agente:** El cuaderno de Arteza sigue disponible. El total del carrito es 12,00 €, que está dentro del presupuesto de 30 euros. En el carrito hay 2 unidades de «Arteza Cuaderno de Dibujo, 15 x 20 cm [Set de 2, Azul Cobalto y…» a 6,00 € cada una, 12,00 €. Total: 12,00 €. Tu presupuesto es de 30,00 € y te quedan 18,00 €.

**Enviado al TTS:** El cuaderno de Arteza sigue disponible. El total del carrito es doce euros, que está dentro del presupuesto de treinta euros. En el carrito hay dos unidades de Arteza Cuaderno de Dibujo a seis euros cada una, doce euros. Total: doce euros. Tu presupuesto es de treinta euros y te quedan dieciocho euros.

- ✔ `budget(cents=3000)` — presupuesto en el estado: 3000
- ✔ `cart(lines=[{"product": "@elegido", "quantity": 2}])` — carrito: 2 × B08VMR6YL7

## Turno 4 (8.1 s)

**Usuario (texto):** Entonces que sean 4.

- `cambiar_cantidad(product_id="B08VMR6YL7", cantidad=4)` → OK: hecho. Así queda el carrito. CARRITO: - id=B08VMR6YL7 | Arteza Cuaderno de Dibujo, 15 x 20 cm [Set de 2, Azul Cobalto y… | 4 unidades × 6,00 € = 24,00 € | existencias: 20 Total del carrito: 24,00 €

**Agente:** Hecho, añadidas dos unidades más. En el carrito hay 4 unidades de «Arteza Cuaderno de Dibujo, 15 x 20 cm [Set de 2, Azul Cobalto y…» a 6,00 € cada una, 24,00 €. Total: 24,00 €. En el carrito hay 4 unidades de «Arteza Cuaderno de Dibujo, 15 x 20 cm [Set de 2, Azul Cobalto y…» a 6,00 € cada una, 24,00 €. Total: 24,00 €. Tu presupuesto es de 30,00 € y te quedan 6,00 €.

**Enviado al TTS:** Hecho, añadidas dos unidades más. En el carrito hay cuatro unidades de Arteza Cuaderno de Dibujo a seis euros cada una, veinticuatro euros. Total: veinticuatro euros. En el carrito hay cuatro unidades de Arteza Cuaderno de Dibujo a seis euros cada una, veinticuatro euros. Total: veinticuatro euros. Tu presupuesto es de treinta euros y te quedan seis euros.

- ✔ `budget(cents=3000)` — presupuesto en el estado: 3000
- ✔ `cart(lines=[{"product": "@elegido", "quantity": 4}])` — carrito: 4 × B08VMR6YL7

## Turno 5 (2.4 s)

**Usuario (texto):** Cierra el pedido.

- `cotizar()` → OK: cotización creada; falta la confirmación del usuario.

**Agente:** Te repito el pedido antes de registrarlo: 4 unidades de «Arteza Cuaderno de Dibujo, 15 x 20 cm [Set de 2, Azul Cobalto y…» a 6,00 € cada una, 24,00 €. Total: 24,00 €. Tu presupuesto es de 30,00 € y te quedan 6,00 €. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar. *(esperando confirmación)*

**Enviado al TTS:** Te repito el pedido antes de registrarlo: cuatro unidades de Arteza Cuaderno de Dibujo a seis euros cada una, veinticuatro euros. Total: veinticuatro euros. Tu presupuesto es de treinta euros y te quedan seis euros. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar.

- ✔ `awaiting_confirmation(value=true)` — esperando confirmación: sí
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 6 (0.0 s)

**Usuario (texto):** Sí, confirmo.

- `confirmar_pedido(quote_id="9473048dcd3441d9b720b05adcdcb7ff")` → OK: pedido registrado

**Agente:** Pedido número 1 registrado: 4 unidades de «Arteza Cuaderno de Dibujo, 15 x 20 cm [Set de 2, Azul Cobalto y…» a 6,00 € cada una, 24,00 €. Total: 24,00 €. Gracias por tu compra.

**Enviado al TTS:** Pedido número uno registrado: cuatro unidades de Arteza Cuaderno de Dibujo a seis euros cada una, veinticuatro euros. Total: veinticuatro euros. Gracias por tu compra.

- ✔ `orders(count=1)` — pedidos registrados: 1

## Comprobaciones finales

- ✔ `orders(count=1)` — pedidos registrados: 1
- ✔ `order(lines=[{"product": "@elegido", "quantity": 4}], total_cents=2400)` — pedido 1: 4 × B08VMR6YL7; total 2400 céntimos
- ✔ `budget(cents=3000)` — presupuesto en el estado: 3000
- ✔ `stock(product="@elegido", equals=16)` — existencias de B08VMR6YL7: 16
- ✔ `cart(empty=true)` — carrito: vacío

## Violaciones de restricciones

- Ninguna.

## Estado final de la tienda

- Pedido 1: total 24,00 €
  - pedido 1: 4 × `B08VMR6YL7` a 6,00 €
- Inventario `B08VMR6YL7`: 4 → 16
- Líneas de carrito pendientes: 0

## Latencia por turno (segundos)

| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total | Audio de respuesta |
|---|---|---|---|---|---|---|---|
| 1 | 0.00 | 0.03 | 7.42 | 0.03 | 0.00 | 7.47 | 0.0 s |
| 2 | 0.00 | 0.00 | 4.70 | 0.05 | 0.00 | 4.75 | 0.0 s |
| 3 | 0.00 | 0.00 | 7.64 | 0.03 | 0.00 | 7.67 | 0.0 s |
| 4 | 0.00 | 0.00 | 8.07 | 0.05 | 0.00 | 8.12 | 0.0 s |
| 5 | 0.00 | 0.00 | 2.39 | 0.03 | 0.00 | 2.42 | 0.0 s |
| 6 | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 | 0.03 | 0.0 s |
| **Media de los turnos con LLM (5)** | 0.00 | 0.01 | 6.04 | 0.04 | 0.00 | 6.09 | |
| **Media de los turnos sin LLM (1)** | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 | 0.03 | |

