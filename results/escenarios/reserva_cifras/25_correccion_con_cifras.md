# 25_correccion_con_cifras — Corregir una cantidad con cifras antes de confirmar

- Veredicto: **correcto**
- Entrada: texto
- Tipo: `correccion_con_cifras`
- Qué se prueba: Escenario de reserva, escrito antes de corregir el agente y sin ejecutarlo. Con la cotización pendiente, el usuario corrige la cantidad escribiendo los números con cifras («Perdona, eran 14, no 4.»), como los escribe a veces el ASR. El agente debe cambiar la cantidad, no fijar un presupuesto; el pedido final lleva catorce.

## Turno 1 (7.9 s)

**Usuario (texto):** Necesito unas pilas recargables.

- `buscar_productos(consulta="pilas recargables")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B077CTJZG7 | PRITECH - Quitapelusas regargable USB Adecuado para Todas Las Prendas, con Orificios de 3 tamaños en la Rejilla para Pelusas de Cualquier tamaño Dos Posiciones. Modelo ES1048. (Azul) | marca: PRITECH | color: Azul | prec…

**Agente:** Tengo una opción de PRITECH por 5,11 euros, un cargador de pilas BONAI por 14,97 euros, y dos empujadores recargables de LATIGO, uno de 9,28 euros y otro de 17,92 euros. ¿Te interesa alguna?

**Enviado al TTS:** Tengo una opción de PRITECH por cinco euros con once céntimos, un cargador de pilas BONAI por catorce euros con noventa y siete céntimos, y dos empujadores recargables de LATIGO, uno de nueve euros con veintiocho céntimos y otro de diecisiete euros con noventa y dos céntimos. ¿Te interesa alguna?

- ✔ `cart(empty=true)` — carrito: vacío

> `@elegidas` = `B077CTJZG7` (candidate:1): PRITECH - Quitapelusas regargable USB Adecuado para Todas Las Prendas, con Orificios de 3 tamaños en la Rejilla para Pelusas de Cualquier tamaño Dos Posiciones. Modelo ES1048. (Azul)

> **Suceso externo:** la tienda deja `B077CTJZG7` (@elegidas) con precio 3,00 € y existencias 30.

## Turno 2 (5.0 s)

**Usuario (texto):** Ponme cuatro de la primera.

- `agregar_al_carrito(product_id="B077CTJZG7", cantidad=4)` → OK: hecho. Así queda el carrito. CARRITO: - id=B077CTJZG7 | PRITECH - Quitapelusas regargable USB Adecuado para Todas Las… | 4 unidades × 3,00 € = 12,00 € | existencias: 30 Total del carrito: 12,00 €

**Agente:** Hecho, añadidas cuatro unidades. El total es 12,00 euros. En el carrito hay 4 unidades de «PRITECH - Quitapelusas regargable USB Adecuado para Todas Las…» a 3,00 € cada una, 12,00 €. Total: 12,00 €.

**Enviado al TTS:** Hecho, añadidas cuatro unidades. El total es doce euros. En el carrito hay cuatro unidades de PRITECH a tres euros cada una, doce euros. Total: doce euros.

- ✔ `cart(lines=[{"product": "@elegidas", "quantity": 4}])` — carrito: 4 × B077CTJZG7

## Turno 3 (1.9 s)

**Usuario (texto):** Quiero pagar.

- `cotizar()` → OK: cotización creada; falta la confirmación del usuario.

**Agente:** Te repito el pedido antes de registrarlo: 4 unidades de «PRITECH - Quitapelusas regargable USB Adecuado para Todas Las…» a 3,00 € cada una, 12,00 €. Total: 12,00 €. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar. *(esperando confirmación)*

**Enviado al TTS:** Te repito el pedido antes de registrarlo: cuatro unidades de PRITECH a tres euros cada una, doce euros. Total: doce euros. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar.

- ✔ `awaiting_confirmation(value=true)` — esperando confirmación: sí
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 4 (7.1 s)

**Usuario (texto):** Perdona, eran 14, no 4.

- `cambiar_cantidad(product_id="B077CTJZG7", cantidad=14)` → OK: hecho. Así queda el carrito. CARRITO: - id=B077CTJZG7 | PRITECH - Quitapelusas regargable USB Adecuado para Todas Las… | 14 unidades × 3,00 € = 42,00 € | existencias: 30 Total del carrito: 42,00 €
- `responder(texto="Hecho, añadidas 10 unidades más. El total es 42,00 euros.")` → RECHAZADO: [cifra_sin_sustento] En tu respuesta hay cifras que no aparecen en los datos (10). Usa solo cifras de CANDIDATOS, CARRITO o de un RESULTADO, sin hacer cuentas; si te falta un dato de un producto, consúltalo con detalle_producto o di que no consta.

**Agente:** Perdona, no he podido completar tu petición. ¿Puedes decírmelo de otra forma? En el carrito hay 14 unidades de «PRITECH - Quitapelusas regargable USB Adecuado para Todas Las…» a 3,00 € cada una, 42,00 €. Total: 42,00 €.

**Enviado al TTS:** Perdona, no he podido completar tu petición. ¿Puedes decírmelo de otra forma? En el carrito hay catorce unidades de PRITECH a tres euros cada una, cuarenta y dos euros. Total: cuarenta y dos euros.

- ✔ `orders(count=0)` — pedidos registrados: 0
- ✔ `cart(lines=[{"product": "@elegidas", "quantity": 14}])` — carrito: 14 × B077CTJZG7

## Turno 5 (2.0 s)

**Usuario (texto):** Ya está, tramítalo.

- `cotizar()` → OK: cotización creada; falta la confirmación del usuario.

**Agente:** Te repito el pedido antes de registrarlo: 14 unidades de «PRITECH - Quitapelusas regargable USB Adecuado para Todas Las…» a 3,00 € cada una, 42,00 €. Total: 42,00 €. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar. *(esperando confirmación)*

**Enviado al TTS:** Te repito el pedido antes de registrarlo: catorce unidades de PRITECH a tres euros cada una, cuarenta y dos euros. Total: cuarenta y dos euros. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar.

- ✔ `awaiting_confirmation(value=true)` — esperando confirmación: sí
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 6 (0.0 s)

**Usuario (texto):** Sí.

- `confirmar_pedido(quote_id="ecc35fda56944dc8abc7536a2fe7fea5")` → OK: pedido registrado

**Agente:** Pedido número 1 registrado: 14 unidades de «PRITECH - Quitapelusas regargable USB Adecuado para Todas Las…» a 3,00 € cada una, 42,00 €. Total: 42,00 €. Gracias por tu compra.

**Enviado al TTS:** Pedido número uno registrado: catorce unidades de PRITECH a tres euros cada una, cuarenta y dos euros. Total: cuarenta y dos euros. Gracias por tu compra.

- ✔ `orders(count=1)` — pedidos registrados: 1

## Comprobaciones finales

- ✔ `orders(count=1)` — pedidos registrados: 1
- ✔ `order(lines=[{"product": "@elegidas", "quantity": 14}], total_cents=4200)` — pedido 1: 14 × B077CTJZG7; total 4200 céntimos
- ✔ `stock(product="@elegidas", equals=16)` — existencias de B077CTJZG7: 16
- ✔ `cart(empty=true)` — carrito: vacío

## Violaciones de restricciones

- Ninguna.

## Estado final de la tienda

- Pedido 1: total 42,00 €
  - pedido 1: 14 × `B077CTJZG7` a 3,00 €
- Inventario `B077CTJZG7`: 4 → 16
- Líneas de carrito pendientes: 0

## Latencia por turno (segundos)

| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total | Audio de respuesta |
|---|---|---|---|---|---|---|---|
| 1 | 0.00 | 0.03 | 7.88 | 0.04 | 0.00 | 7.94 | 0.0 s |
| 2 | 0.00 | 0.00 | 4.94 | 0.05 | 0.00 | 4.99 | 0.0 s |
| 3 | 0.00 | 0.00 | 1.90 | 0.04 | 0.00 | 1.94 | 0.0 s |
| 4 | 0.00 | 0.00 | 7.05 | 0.05 | 0.00 | 7.10 | 0.0 s |
| 5 | 0.00 | 0.00 | 1.92 | 0.04 | 0.00 | 1.96 | 0.0 s |
| 6 | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 | 0.03 | 0.0 s |
| **Media de los turnos con LLM (5)** | 0.00 | 0.01 | 4.74 | 0.04 | 0.00 | 4.79 | |
| **Media de los turnos sin LLM (1)** | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 | 0.03 | |

