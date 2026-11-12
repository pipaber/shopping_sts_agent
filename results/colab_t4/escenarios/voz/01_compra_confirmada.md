# 01_compra_confirmada — Compra confirmada

- Veredicto: **correcto**
- Entrada: audio (grabaciones del usuario)
- Tipo: `compra_confirmada`
- Qué se prueba: El usuario busca con presupuesto, añade dos unidades, pide cerrar y confirma. Tras la búsqueda la tienda fija el primer candidato en 14,50 € y 20 unidades, para que el resultado no dependa de qué producto salga primero.

## Turno 1 (36.3 s)

**Usuario (transcripción del ASR):** Hola, busco una cafetería italiana. Tengo un presupuesto de 60 euros.

**Texto correcto:** Hola, busco una cafetera italiana. Tengo un presupuesto de 60 euros.

- `fijar_presupuesto(importe_eur=60)` → OK: presupuesto fijado en 60,00 €.
- `buscar_productos(consulta="cafetería italiana")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B088MC6DPT | FRHOME - Nespresso 120 Cápsulas de Café compatibles - Il Caffè italiano - Tour d' Italia Kit de degustación con varias intensidades | marca: FRHOME | color: Kit degustazione | precio: 6,13 € | existencias: 35 | caracterí…

**Agente:** Tengo una cafetera Nespresso de FRHOME por 6,13 euros, una cafetera Gastroback por 46,24 euros, una Breville Barista Max por 2,25 euros, un libro 'El amor huele a café' por 25,16 euros y una cafetera De'Longhi por 44,50 euros. ¿Te interesa alguna? He anotado un presupuesto de 60,00 €.

**Enviado al TTS:** Tengo una cafetera Nespresso de FRHOME por seis euros con trece céntimos, una cafetera Gastroback por cuarenta y seis euros con veinticuatro céntimos, una Breville Barista Max por dos euros con veinticinco céntimos, un libro El amor huele a café por veinticinco euros con dieciséis céntimos y una cafetera De'Longhi por cuarenta y cuatro euros con cincuenta céntimos. ¿Te interesa alguna? He anotado un presupuesto de sesenta euros.

- ✔ `budget(cents=6000)` — presupuesto en el estado: 6000
- ✔ `cart(empty=true)` — carrito: vacío

> `@elegida` = `B088MC6DPT` (candidate:1): FRHOME - Nespresso 120 Cápsulas de Café compatibles - Il Caffè italiano - Tour d' Italia Kit de degustación con varias intensidades

> **Suceso externo:** la tienda deja `B088MC6DPT` (@elegida) con precio 14,50 € y existencias 20.

## Turno 2 (23.9 s)

**Usuario (transcripción del ASR):** Añade dos de la primera al carrito.

- `agregar_al_carrito(product_id="B088MC6DPT", cantidad=2)` → OK: hecho. Así queda el carrito. CARRITO: - id=B088MC6DPT | FRHOME - Nespresso 120 Cápsulas de Café compatibles - Il Caffè… | 2 unidades × 14,50 € = 29,00 € | existencias: 20 Total del carrito: 29,00 €

**Agente:** Hecho, añadidas dos unidades. El total del carrito es 29,00 €. En el carrito hay 2 unidades de «FRHOME - Nespresso 120 Cápsulas de Café compatibles - Il Caffè…» a 14,50 € cada una, 29,00 €. Total: 29,00 €. Tu presupuesto es de 60,00 € y te quedan 31,00 €.

**Enviado al TTS:** Hecho, añadidas dos unidades. El total del carrito es veintinueve euros. En el carrito hay dos unidades de FRHOME a catorce euros con cincuenta céntimos cada una, veintinueve euros. Total: veintinueve euros. Tu presupuesto es de sesenta euros y te quedan treinta y un euros.

- ✔ `cart(lines=[{"product": "@elegida", "quantity": 2}])` — carrito: 2 × B088MC6DPT
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 3 (16.8 s)

**Usuario (transcripción del ASR):** Quiero cerrar el pedido.

- `cotizar()` → OK: cotización creada; falta la confirmación del usuario.

**Agente:** Te repito el pedido antes de registrarlo: 2 unidades de «FRHOME - Nespresso 120 Cápsulas de Café compatibles - Il Caffè…» a 14,50 € cada una, 29,00 €. Total: 29,00 €. Tu presupuesto es de 60,00 € y te quedan 31,00 €. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar. *(esperando confirmación)*

**Enviado al TTS:** Te repito el pedido antes de registrarlo: dos unidades de FRHOME a catorce euros con cincuenta céntimos cada una, veintinueve euros. Total: veintinueve euros. Tu presupuesto es de sesenta euros y te quedan treinta y un euros. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar.

- ✔ `awaiting_confirmation(value=true)` — esperando confirmación: sí
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 4 (6.4 s)

**Usuario (transcripción del ASR):** Sí, confirmo.

- `confirmar_pedido(quote_id="f7aa8f534e9a4250843ecac487a0afb1")` → OK: pedido registrado

**Agente:** Pedido número 1 registrado: 2 unidades de «FRHOME - Nespresso 120 Cápsulas de Café compatibles - Il Caffè…» a 14,50 € cada una, 29,00 €. Total: 29,00 €. Gracias por tu compra.

**Enviado al TTS:** Pedido número uno registrado: dos unidades de FRHOME a catorce euros con cincuenta céntimos cada una, veintinueve euros. Total: veintinueve euros. Gracias por tu compra.

- ✔ `orders(count=1)` — pedidos registrados: 1

## Comprobaciones finales

- ✔ `orders(count=1)` — pedidos registrados: 1
- ✔ `order(lines=[{"product": "@elegida", "quantity": 2}], total_cents=2900)` — pedido 1: 2 × B088MC6DPT; total 2900 céntimos
- ✔ `stock(product="@elegida", equals=18)` — existencias de B088MC6DPT: 18
- ✔ `cart(empty=true)` — carrito: vacío
- ✔ `budget(cents=6000)` — presupuesto en el estado: 6000

## Violaciones de restricciones

- Ninguna.

## Estado final de la tienda

- Pedido 1: total 29,00 €
  - pedido 1: 2 × `B088MC6DPT` a 14,50 €
- Inventario `B088MC6DPT`: 35 → 18
- Líneas de carrito pendientes: 0

## Latencia por turno (segundos)

| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total | Audio de respuesta |
|---|---|---|---|---|---|---|---|
| 1 | 1.00 | 0.10 | 16.52 | 0.05 | 18.60 | 36.26 | 31.7 s |
| 2 | 0.38 | 0.00 | 7.62 | 0.04 | 15.86 | 23.90 | 26.8 s |
| 3 | 0.39 | 0.00 | 2.85 | 0.04 | 13.52 | 16.80 | 23.1 s |
| 4 | 0.34 | 0.00 | 0.00 | 0.03 | 6.08 | 6.45 | 11.3 s |
| **Media de los turnos con LLM (3)** | 0.59 | 0.03 | 8.99 | 0.04 | 15.99 | 25.65 | |
| **Media de los turnos sin LLM (1)** | 0.34 | 0.00 | 0.00 | 0.03 | 6.08 | 6.45 | |

