# 01_compra_confirmada — Compra confirmada

- Veredicto: **correcto**
- Entrada: audio (sintéticos, hablante de prueba «Luis Moray» de XTTS-v2 (no es la voz del usuario))
- Tipo: `compra_confirmada`
- Qué se prueba: El usuario busca con presupuesto, añade dos unidades, pide cerrar y confirma. Tras la búsqueda la tienda fija el primer candidato en 14,50 € y 20 unidades, para que el resultado no dependa de qué producto salga primero.

## Turno 1 (18.2 s)

**Usuario (transcripción del ASR):** Hola, busco una cafetera italiana. Tengo un presupuesto de 60 euros.

- `fijar_presupuesto(importe_eur=60)` → OK: presupuesto fijado en 60,00 €.
- `buscar_productos(consulta="cafetera italiana")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B06WGTZ874 | De'longhi Dedica - Cafetera de Bomba de Acero Inoxidable para Café Molido o Monodosis, Cafetera para Espresso y Cappuccino, Depósito de 1.3 Litros, Sistema Anti-goteo, EC685.M, Metal 30x33x15cm | marca: De'Longhi | color…

**Agente:** Tengo la De'Longhi Dedica por 5,03 €, la Gastroback por 46,24 €, la De'Longhi ECOV por 44,50 €, la CREATE THERA Classic por 5,05 € y la CREATE Stylance Pro por 5,23 €. ¿Te interesa alguna? He anotado un presupuesto de 60,00 €.

**Enviado al TTS:** Tengo la De'Longhi Dedica por cinco euros con tres céntimos, la Gastroback por cuarenta y seis euros con veinticuatro céntimos, la De'Longhi ECOV por cuarenta y cuatro euros con cincuenta céntimos, la CREATE THERA Classic por cinco euros con cinco céntimos y la CREATE Stylance Pro por cinco euros con veintitrés céntimos. ¿Te interesa alguna? He anotado un presupuesto de sesenta euros.

- ✔ `budget(cents=6000)` — presupuesto en el estado: 6000
- ✔ `cart(empty=true)` — carrito: vacío

> `@elegida` = `B06WGTZ874` (candidate:1): De'longhi Dedica - Cafetera de Bomba de Acero Inoxidable para Café Molido o Monodosis, Cafetera para Espresso y Cappuccino, Depósito de 1.3 Litros, Sistema Anti-goteo, EC685.M, Metal 30x33x15cm

> **Suceso externo:** la tienda deja `B06WGTZ874` (@elegida) con precio 14,50 € y existencias 20.

## Turno 2 (11.7 s)

**Usuario (transcripción del ASR):** Añade dos de la primera al carrito E.

**Texto correcto:** Añade dos de la primera al carrito.

- `agregar_al_carrito(product_id="B06WGTZ874", cantidad=2)` → OK: hecho. Así queda el carrito. CARRITO: - id=B06WGTZ874 | De'longhi Dedica - Cafetera de Bomba de Acero Inoxidable para Café… | 2 unidades × 14,50 € = 29,00 € | existencias: 20 Total del carrito: 29,00 €

**Agente:** Hecho, añadidas dos unidades. El total es 29,00 €. En el carrito hay 2 unidades de «De'longhi Dedica - Cafetera de Bomba de Acero Inoxidable para Café…» a 14,50 € cada una, 29,00 €. Total: 29,00 €. Tu presupuesto es de 60,00 € y te quedan 31,00 €.

**Enviado al TTS:** Hecho, añadidas dos unidades. El total es veintinueve euros. En el carrito hay dos unidades de De'longhi Dedica a catorce euros con cincuenta céntimos cada una, veintinueve euros. Total: veintinueve euros. Tu presupuesto es de sesenta euros y te quedan treinta y un euros.

- ✔ `cart(lines=[{"product": "@elegida", "quantity": 2}])` — carrito: 2 × B06WGTZ874
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 3 (9.1 s)

**Usuario (transcripción del ASR):** Quiero cerrar el pedido.

- `cotizar()` → OK: cotización creada; falta la confirmación del usuario.

**Agente:** Te repito el pedido antes de registrarlo: 2 unidades de «De'longhi Dedica - Cafetera de Bomba de Acero Inoxidable para Café…» a 14,50 € cada una, 29,00 €. Total: 29,00 €. Tu presupuesto es de 60,00 € y te quedan 31,00 €. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar. *(esperando confirmación)*

**Enviado al TTS:** Te repito el pedido antes de registrarlo: dos unidades de De'longhi Dedica a catorce euros con cincuenta céntimos cada una, veintinueve euros. Total: veintinueve euros. Tu presupuesto es de sesenta euros y te quedan treinta y un euros. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar.

- ✔ `awaiting_confirmation(value=true)` — esperando confirmación: sí
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 4 (4.2 s)

**Usuario (transcripción del ASR):** Sí, confirmo.

- `confirmar_pedido(quote_id="5f154455f4e445f09bd828afa26f8a8e")` → OK: pedido registrado

**Agente:** Pedido número 1 registrado: 2 unidades de «De'longhi Dedica - Cafetera de Bomba de Acero Inoxidable para Café…» a 14,50 € cada una, 29,00 €. Total: 29,00 €. Gracias por tu compra.

**Enviado al TTS:** Pedido número uno registrado: dos unidades de De'longhi Dedica a catorce euros con cincuenta céntimos cada una, veintinueve euros. Total: veintinueve euros. Gracias por tu compra.

- ✔ `orders(count=1)` — pedidos registrados: 1

## Comprobaciones finales

- ✔ `orders(count=1)` — pedidos registrados: 1
- ✔ `order(lines=[{"product": "@elegida", "quantity": 2}], total_cents=2900)` — pedido 1: 2 × B06WGTZ874; total 2900 céntimos
- ✔ `stock(product="@elegida", equals=18)` — existencias de B06WGTZ874: 18
- ✔ `cart(empty=true)` — carrito: vacío
- ✔ `budget(cents=6000)` — presupuesto en el estado: 6000

## Violaciones de restricciones

- Ninguna.

## Estado final de la tienda

- Pedido 1: total 29,00 €
  - pedido 1: 2 × `B06WGTZ874` a 14,50 €
- Inventario `B06WGTZ874`: 27 → 18
- Líneas de carrito pendientes: 0

## Latencia por turno (segundos)

| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total | Audio de respuesta |
|---|---|---|---|---|---|---|---|
| 1 | 0.56 | 0.03 | 9.84 | 0.04 | 7.70 | 18.18 | 33.2 s |
| 2 | 0.35 | 0.00 | 5.11 | 0.05 | 6.18 | 11.70 | 26.1 s |
| 3 | 0.33 | 0.00 | 2.21 | 0.04 | 6.47 | 9.05 | 27.4 s |
| 4 | 0.33 | 0.00 | 0.00 | 0.04 | 3.81 | 4.19 | 15.6 s |
| **Media de los turnos con LLM (3)** | 0.41 | 0.01 | 5.72 | 0.05 | 6.79 | 12.98 | |
| **Media de los turnos sin LLM (1)** | 0.33 | 0.00 | 0.00 | 0.04 | 3.81 | 4.19 | |

