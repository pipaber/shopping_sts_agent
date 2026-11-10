# 13_confirmacion_con_cambio — Un sí con cambios no compra

- Veredicto: **correcto**
- Entrada: texto
- Tipo: `confirmacion_con_cambio`
- Qué se prueba: A la cotización de una unidad el usuario contesta «sí, pero que sean tres». No es una confirmación limpia: no debe registrarse el pedido de una unidad. El pedido final lleva tres.

## Turno 1 (7.8 s)

**Usuario (texto):** Busco un paraguas plegable.

- `buscar_productos(consulta="paraguas plegable")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B08ZC4844X | Gonex Paraguas de Golf Plegable de 10 Varillas, Paraguas Grande a Prueba de Viento de Toldo Doble, Paraguas Compacto de 54 Pulgadas, Ventilado y a Prueba de Lluvia para Deportes, Negocios y Viajes | marca: Gonex | color:…

**Agente:** Tengo el paraguas Gonex Negro por 6,52 euros, el sombrero xj Camuflaje por 16,30 euros, el paraguas LJGYX Blue por 49,59 euros, el paraguas Jooayou Night Sky por 30,33 euros y el sombrero Yosoo Health Gear plata por 16,34 euros. ¿Te interesa alguno?

**Enviado al TTS:** Tengo el paraguas Gonex Negro por seis euros con cincuenta y dos céntimos, el sombrero xj Camuflaje por dieciséis euros con treinta céntimos, el paraguas LJGYX Blue por cuarenta y nueve euros con cincuenta y nueve céntimos, el paraguas Jooayou Night Sky por treinta euros con treinta y tres céntimos y el sombrero Yosoo Health Gear plata por dieciséis euros con treinta y cuatro céntimos. ¿Te interesa alguno?

- ✔ `cart(empty=true)` — carrito: vacío

> `@elegido` = `B08ZC4844X` (candidate:1): Gonex Paraguas de Golf Plegable de 10 Varillas, Paraguas Grande a Prueba de Viento de Toldo Doble, Paraguas Compacto de 54 Pulgadas, Ventilado y a Prueba de Lluvia para Deportes, Negocios y Viajes

> **Suceso externo:** la tienda deja `B08ZC4844X` (@elegido) con precio 9,00 € y existencias 20.

## Turno 2 (5.4 s)

**Usuario (texto):** Añade uno del primero.

- `agregar_al_carrito(product_id="B08ZC4844X", cantidad=1)` → OK: hecho. Así queda el carrito. CARRITO: - id=B08ZC4844X | Gonex Paraguas de Golf Plegable de 10 Varillas, Paraguas Grande a… | 1 unidad × 9,00 € = 9,00 € | existencias: 20 Total del carrito: 9,00 €

**Agente:** Hecho, añadido un paraguas Gonex Negro al carrito. En el carrito hay 1 unidad de «Gonex Paraguas de Golf Plegable de 10 Varillas, Paraguas Grande a…» a 9,00 € cada una, 9,00 €. Total: 9,00 €.

**Enviado al TTS:** Hecho, añadido un paraguas Gonex Negro al carrito. En el carrito hay una unidad de Gonex Paraguas de Golf Plegable de diez a nueve euros cada una, nueve euros. Total: nueve euros.

- ✔ `cart(lines=[{"product": "@elegido", "quantity": 1}])` — carrito: 1 × B08ZC4844X

## Turno 3 (2.3 s)

**Usuario (texto):** Cierra el pedido.

- `cotizar()` → OK: cotización creada; falta la confirmación del usuario.

**Agente:** Te repito el pedido antes de registrarlo: 1 unidad de «Gonex Paraguas de Golf Plegable de 10 Varillas, Paraguas Grande a…» a 9,00 € cada una, 9,00 €. Total: 9,00 €. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar. *(esperando confirmación)*

**Enviado al TTS:** Te repito el pedido antes de registrarlo: una unidad de Gonex Paraguas de Golf Plegable de diez a nueve euros cada una, nueve euros. Total: nueve euros. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar.

- ✔ `awaiting_confirmation(value=true)` — esperando confirmación: sí
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 4 (6.0 s)

**Usuario (texto):** Sí, pero que sean tres.

- `cambiar_cantidad(product_id="B08ZC4844X", cantidad=3)` → OK: hecho. Así queda el carrito. CARRITO: - id=B08ZC4844X | Gonex Paraguas de Golf Plegable de 10 Varillas, Paraguas Grande a… | 3 unidades × 9,00 € = 27,00 € | existencias: 20 Total del carrito: 27,00 €

**Agente:** Hecho, el carrito ahora incluye 3 unidades de paraguas Gonex Negro por 9,00 € cada uno, total 27,00 €. En el carrito hay 3 unidades de «Gonex Paraguas de Golf Plegable de 10 Varillas, Paraguas Grande a…» a 9,00 € cada una, 27,00 €. Total: 27,00 €.

**Enviado al TTS:** Hecho, el carrito ahora incluye tres unidades de paraguas Gonex Negro por nueve euros cada uno, total veintisiete euros. En el carrito hay tres unidades de Gonex Paraguas de Golf Plegable de diez a nueve euros cada una, veintisiete euros. Total: veintisiete euros.

- ✔ `orders(count=0)` — pedidos registrados: 0
- ✔ `cart(lines=[{"product": "@elegido", "quantity": 3}])` — carrito: 3 × B08ZC4844X

## Turno 5 (2.2 s)

**Usuario (texto):** Cierra el pedido.

- `cotizar()` → OK: cotización creada; falta la confirmación del usuario.

**Agente:** Te repito el pedido antes de registrarlo: 3 unidades de «Gonex Paraguas de Golf Plegable de 10 Varillas, Paraguas Grande a…» a 9,00 € cada una, 27,00 €. Total: 27,00 €. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar. *(esperando confirmación)*

**Enviado al TTS:** Te repito el pedido antes de registrarlo: tres unidades de Gonex Paraguas de Golf Plegable de diez a nueve euros cada una, veintisiete euros. Total: veintisiete euros. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar.

- ✔ `awaiting_confirmation(value=true)` — esperando confirmación: sí
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 6 (0.0 s)

**Usuario (texto):** Sí.

- `confirmar_pedido(quote_id="78891010ccd44d8aad7bdda0153c4c1a")` → OK: pedido registrado

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
| 1 | 0.00 | 0.03 | 7.71 | 0.03 | 0.00 | 7.76 | 0.0 s |
| 2 | 0.00 | 0.00 | 5.33 | 0.05 | 0.00 | 5.38 | 0.0 s |
| 3 | 0.00 | 0.00 | 2.21 | 0.04 | 0.00 | 2.25 | 0.0 s |
| 4 | 0.00 | 0.00 | 5.99 | 0.06 | 0.00 | 6.04 | 0.0 s |
| 5 | 0.00 | 0.00 | 2.21 | 0.03 | 0.00 | 2.23 | 0.0 s |
| 6 | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 | 0.03 | 0.0 s |
| **Media de los turnos con LLM (5)** | 0.00 | 0.01 | 4.69 | 0.04 | 0.00 | 4.74 | |
| **Media de los turnos sin LLM (1)** | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 | 0.03 | |

