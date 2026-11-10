# 01_compra_confirmada — Compra confirmada

- Veredicto: **correcto**
- Entrada: texto
- Tipo: `compra_confirmada`
- Qué se prueba: El usuario busca con presupuesto, añade dos unidades, pide cerrar y confirma. Tras la búsqueda la tienda fija el primer candidato en 14,50 € y 20 unidades, para que el resultado no dependa de qué producto salga primero.

## Turno 1 (9.6 s)

**Usuario (texto):** Hola, busco una cafetera italiana. Tengo un presupuesto de 60 euros.

- `fijar_presupuesto(importe_eur=60)` → OK: presupuesto fijado en 60,00 €.
- `buscar_productos(consulta="cafetera italiana")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B07V47R2Z2 | Gastroback 42619 Design Espresso Advanced Barista - Cafetera espresso (programable, con mecanismo cónico y bomba de espresso italiana, 15 bares, acero inoxidable) | marca: GASTROBACK | color: Acero Inoxidable. | precio: …

**Agente:** Tengo una cafetera Gastroback por 46,24 euros, una De'Longhi por 5,03 euros, una Solis por 20,53 euros, una Princess por 7,74 euros y una Cecotec por 15,19 euros. ¿Te interesa alguna? He anotado un presupuesto de 60,00 €.

**Enviado al TTS:** Tengo una cafetera Gastroback por cuarenta y seis euros con veinticuatro céntimos, una De'Longhi por cinco euros con tres céntimos, una Solis por veinte euros con cincuenta y tres céntimos, una Princess por siete euros con setenta y cuatro céntimos y una Cecotec por quince euros con diecinueve céntimos. ¿Te interesa alguna? He anotado un presupuesto de sesenta euros.

- ✔ `budget(cents=6000)` — presupuesto en el estado: 6000
- ✔ `cart(empty=true)` — carrito: vacío

> `@elegida` = `B07V47R2Z2` (candidate:1): Gastroback 42619 Design Espresso Advanced Barista - Cafetera espresso (programable, con mecanismo cónico y bomba de espresso italiana, 15 bares, acero inoxidable)

> **Suceso externo:** la tienda deja `B07V47R2Z2` (@elegida) con precio 14,50 € y existencias 20.

## Turno 2 (5.0 s)

**Usuario (texto):** Añade dos de la primera al carrito.

- `agregar_al_carrito(product_id="B07V47R2Z2", cantidad=2)` → OK: hecho. Así queda el carrito. CARRITO: - id=B07V47R2Z2 | Gastroback 42619 Design Espresso Advanced Barista - Cafetera espresso… | 2 unidades × 14,50 € = 29,00 € | existencias: 20 Total del carrito: 29,00 €

**Agente:** Hecho, añadidas dos unidades. El total es 29,00 €. En el carrito hay 2 unidades de «Gastroback 42619 Design Espresso Advanced Barista - Cafetera espresso…» a 14,50 € cada una, 29,00 €. Total: 29,00 €. Tu presupuesto es de 60,00 € y te quedan 31,00 €.

**Enviado al TTS:** Hecho, añadidas dos unidades. El total es veintinueve euros. En el carrito hay dos unidades de Gastroback cuarenta y dos mil seiscientos diecinueve Design Espresso Advanced Barista a catorce euros con cincuenta céntimos cada una, veintinueve euros. Total: veintinueve euros. Tu presupuesto es de sesenta euros y te quedan treinta y un euros.

- ✔ `cart(lines=[{"product": "@elegida", "quantity": 2}])` — carrito: 2 × B07V47R2Z2
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 3 (2.1 s)

**Usuario (texto):** Quiero cerrar el pedido.

- `cotizar()` → OK: cotización creada; falta la confirmación del usuario.

**Agente:** Te repito el pedido antes de registrarlo: 2 unidades de «Gastroback 42619 Design Espresso Advanced Barista - Cafetera espresso…» a 14,50 € cada una, 29,00 €. Total: 29,00 €. Tu presupuesto es de 60,00 € y te quedan 31,00 €. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar. *(esperando confirmación)*

**Enviado al TTS:** Te repito el pedido antes de registrarlo: dos unidades de Gastroback cuarenta y dos mil seiscientos diecinueve Design Espresso Advanced Barista a catorce euros con cincuenta céntimos cada una, veintinueve euros. Total: veintinueve euros. Tu presupuesto es de sesenta euros y te quedan treinta y un euros. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar.

- ✔ `awaiting_confirmation(value=true)` — esperando confirmación: sí
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 4 (0.0 s)

**Usuario (texto):** Sí, confirmo.

- `confirmar_pedido(quote_id="aad74610e2e24621b03c27eb43a6e475")` → OK: pedido registrado

**Agente:** Pedido número 1 registrado: 2 unidades de «Gastroback 42619 Design Espresso Advanced Barista - Cafetera espresso…» a 14,50 € cada una, 29,00 €. Total: 29,00 €. Gracias por tu compra.

**Enviado al TTS:** Pedido número uno registrado: dos unidades de Gastroback cuarenta y dos mil seiscientos diecinueve Design Espresso Advanced Barista a catorce euros con cincuenta céntimos cada una, veintinueve euros. Total: veintinueve euros. Gracias por tu compra.

- ✔ `orders(count=1)` — pedidos registrados: 1

## Comprobaciones finales

- ✔ `orders(count=1)` — pedidos registrados: 1
- ✔ `order(lines=[{"product": "@elegida", "quantity": 2}], total_cents=2900)` — pedido 1: 2 × B07V47R2Z2; total 2900 céntimos
- ✔ `stock(product="@elegida", equals=18)` — existencias de B07V47R2Z2: 18
- ✔ `cart(empty=true)` — carrito: vacío
- ✔ `budget(cents=6000)` — presupuesto en el estado: 6000

## Violaciones de restricciones

- Ninguna.

## Estado final de la tienda

- Pedido 1: total 29,00 €
  - pedido 1: 2 × `B07V47R2Z2` a 14,50 €
- Inventario `B07V47R2Z2`: 26 → 18
- Líneas de carrito pendientes: 0

## Latencia por turno (segundos)

| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total | Audio de respuesta |
|---|---|---|---|---|---|---|---|
| 1 | 0.00 | 0.03 | 9.57 | 0.04 | 0.00 | 9.63 | 0.0 s |
| 2 | 0.00 | 0.00 | 4.96 | 0.05 | 0.00 | 5.02 | 0.0 s |
| 3 | 0.00 | 0.00 | 2.05 | 0.04 | 0.00 | 2.09 | 0.0 s |
| 4 | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 | 0.03 | 0.0 s |
| **Media de los turnos con LLM (3)** | 0.00 | 0.01 | 5.53 | 0.04 | 0.00 | 5.58 | |
| **Media de los turnos sin LLM (1)** | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 | 0.03 | |

