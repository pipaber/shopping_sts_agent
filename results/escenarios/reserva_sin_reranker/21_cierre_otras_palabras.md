# 21_cierre_otras_palabras — Cerrar el pedido con otras palabras

- Veredicto: **correcto**
- Entrada: texto
- Tipo: `cierre_otras_palabras`
- Qué se prueba: Escenario de reserva, escrito antes de corregir el agente y sin ejecutarlo. El usuario pide cerrar la compra sin decir «cierra el pedido»: primero «Eso es todo, ya puedes tramitarlo» y, tras cancelar, «Listo, quiero pagar ya». Las dos veces el agente debe cotizar y esperar la confirmación.

## Turno 1 (8.5 s)

**Usuario (texto):** Busco una báscula de cocina.

- `buscar_productos(consulta="báscula cocina")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B08FB5D64D | Báscula digital Jooheli, de acero inoxidable, 15 kg/1 g, con gran superficie de pesaje y tara, báscula de cocina de alta precisión (plata) | marca: Jooheli | color: plata | precio: 22,56 € | existencias: 33 | característ…

**Agente:** Tengo la báscula digital Jooheli por 22,56 euros, la Raniaco por 14,65, la Cocogeneric verde por 22,71, la TOUSEEDA plata por 12,88 y la Amazon Basics negra por 11,74. ¿Te interesa alguna?

**Enviado al TTS:** Tengo la báscula digital Jooheli por veintidós euros con cincuenta y seis céntimos, la Raniaco por catorce coma sesenta y cinco, la Cocogeneric verde por veintidós coma setenta y uno, la TOUSEEDA plata por doce coma ochenta y ocho y la Amazon Basics negra por once coma setenta y cuatro. ¿Te interesa alguna?

- ✔ `cart(empty=true)` — carrito: vacío

> `@elegida` = `B08FB5D64D` (candidate:1): Báscula digital Jooheli, de acero inoxidable, 15 kg/1 g, con gran superficie de pesaje y tara, báscula de cocina de alta precisión (plata)

> **Suceso externo:** la tienda deja `B08FB5D64D` (@elegida) con precio 13,00 € y existencias 20.

## Turno 2 (5.5 s)

**Usuario (texto):** Añade una de la primera.

- `agregar_al_carrito(product_id="B08FB5D64D", cantidad=1)` → OK: hecho. Así queda el carrito. CARRITO: - id=B08FB5D64D | Báscula digital Jooheli, de acero inoxidable, 15 kg/1 g, con gran… | 1 unidad × 13,00 € = 13,00 € | existencias: 20 Total del carrito: 13,00 €

**Agente:** Hecho, añadida una unidad. El total del carrito es 13,00 €. En el carrito hay 1 unidad de «Báscula digital Jooheli, de acero inoxidable, 15 kg/1 g, con gran…» a 13,00 € cada una, 13,00 €. Total: 13,00 €.

**Enviado al TTS:** Hecho, añadida una unidad. El total del carrito es trece euros. En el carrito hay una unidad de Báscula digital Jooheli a trece euros cada una, trece euros. Total: trece euros.

- ✔ `cart(lines=[{"product": "@elegida", "quantity": 1}])` — carrito: 1 × B08FB5D64D

## Turno 3 (2.2 s)

**Usuario (texto):** Eso es todo, ya puedes tramitarlo.

- `cotizar()` → OK: cotización creada; falta la confirmación del usuario.

**Agente:** Te repito el pedido antes de registrarlo: 1 unidad de «Báscula digital Jooheli, de acero inoxidable, 15 kg/1 g, con gran…» a 13,00 € cada una, 13,00 €. Total: 13,00 €. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar. *(esperando confirmación)*

**Enviado al TTS:** Te repito el pedido antes de registrarlo: una unidad de Báscula digital Jooheli a trece euros cada una, trece euros. Total: trece euros. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar.

- ✔ `awaiting_confirmation(value=true)` — esperando confirmación: sí
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 4 (0.0 s)

**Usuario (texto):** No, espera.

**Agente:** De acuerdo, no registro el pedido. Tu carrito sigue como estaba; dime si quieres cambiar algo.

**Enviado al TTS:** De acuerdo, no registro el pedido. Tu carrito sigue como estaba, dime si quieres cambiar algo.

- ✔ `orders(count=0)` — pedidos registrados: 0
- ✔ `awaiting_confirmation(value=false)` — esperando confirmación: no
- ✔ `cart(lines=[{"product": "@elegida", "quantity": 1}])` — carrito: 1 × B08FB5D64D

## Turno 5 (2.3 s)

**Usuario (texto):** Listo, quiero pagar ya.

- `cotizar()` → OK: cotización creada; falta la confirmación del usuario.

**Agente:** Te repito el pedido antes de registrarlo: 1 unidad de «Báscula digital Jooheli, de acero inoxidable, 15 kg/1 g, con gran…» a 13,00 € cada una, 13,00 €. Total: 13,00 €. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar. *(esperando confirmación)*

**Enviado al TTS:** Te repito el pedido antes de registrarlo: una unidad de Báscula digital Jooheli a trece euros cada una, trece euros. Total: trece euros. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar.

- ✔ `awaiting_confirmation(value=true)` — esperando confirmación: sí
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 6 (0.0 s)

**Usuario (texto):** Sí.

- `confirmar_pedido(quote_id="2b658497162446e3b3d9b7d3f099ab4c")` → OK: pedido registrado

**Agente:** Pedido número 1 registrado: 1 unidad de «Báscula digital Jooheli, de acero inoxidable, 15 kg/1 g, con gran…» a 13,00 € cada una, 13,00 €. Total: 13,00 €. Gracias por tu compra.

**Enviado al TTS:** Pedido número uno registrado: una unidad de Báscula digital Jooheli a trece euros cada una, trece euros. Total: trece euros. Gracias por tu compra.

- ✔ `orders(count=1)` — pedidos registrados: 1

## Comprobaciones finales

- ✔ `orders(count=1)` — pedidos registrados: 1
- ✔ `order(lines=[{"product": "@elegida", "quantity": 1}], total_cents=1300)` — pedido 1: 1 × B08FB5D64D; total 1300 céntimos
- ✔ `stock(product="@elegida", equals=19)` — existencias de B08FB5D64D: 19
- ✔ `cart(empty=true)` — carrito: vacío

## Violaciones de restricciones

- Ninguna.

## Estado final de la tienda

- Pedido 1: total 13,00 €
  - pedido 1: 1 × `B08FB5D64D` a 13,00 €
- Inventario `B08FB5D64D`: 33 → 19
- Líneas de carrito pendientes: 0

## Latencia por turno (segundos)

| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total | Audio de respuesta |
|---|---|---|---|---|---|---|---|
| 1 | 0.00 | 0.03 | 8.45 | 0.04 | 0.00 | 8.52 | 0.0 s |
| 2 | 0.00 | 0.00 | 5.47 | 0.05 | 0.00 | 5.52 | 0.0 s |
| 3 | 0.00 | 0.00 | 2.21 | 0.03 | 0.00 | 2.24 | 0.0 s |
| 4 | 0.00 | 0.00 | 0.00 | 0.01 | 0.00 | 0.01 | 0.0 s |
| 5 | 0.00 | 0.00 | 2.25 | 0.04 | 0.00 | 2.29 | 0.0 s |
| 6 | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 | 0.03 | 0.0 s |
| **Media de los turnos con LLM (4)** | 0.00 | 0.01 | 4.59 | 0.04 | 0.00 | 4.64 | |
| **Media de los turnos sin LLM (2)** | 0.00 | 0.00 | 0.00 | 0.02 | 0.00 | 0.02 | |

