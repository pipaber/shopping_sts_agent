# 13_confirmacion_con_cambio — Un sí con cambios no compra

- Veredicto: **correcto**
- Entrada: texto
- Tipo: `confirmacion_con_cambio`
- Qué se prueba: A la cotización de una unidad el usuario contesta «sí, pero que sean tres». No es una confirmación limpia: no debe registrarse el pedido de una unidad. El pedido final lleva tres.

## Turno 1 (7.8 s)

**Usuario (texto):** Busco un paraguas plegable.

- `buscar_productos(consulta="paraguas plegable")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B08ZC4844X | Gonex Paraguas de Golf Plegable de 10 Varillas, Paraguas Grande a Prueba de Viento de Toldo Doble, Paraguas Compacto de 54 Pulgadas, Ventilado y a Prueba de Lluvia para Deportes, Negocios y Viajes | marca: Gonex | color:…

**Agente:** Tengo el paraguas Gonex por 6,52 euros, el sombrero de paraguas xj por 16,30 euros, el paraguas Jooayou por 30,33 euros, el sombrero de paraguas Yosoo Health Gear por 16,34 euros y el paraguas ADVERS por 33,61 euros. ¿Te interesa alguno?

**Enviado al TTS:** Tengo el paraguas Gonex por seis euros con cincuenta y dos céntimos, el sombrero de paraguas xj por dieciséis euros con treinta céntimos, el paraguas Jooayou por treinta euros con treinta y tres céntimos, el sombrero de paraguas Yosoo Health Gear por dieciséis euros con treinta y cuatro céntimos y el paraguas ADVERS por treinta y tres euros con sesenta y un céntimos. ¿Te interesa alguno?

- ✔ `cart(empty=true)` — carrito: vacío

> `@elegido` = `B08ZC4844X` (candidate:1): Gonex Paraguas de Golf Plegable de 10 Varillas, Paraguas Grande a Prueba de Viento de Toldo Doble, Paraguas Compacto de 54 Pulgadas, Ventilado y a Prueba de Lluvia para Deportes, Negocios y Viajes

> **Suceso externo:** la tienda deja `B08ZC4844X` (@elegido) con precio 9,00 € y existencias 20.

## Turno 2 (4.8 s)

**Usuario (texto):** Añade uno del primero.

- `agregar_al_carrito(product_id="B08ZC4844X", cantidad=1)` → OK: hecho. Así queda el carrito. CARRITO: - id=B08ZC4844X | Gonex Paraguas de Golf Plegable de 10 Varillas, Paraguas Grande a… | 1 unidad × 9,00 € = 9,00 € | existencias: 20 Total del carrito: 9,00 €

**Agente:** Hecho, añadida una unidad al carrito. En el carrito hay 1 unidad de «Gonex Paraguas de Golf Plegable de 10 Varillas, Paraguas Grande a…» a 9,00 € cada una, 9,00 €. Total: 9,00 €.

**Enviado al TTS:** Hecho, añadida una unidad al carrito. En el carrito hay una unidad de Gonex Paraguas de Golf Plegable de diez a nueve euros cada una, nueve euros. Total: nueve euros.

- ✔ `cart(lines=[{"product": "@elegido", "quantity": 1}])` — carrito: 1 × B08ZC4844X

## Turno 3 (2.2 s)

**Usuario (texto):** Cierra el pedido.

- `cotizar()` → OK: cotización creada; falta la confirmación del usuario.

**Agente:** Te repito el pedido antes de registrarlo: 1 unidad de «Gonex Paraguas de Golf Plegable de 10 Varillas, Paraguas Grande a…» a 9,00 € cada una, 9,00 €. Total: 9,00 €. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar. *(esperando confirmación)*

**Enviado al TTS:** Te repito el pedido antes de registrarlo: una unidad de Gonex Paraguas de Golf Plegable de diez a nueve euros cada una, nueve euros. Total: nueve euros. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar.

- ✔ `awaiting_confirmation(value=true)` — esperando confirmación: sí
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 4 (7.6 s)

**Usuario (texto):** Sí, pero que sean tres.

- `cambiar_cantidad(product_id="B08ZC4844X", cantidad=3)` → OK: hecho. Así queda el carrito. CARRITO: - id=B08ZC4844X | Gonex Paraguas de Golf Plegable de 10 Varillas, Paraguas Grande a… | 3 unidades × 9,00 € = 27,00 € | existencias: 20 Total del carrito: 27,00 €

**Agente:** Hecho, añadidas dos unidades más. Ahora en el carrito hay 3 unidades de «Gonex Paraguas de Golf Plegable de 10 Varillas, Paraguas Grande a…» a 9,00 € cada una, 27,00 €. Total: 27,00 €. En el carrito hay 3 unidades de «Gonex Paraguas de Golf Plegable de 10 Varillas, Paraguas Grande a…» a 9,00 € cada una, 27,00 €. Total: 27,00 €.

**Enviado al TTS:** Hecho, añadidas dos unidades más. Ahora en el carrito hay tres unidades de Gonex Paraguas de Golf Plegable de diez a nueve euros cada una, veintisiete euros. Total: veintisiete euros. En el carrito hay tres unidades de Gonex Paraguas de Golf Plegable de diez a nueve euros cada una, veintisiete euros. Total: veintisiete euros.

- ✔ `orders(count=0)` — pedidos registrados: 0
- ✔ `cart(lines=[{"product": "@elegido", "quantity": 3}])` — carrito: 3 × B08ZC4844X

## Turno 5 (2.3 s)

**Usuario (texto):** Cierra el pedido.

- `cotizar()` → OK: cotización creada; falta la confirmación del usuario.

**Agente:** Te repito el pedido antes de registrarlo: 3 unidades de «Gonex Paraguas de Golf Plegable de 10 Varillas, Paraguas Grande a…» a 9,00 € cada una, 27,00 €. Total: 27,00 €. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar. *(esperando confirmación)*

**Enviado al TTS:** Te repito el pedido antes de registrarlo: tres unidades de Gonex Paraguas de Golf Plegable de diez a nueve euros cada una, veintisiete euros. Total: veintisiete euros. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar.

- ✔ `awaiting_confirmation(value=true)` — esperando confirmación: sí
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 6 (0.0 s)

**Usuario (texto):** Sí.

- `confirmar_pedido(quote_id="cb5cb1aec69f44659659de8e8e345027")` → OK: pedido registrado

**Agente:** Pedido número 1 registrado: 3 unidades de «Gonex Paraguas de Golf Plegable de 10 Varillas, Paraguas Grande a…» a 9,00 € cada una, 27,00 €. Total: 27,00 €. Gracias por tu compra.

**Enviado al TTS:** Pedido número uno registrado: tres unidades de Gonex Paraguas de Golf Plegable de diez a nueve euros cada una, veintisiete euros. Total: veintisiete euros. Gracias por tu compra.

- ✔ `orders(count=1)` — pedidos registrados: 1

## Comprobaciones finales

- ✔ `orders(count=1)` — pedidos registrados: 1
- ✔ `order(lines=[{"product": "@elegido", "quantity": 3}], total_cents=2700)` — pedido 1: 3 × B08ZC4844X; total 2700 céntimos
- ✔ `stock(product="@elegido", equals=17)` — existencias de B08ZC4844X: 17
- ✔ `cart(empty=true)` — carrito: vacío

## Violaciones de restricciones

- Ninguna.

## Estado final de la tienda

- Pedido 1: total 27,00 €
  - pedido 1: 3 × `B08ZC4844X` a 9,00 €
- Inventario `B08ZC4844X`: 7 → 17
- Líneas de carrito pendientes: 0

## Latencia por turno (segundos)

| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total | Audio de respuesta |
|---|---|---|---|---|---|---|---|
| 1 | 0.00 | 0.03 | 7.75 | 0.03 | 0.00 | 7.80 | 0.0 s |
| 2 | 0.00 | 0.00 | 4.80 | 0.05 | 0.00 | 4.84 | 0.0 s |
| 3 | 0.00 | 0.00 | 2.18 | 0.04 | 0.00 | 2.22 | 0.0 s |
| 4 | 0.00 | 0.00 | 7.60 | 0.05 | 0.00 | 7.65 | 0.0 s |
| 5 | 0.00 | 0.00 | 2.31 | 0.04 | 0.00 | 2.34 | 0.0 s |
| 6 | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 | 0.03 | 0.0 s |
| **Media de los turnos con LLM (5)** | 0.00 | 0.01 | 4.93 | 0.04 | 0.00 | 4.97 | |
| **Media de los turnos sin LLM (1)** | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 | 0.03 | |

