# 20_agotado_al_confirmar — Producto agotado entre la cotización y la confirmación

- Veredicto: **correcto**
- Entrada: texto
- Tipo: `agotado_al_confirmar`
- Qué se prueba: Con la cotización pendiente, el producto se agota. La confirmación debe rechazarse sin cambios y el agente debe proponer alternativas con existencias. El usuario cambia el producto por la primera alternativa y compra.

## Turno 1 (5.8 s)

**Usuario (texto):** Busco un cuaderno de tapa dura.

- `buscar_productos(consulta="cuaderno tapa dura")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B0112S7DTY | Moleskine QP060BKEVER - Cuaderno digital Evernote (CARNETS CONNECTES), Negro | marca: Moleskine | color: Negro | precio: 7,01 € | existencias: 50 | características (extracto): Cuaderno evernote de tapa dura compatible co…

**Agente:** Tengo el Moleskine QP060BKEVER por 7,01 € y el Arteza de Azul cobalto y gris por 10,95 €. ¿Te interesa alguno?

**Enviado al TTS:** Tengo el Moleskine por siete euros con un céntimo y el Arteza de Azul cobalto y gris por diez euros con noventa y cinco céntimos. ¿Te interesa alguno?

- ✔ `cart(empty=true)` — carrito: vacío

> `@elegido` = `B0112S7DTY` (candidate:1): Moleskine QP060BKEVER - Cuaderno digital Evernote (CARNETS CONNECTES), Negro

> **Suceso externo:** la tienda deja `B0112S7DTY` (@elegido) con precio 6,00 € y existencias 5.

## Turno 2 (4.7 s)

**Usuario (texto):** Añade dos del primero.

- `agregar_al_carrito(product_id="B0112S7DTY", cantidad=2)` → OK: hecho. Así queda el carrito. CARRITO: - id=B0112S7DTY | Moleskine QP060BKEVER - Cuaderno digital Evernote (CARNETS… | 2 unidades × 6,00 € = 12,00 € | existencias: 5 Total del carrito: 12,00 €

**Agente:** Hecho, añadidas dos unidades. En el carrito hay 2 unidades de «Moleskine QP060BKEVER - Cuaderno digital Evernote (CARNETS…» a 6,00 € cada una, 12,00 €. Total: 12,00 €.

**Enviado al TTS:** Hecho, añadidas dos unidades. En el carrito hay dos unidades de Moleskine a seis euros cada una, doce euros. Total: doce euros.

- ✔ `cart(lines=[{"product": "@elegido", "quantity": 2}])` — carrito: 2 × B0112S7DTY

## Turno 3 (2.2 s)

**Usuario (texto):** Cierra el pedido.

- `cotizar()` → OK: cotización creada; falta la confirmación del usuario.

**Agente:** Te repito el pedido antes de registrarlo: 2 unidades de «Moleskine QP060BKEVER - Cuaderno digital Evernote (CARNETS…» a 6,00 € cada una, 12,00 €. Total: 12,00 €. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar. *(esperando confirmación)*

**Enviado al TTS:** Te repito el pedido antes de registrarlo: dos unidades de Moleskine a seis euros cada una, doce euros. Total: doce euros. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar.

- ✔ `awaiting_confirmation(value=true)` — esperando confirmación: sí
- ✔ `orders(count=0)` — pedidos registrados: 0

> **Suceso externo:** la tienda deja `B0112S7DTY` (@elegido) con existencias 0.

## Turno 4 (0.0 s)

**Usuario (texto):** Sí.

- `confirmar_pedido(quote_id="64bff7e7770443f4a88153a51bab9891")` → RECHAZADO: [agotado] El producto B0112S7DTY está agotado.

**Agente:** No he registrado el pedido porque la tienda cambió después de la cotización. «Moleskine QP060BKEVER - Cuaderno digital Evernote (CARNETS…» se ha agotado. Como alternativa tengo: «Moleskine - Cuaderno Digital con Páginas Rayadas y Tapa Dura, Apto…» a 23,03 €, con 44 en existencias; «Moleskine Smart Writing Set - Set de Escritura Inteligente, Cuaderno…» a 9,54 €, con 41 en existencias; «Moleskine - Set de Escritura Inteligente, Cuaderno Digital y…» a 19,42 €, con 12 en existencias. ¿Qué prefieres?

**Enviado al TTS:** No he registrado el pedido porque la tienda cambió después de la cotización. Moleskine se ha agotado. Como alternativa tengo: Moleskine a veintitrés euros con tres céntimos, con cuarenta y cuatro en existencias, Moleskine Smart Writing Set a nueve euros con cincuenta y cuatro céntimos, con cuarenta y uno en existencias, Moleskine a diecinueve euros con cuarenta y dos céntimos, con doce en existencias. ¿Qué prefieres?

- ✔ `orders(count=0)` — pedidos registrados: 0
- ✔ `rejected(code="agotado")` — rechazos del turno: ['agotado']
- ✔ `offered_alternative(instead_of="@elegido")` — alternativas con existencias citadas: ['B076BCD81R', 'B01EJKCWMU', 'B08RJ81R4D']
- ✔ `cart(lines=[{"product": "@elegido", "quantity": 2}])` — carrito: 2 × B0112S7DTY

> `@alternativa` = `B076BCD81R` (candidate:1): Moleskine - Cuaderno Digital con Páginas Rayadas y Tapa Dura, Apto para Uso con Bolígrafo Moleskine+, Tamaño Extra Grande 19 x 25 cm, Color Negro

## Turno 5 (7.0 s)

**Usuario (texto):** Quita ese cuaderno y ponme dos de la primera alternativa.

- `quitar_del_carrito(product_id="B0112S7DTY")` → OK: hecho. Así queda el carrito. CARRITO: vacío
- `agregar_al_carrito(product_id="B076BCD81R", cantidad=2)` → OK: hecho. Así queda el carrito. CARRITO: - id=B076BCD81R | Moleskine - Cuaderno Digital con Páginas Rayadas y Tapa Dura, Apto… | 2 unidades × 23,03 € = 46,06 € | existencias: 44 Total del carrito: 46,06 €

**Agente:** Hecho, añadidas dos unidades del Moleskine - Cuaderno Digital con Páginas Rayadas y Tapa Dura. En el carrito hay 2 unidades de «Moleskine - Cuaderno Digital con Páginas Rayadas y Tapa Dura, Apto…» a 23,03 € cada una, 46,06 €. Total: 46,06 €.

**Enviado al TTS:** Hecho, añadidas dos unidades del Moleskine, Cuaderno Digital con Páginas Rayadas y Tapa Dura. En el carrito hay dos unidades de Moleskine a veintitrés euros con tres céntimos cada una, cuarenta y seis euros con seis céntimos. Total: cuarenta y seis euros con seis céntimos.

- ✔ `cart(lines=[{"product": "@alternativa", "quantity": 2}])` — carrito: 2 × B076BCD81R

## Turno 6 (2.0 s)

**Usuario (texto):** Cierra el pedido.

- `cotizar()` → OK: cotización creada; falta la confirmación del usuario.

**Agente:** Te repito el pedido antes de registrarlo: 2 unidades de «Moleskine - Cuaderno Digital con Páginas Rayadas y Tapa Dura, Apto…» a 23,03 € cada una, 46,06 €. Total: 46,06 €. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar. *(esperando confirmación)*

**Enviado al TTS:** Te repito el pedido antes de registrarlo: dos unidades de Moleskine a veintitrés euros con tres céntimos cada una, cuarenta y seis euros con seis céntimos. Total: cuarenta y seis euros con seis céntimos. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar.

- ✔ `awaiting_confirmation(value=true)` — esperando confirmación: sí
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 7 (0.0 s)

**Usuario (texto):** Sí.

- `confirmar_pedido(quote_id="ce9756d29ab64225acd72173ddc56b8c")` → OK: pedido registrado

**Agente:** Pedido número 1 registrado: 2 unidades de «Moleskine - Cuaderno Digital con Páginas Rayadas y Tapa Dura, Apto…» a 23,03 € cada una, 46,06 €. Total: 46,06 €. Gracias por tu compra.

**Enviado al TTS:** Pedido número uno registrado: dos unidades de Moleskine a veintitrés euros con tres céntimos cada una, cuarenta y seis euros con seis céntimos. Total: cuarenta y seis euros con seis céntimos. Gracias por tu compra.

- ✔ `orders(count=1)` — pedidos registrados: 1

## Comprobaciones finales

- ✔ `orders(count=1)` — pedidos registrados: 1
- ✔ `order(lines=[{"not": "@elegido", "quantity": 2}])` — pedido 1: 2 × B076BCD81R; total 4606 céntimos
- ✔ `stock(product="@elegido", equals=0)` — existencias de B0112S7DTY: 0
- ✔ `cart(empty=true)` — carrito: vacío

## Violaciones de restricciones

- Ninguna.

## Estado final de la tienda

- Pedido 1: total 46,06 €
  - pedido 1: 2 × `B076BCD81R` a 23,03 €
- Inventario `B0112S7DTY`: 50 → 0
- Inventario `B076BCD81R`: 44 → 42
- Líneas de carrito pendientes: 0

## Latencia por turno (segundos)

| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total | Audio de respuesta |
|---|---|---|---|---|---|---|---|
| 1 | 0.00 | 0.04 | 5.70 | 0.03 | 0.00 | 5.77 | 0.0 s |
| 2 | 0.00 | 0.00 | 4.61 | 0.05 | 0.00 | 4.66 | 0.0 s |
| 3 | 0.00 | 0.00 | 2.17 | 0.04 | 0.00 | 2.21 | 0.0 s |
| 4 | 0.00 | 0.03 | 0.00 | 0.01 | 0.00 | 0.04 | 0.0 s |
| 5 | 0.00 | 0.00 | 6.91 | 0.07 | 0.00 | 6.99 | 0.0 s |
| 6 | 0.00 | 0.00 | 1.92 | 0.04 | 0.00 | 1.96 | 0.0 s |
| 7 | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 | 0.03 | 0.0 s |
| **Media de los turnos con LLM (5)** | 0.00 | 0.01 | 4.26 | 0.05 | 0.00 | 4.32 | |
| **Media de los turnos sin LLM (2)** | 0.00 | 0.01 | 0.00 | 0.02 | 0.00 | 0.03 | |

