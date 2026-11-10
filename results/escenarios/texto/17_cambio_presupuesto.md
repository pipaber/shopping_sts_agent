# 17_cambio_presupuesto — Bajar el presupuesto con el carrito lleno

- Veredicto: **correcto**
- Entrada: texto
- Tipo: `cambio_presupuesto`
- Qué se prueba: Con tres unidades en el carrito (30,00 €) el usuario baja el presupuesto a 25 €. Cerrar el pedido debe rechazarse sin que el agente cambie el carrito por su cuenta. Con dos unidades (20,00 €) sí se puede comprar.

## Turno 1 (8.5 s)

**Usuario (texto):** Busco una taza de desayuno. Tengo 40 euros.

- `fijar_presupuesto(importe_eur=40)` → OK: presupuesto fijado en 40,00 €.
- `buscar_productos(consulta="taza desayuno")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B08ZLX5MXL | Taza Desayuno con Mensaje Respira_ Regalos Originales para Mujer_ Taza café Infusiones o Decoración Hogar en Cerámica de Gran Calidad. | marca: AN | color: desconocido | precio: 7,48 € | existencias: 17 | características…

**Agente:** Tengo una taza de desayuno de AN por 7,48 euros, una de MUGFFINS por 18,90 euros, una de HMB por 10,39 euros, una de Wistty por 5,05 euros y un pack de 2 tazas por 5,30 euros. ¿Te interesa alguna? He anotado un presupuesto de 40,00 €.

**Enviado al TTS:** Tengo una taza de desayuno de AN por siete euros con cuarenta y ocho céntimos, una de MUGFFINS por dieciocho euros con noventa céntimos, una de HMB por diez euros con treinta y nueve céntimos, una de Wistty por cinco euros con cinco céntimos y un pack de dos tazas por cinco euros con treinta céntimos. ¿Te interesa alguna? He anotado un presupuesto de cuarenta euros.

- ✔ `budget(cents=4000)` — presupuesto en el estado: 4000
- ✔ `cart(empty=true)` — carrito: vacío

> `@elegida` = `B08ZLX5MXL` (candidate:1): Taza Desayuno con Mensaje Respira_ Regalos Originales para Mujer_ Taza café Infusiones o Decoración Hogar en Cerámica de Gran Calidad.

> **Suceso externo:** la tienda deja `B08ZLX5MXL` (@elegida) con precio 10,00 € y existencias 20.

## Turno 2 (5.4 s)

**Usuario (texto):** Añade tres de la primera.

- `agregar_al_carrito(product_id="B08ZLX5MXL", cantidad=3)` → OK: hecho. Así queda el carrito. CARRITO: - id=B08ZLX5MXL | Taza Desayuno con Mensaje Respira_ Regalos Originales para Mujer_… | 3 unidades × 10,00 € = 30,00 € | existencias: 20 Total del carrito: 30,00 €

**Agente:** Hecho, añadidas tres unidades. El total es 30,00 €. En el carrito hay 3 unidades de «Taza Desayuno con Mensaje Respira_ Regalos Originales para Mujer_…» a 10,00 € cada una, 30,00 €. Total: 30,00 €. Tu presupuesto es de 40,00 € y te quedan 10,00 €.

**Enviado al TTS:** Hecho, añadidas tres unidades. El total es treinta euros. En el carrito hay tres unidades de Taza Desayuno con Mensaje Respira Regalos Originales a diez euros cada una, treinta euros. Total: treinta euros. Tu presupuesto es de cuarenta euros y te quedan diez euros.

- ✔ `cart(lines=[{"product": "@elegida", "quantity": 3}])` — carrito: 3 × B08ZLX5MXL

## Turno 3 (4.9 s)

**Usuario (texto):** Mejor baja mi presupuesto a 25 euros.

- `fijar_presupuesto(importe_eur=25)` → OK: presupuesto fijado en 25,00 €. Aviso: el carrito suma 30,00 € y lo supera en 5,00 €.

**Agente:** El carrito supera tu presupuesto en 5,00 €. ¿Qué deseas hacer? En el carrito hay 3 unidades de «Taza Desayuno con Mensaje Respira_ Regalos Originales para Mujer_…» a 10,00 € cada una, 30,00 €. Total: 30,00 €. Tu presupuesto es de 25,00 € y lo superas en 5,00 €.

**Enviado al TTS:** El carrito supera tu presupuesto en cinco euros. ¿Qué deseas hacer? En el carrito hay tres unidades de Taza Desayuno con Mensaje Respira Regalos Originales a diez euros cada una, treinta euros. Total: treinta euros. Tu presupuesto es de veinticinco euros y lo superas en cinco euros.

- ✔ `budget(cents=2500)` — presupuesto en el estado: 2500
- ✔ `cart(lines=[{"product": "@elegida", "quantity": 3}])` — carrito: 3 × B08ZLX5MXL

## Turno 4 (4.9 s)

**Usuario (texto):** Cierra el pedido.

- `cotizar()` → RECHAZADO: [presupuesto_excedido] El total sería 30,00 € y supera el presupuesto de 25,00 € por 5,00 €.

**Agente:** El pedido supera tu presupuesto en 5,00 €. ¿Quieres reducirlo o cambiar el presupuesto?

**Enviado al TTS:** El pedido supera tu presupuesto en cinco euros. ¿Quieres reducirlo o cambiar el presupuesto?

- ✔ `orders(count=0)` — pedidos registrados: 0
- ✔ `awaiting_confirmation(value=false)` — esperando confirmación: no
- ✔ `cart(lines=[{"product": "@elegida", "quantity": 3}])` — carrito: 3 × B08ZLX5MXL

## Turno 5 (7.6 s)

**Usuario (texto):** Entonces deja solo dos.

- `cambiar_cantidad(product_id="B08ZLX5MXL", cantidad=2)` → OK: hecho. Así queda el carrito. CARRITO: - id=B08ZLX5MXL | Taza Desayuno con Mensaje Respira_ Regalos Originales para Mujer_… | 2 unidades × 10,00 € = 20,00 € | existencias: 20 Total del carrito: 20,00 €

**Agente:** Hecho, el carrito ahora tiene 2 unidades de «Taza Desayuno con Mensaje Respira_ Regalos Originales para Mujer_…» a 10,00 € cada una, 20,00 €. Total: 20,00 €. En el carrito hay 2 unidades de «Taza Desayuno con Mensaje Respira_ Regalos Originales para Mujer_…» a 10,00 € cada una, 20,00 €. Total: 20,00 €. Tu presupuesto es de 25,00 € y te quedan 5,00 €.

**Enviado al TTS:** Hecho, el carrito ahora tiene dos unidades de Taza Desayuno con Mensaje Respira Regalos Originales a diez euros cada una, veinte euros. Total: veinte euros. En el carrito hay dos unidades de Taza Desayuno con Mensaje Respira Regalos Originales a diez euros cada una, veinte euros. Total: veinte euros. Tu presupuesto es de veinticinco euros y te quedan cinco euros.

- ✔ `cart(lines=[{"product": "@elegida", "quantity": 2}])` — carrito: 2 × B08ZLX5MXL

## Turno 6 (2.6 s)

**Usuario (texto):** Cierra el pedido.

- `cotizar()` → OK: cotización creada; falta la confirmación del usuario.

**Agente:** Te repito el pedido antes de registrarlo: 2 unidades de «Taza Desayuno con Mensaje Respira_ Regalos Originales para Mujer_…» a 10,00 € cada una, 20,00 €. Total: 20,00 €. Tu presupuesto es de 25,00 € y te quedan 5,00 €. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar. *(esperando confirmación)*

**Enviado al TTS:** Te repito el pedido antes de registrarlo: dos unidades de Taza Desayuno con Mensaje Respira Regalos Originales a diez euros cada una, veinte euros. Total: veinte euros. Tu presupuesto es de veinticinco euros y te quedan cinco euros. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar.

- ✔ `awaiting_confirmation(value=true)` — esperando confirmación: sí
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 7 (0.0 s)

**Usuario (texto):** Sí.

- `confirmar_pedido(quote_id="b5a9cb00f7fb44d0828e5d3b8a28aa6b")` → OK: pedido registrado

**Agente:** Pedido número 1 registrado: 2 unidades de «Taza Desayuno con Mensaje Respira_ Regalos Originales para Mujer_…» a 10,00 € cada una, 20,00 €. Total: 20,00 €. Gracias por tu compra.

**Enviado al TTS:** Pedido número uno registrado: dos unidades de Taza Desayuno con Mensaje Respira Regalos Originales a diez euros cada una, veinte euros. Total: veinte euros. Gracias por tu compra.

- ✔ `orders(count=1)` — pedidos registrados: 1

## Comprobaciones finales

- ✔ `orders(count=1)` — pedidos registrados: 1
- ✔ `order(lines=[{"product": "@elegida", "quantity": 2}], total_cents=2000)` — pedido 1: 2 × B08ZLX5MXL; total 2000 céntimos
- ✔ `budget(cents=2500)` — presupuesto en el estado: 2500
- ✔ `stock(product="@elegida", equals=18)` — existencias de B08ZLX5MXL: 18
- ✔ `cart(empty=true)` — carrito: vacío

## Violaciones de restricciones

- Ninguna.

## Estado final de la tienda

- Pedido 1: total 20,00 €
  - pedido 1: 2 × `B08ZLX5MXL` a 10,00 €
- Inventario `B08ZLX5MXL`: 17 → 18
- Líneas de carrito pendientes: 0

## Latencia por turno (segundos)

| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total | Audio de respuesta |
|---|---|---|---|---|---|---|---|
| 1 | 0.00 | 0.03 | 8.45 | 0.03 | 0.00 | 8.51 | 0.0 s |
| 2 | 0.00 | 0.00 | 5.36 | 0.05 | 0.00 | 5.41 | 0.0 s |
| 3 | 0.00 | 0.00 | 4.90 | 0.03 | 0.00 | 4.93 | 0.0 s |
| 4 | 0.00 | 0.00 | 4.87 | 0.03 | 0.00 | 4.90 | 0.0 s |
| 5 | 0.00 | 0.00 | 7.51 | 0.04 | 0.00 | 7.55 | 0.0 s |
| 6 | 0.00 | 0.00 | 2.60 | 0.04 | 0.00 | 2.64 | 0.0 s |
| 7 | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 | 0.03 | 0.0 s |
| **Media de los turnos con LLM (6)** | 0.00 | 0.00 | 5.61 | 0.04 | 0.00 | 5.66 | |
| **Media de los turnos sin LLM (1)** | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 | 0.03 | |

