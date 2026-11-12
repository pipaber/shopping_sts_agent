# 25_correccion_con_cifras — Corregir una cantidad con cifras antes de confirmar

- Veredicto: **correcto**
- Entrada: texto
- Tipo: `correccion_con_cifras`
- Qué se prueba: Escenario de reserva, escrito antes de corregir el agente y sin ejecutarlo. Con la cotización pendiente, el usuario corrige la cantidad escribiendo los números con cifras («Perdona, eran 14, no 4.»), como los escribe a veces el ASR. El agente debe cambiar la cantidad, no fijar un presupuesto; el pedido final lleva catorce.

## Turno 1 (9.1 s)

**Usuario (texto):** Necesito unas pilas recargables.

- `buscar_productos(consulta="pilas recargables")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B07F58PXYR | BONAI LCD Cargador de Pilas Inteligente para AA/AAA/SC/C/D /9V Ni-MH/Ni-CD, 4 Ranura Independiente y Auto-Detección, Universal Cargador Pilas con Función de Descarga (Cargador de batería AC) | marca: BONAI | color: desco…

**Agente:** Tengo la opción de BONAI LCD Cargador de Pilas por 14,97 euros, el quitapelusas Severin por 38,16 euros, el empujador recargable Latigo por 42,86 euros, el pack de cepillos de dientes Philips por 25,13 euros y el pica veterinario PICAAVISPA por 9,79 euros. ¿Te interesa alguna?

**Enviado al TTS:** Tengo la opción de BONAI LCD Cargador de Pilas por catorce euros con noventa y siete céntimos, el quitapelusas Severin por treinta y ocho euros con dieciséis céntimos, el empujador recargable Latigo por cuarenta y dos euros con ochenta y seis céntimos, el pack de cepillos de dientes Philips por veinticinco euros con trece céntimos y el pica veterinario PICAAVISPA por nueve euros con setenta y nueve céntimos. ¿Te interesa alguna?

- ✔ `cart(empty=true)` — carrito: vacío

> `@elegidas` = `B07F58PXYR` (candidate:1): BONAI LCD Cargador de Pilas Inteligente para AA/AAA/SC/C/D /9V Ni-MH/Ni-CD, 4 Ranura Independiente y Auto-Detección, Universal Cargador Pilas con Función de Descarga (Cargador de batería AC)

> **Suceso externo:** la tienda deja `B07F58PXYR` (@elegidas) con precio 3,00 € y existencias 30.

## Turno 2 (5.0 s)

**Usuario (texto):** Ponme cuatro de la primera.

- `agregar_al_carrito(product_id="B07F58PXYR", cantidad=4)` → OK: hecho. Así queda el carrito. CARRITO: - id=B07F58PXYR | BONAI LCD Cargador de Pilas Inteligente para AA/AAA/SC/C/D /9V… | 4 unidades × 3,00 € = 12,00 € | existencias: 30 Total del carrito: 12,00 €

**Agente:** Hecho, añadidas cuatro unidades. El total del carrito es 12,00 euros. En el carrito hay 4 unidades de «BONAI LCD Cargador de Pilas Inteligente para AA/AAA/SC/C/D /9V…» a 3,00 € cada una, 12,00 €. Total: 12,00 €.

**Enviado al TTS:** Hecho, añadidas cuatro unidades. El total del carrito es doce euros. En el carrito hay cuatro unidades de BONAI LCD Cargador de Pilas Inteligente a tres euros cada una, doce euros. Total: doce euros.

- ✔ `cart(lines=[{"product": "@elegidas", "quantity": 4}])` — carrito: 4 × B07F58PXYR

## Turno 3 (1.9 s)

**Usuario (texto):** Quiero pagar.

- `cotizar()` → OK: cotización creada; falta la confirmación del usuario.

**Agente:** Te repito el pedido antes de registrarlo: 4 unidades de «BONAI LCD Cargador de Pilas Inteligente para AA/AAA/SC/C/D /9V…» a 3,00 € cada una, 12,00 €. Total: 12,00 €. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar. *(esperando confirmación)*

**Enviado al TTS:** Te repito el pedido antes de registrarlo: cuatro unidades de BONAI LCD Cargador de Pilas Inteligente a tres euros cada una, doce euros. Total: doce euros. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar.

- ✔ `awaiting_confirmation(value=true)` — esperando confirmación: sí
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 4 (4.9 s)

**Usuario (texto):** Perdona, eran 14, no 4.

- `cambiar_cantidad(product_id="B07F58PXYR", cantidad=14)` → OK: hecho. Así queda el carrito. CARRITO: - id=B07F58PXYR | BONAI LCD Cargador de Pilas Inteligente para AA/AAA/SC/C/D /9V… | 14 unidades × 3,00 € = 42,00 € | existencias: 30 Total del carrito: 42,00 €

**Agente:** Hecho, añadidas 10 unidades más. El total del carrito es 42,00 euros. En el carrito hay 14 unidades de «BONAI LCD Cargador de Pilas Inteligente para AA/AAA/SC/C/D /9V…» a 3,00 € cada una, 42,00 €. Total: 42,00 €.

**Enviado al TTS:** Hecho, añadidas diez unidades más. El total del carrito es cuarenta y dos euros. En el carrito hay catorce unidades de BONAI LCD Cargador de Pilas Inteligente a tres euros cada una, cuarenta y dos euros. Total: cuarenta y dos euros.

- ✔ `orders(count=0)` — pedidos registrados: 0
- ✔ `cart(lines=[{"product": "@elegidas", "quantity": 14}])` — carrito: 14 × B07F58PXYR

## Turno 5 (1.9 s)

**Usuario (texto):** Ya está, tramítalo.

- `cotizar()` → OK: cotización creada; falta la confirmación del usuario.

**Agente:** Te repito el pedido antes de registrarlo: 14 unidades de «BONAI LCD Cargador de Pilas Inteligente para AA/AAA/SC/C/D /9V…» a 3,00 € cada una, 42,00 €. Total: 42,00 €. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar. *(esperando confirmación)*

**Enviado al TTS:** Te repito el pedido antes de registrarlo: catorce unidades de BONAI LCD Cargador de Pilas Inteligente a tres euros cada una, cuarenta y dos euros. Total: cuarenta y dos euros. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar.

- ✔ `awaiting_confirmation(value=true)` — esperando confirmación: sí
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 6 (0.0 s)

**Usuario (texto):** Sí.

- `confirmar_pedido(quote_id="01cf2711ccb046749812b01f19a1cd15")` → OK: pedido registrado

**Agente:** Pedido número 1 registrado: 14 unidades de «BONAI LCD Cargador de Pilas Inteligente para AA/AAA/SC/C/D /9V…» a 3,00 € cada una, 42,00 €. Total: 42,00 €. Gracias por tu compra.

**Enviado al TTS:** Pedido número uno registrado: catorce unidades de BONAI LCD Cargador de Pilas Inteligente a tres euros cada una, cuarenta y dos euros. Total: cuarenta y dos euros. Gracias por tu compra.

- ✔ `orders(count=1)` — pedidos registrados: 1

## Comprobaciones finales

- ✔ `orders(count=1)` — pedidos registrados: 1
- ✔ `order(lines=[{"product": "@elegidas", "quantity": 14}], total_cents=4200)` — pedido 1: 14 × B07F58PXYR; total 4200 céntimos
- ✔ `stock(product="@elegidas", equals=16)` — existencias de B07F58PXYR: 16
- ✔ `cart(empty=true)` — carrito: vacío

## Violaciones de restricciones

- Ninguna.

## Estado final de la tienda

- Pedido 1: total 42,00 €
  - pedido 1: 14 × `B07F58PXYR` a 3,00 €
- Inventario `B07F58PXYR`: 45 → 16
- Líneas de carrito pendientes: 0

## Latencia por turno (segundos)

| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total | Audio de respuesta |
|---|---|---|---|---|---|---|---|
| 1 | 0.00 | 0.03 | 9.07 | 0.04 | 0.00 | 9.13 | 0.0 s |
| 2 | 0.00 | 0.00 | 4.96 | 0.05 | 0.00 | 5.00 | 0.0 s |
| 3 | 0.00 | 0.00 | 1.82 | 0.04 | 0.00 | 1.85 | 0.0 s |
| 4 | 0.00 | 0.00 | 4.89 | 0.05 | 0.00 | 4.94 | 0.0 s |
| 5 | 0.00 | 0.00 | 1.85 | 0.04 | 0.00 | 1.89 | 0.0 s |
| 6 | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 | 0.03 | 0.0 s |
| **Media de los turnos con LLM (5)** | 0.00 | 0.01 | 4.52 | 0.04 | 0.00 | 4.56 | |
| **Media de los turnos sin LLM (1)** | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 | 0.03 | |

