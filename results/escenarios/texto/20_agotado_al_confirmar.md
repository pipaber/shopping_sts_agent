# 20_agotado_al_confirmar — Producto agotado entre la cotización y la confirmación

- Veredicto: **fallo**
- Entrada: texto
- Tipo: `agotado_al_confirmar`
- Qué se prueba: Con la cotización pendiente, el producto se agota. La confirmación debe rechazarse sin cambios y el agente debe proponer alternativas con existencias. El usuario cambia el producto por la primera alternativa y compra.

## Turno 1 (7.7 s)

**Usuario (texto):** Busco un cuaderno de tapa dura.

- `buscar_productos(consulta="cuaderno tapa dura")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B08VMR6YL7 | Arteza Cuaderno de Dibujo, 15 x 20 cm [Set de 2, Azul Cobalto y Gris], Pack Cuadernos de Dibujo, Diarios de Tapa Dura con Papel de Escribir en Blanco [96 Hojas] | marca: ARTEZA | color: Azul cobalto y gris | precio: 10,9…
- `responder(texto="Tengo el Arteza de 25,91 € y el Eachgoo de 43,88 €. ¿Te interesa alguno?")` → RECHAZADO: [cifra_sin_sustento] En tu respuesta hay cifras que no aparecen en los datos (25.91). Usa solo cifras de CANDIDATOS, CARRITO o de un RESULTADO, sin hacer cuentas; si te falta un dato de un producto, consúltalo con detalle_producto o di que no consta.

**Agente:** Tengo el Arteza por 10,95 € y el Eachgoo por 43,88 €. ¿Te interesa alguno?

**Enviado al TTS:** Tengo el Arteza por diez euros con noventa y cinco céntimos y el Eachgoo por cuarenta y tres euros con ochenta y ocho céntimos. ¿Te interesa alguno?

- ✔ `cart(empty=true)` — carrito: vacío

> `@elegido` = `B08VMR6YL7` (candidate:1): Arteza Cuaderno de Dibujo, 15 x 20 cm [Set de 2, Azul Cobalto y Gris], Pack Cuadernos de Dibujo, Diarios de Tapa Dura con Papel de Escribir en Blanco [96 Hojas]

> **Suceso externo:** la tienda deja `B08VMR6YL7` (@elegido) con precio 6,00 € y existencias 5.

## Turno 2 (4.7 s)

**Usuario (texto):** Añade dos del primero.

- `agregar_al_carrito(product_id="B08VMR6YL7", cantidad=2)` → OK: hecho. Así queda el carrito. CARRITO: - id=B08VMR6YL7 | Arteza Cuaderno de Dibujo, 15 x 20 cm [Set de 2, Azul Cobalto y… | 2 unidades × 6,00 € = 12,00 € | existencias: 5 Total del carrito: 12,00 €

**Agente:** Hecho, añadidas dos unidades. En el carrito hay 2 unidades de «Arteza Cuaderno de Dibujo, 15 x 20 cm [Set de 2, Azul Cobalto y…» a 6,00 € cada una, 12,00 €. Total: 12,00 €.

**Enviado al TTS:** Hecho, añadidas dos unidades. En el carrito hay dos unidades de Arteza Cuaderno de Dibujo a seis euros cada una, doce euros. Total: doce euros.

- ✔ `cart(lines=[{"product": "@elegido", "quantity": 2}])` — carrito: 2 × B08VMR6YL7

## Turno 3 (2.3 s)

**Usuario (texto):** Cierra el pedido.

- `cotizar()` → OK: cotización creada; falta la confirmación del usuario.

**Agente:** Te repito el pedido antes de registrarlo: 2 unidades de «Arteza Cuaderno de Dibujo, 15 x 20 cm [Set de 2, Azul Cobalto y…» a 6,00 € cada una, 12,00 €. Total: 12,00 €. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar. *(esperando confirmación)*

**Enviado al TTS:** Te repito el pedido antes de registrarlo: dos unidades de Arteza Cuaderno de Dibujo a seis euros cada una, doce euros. Total: doce euros. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar.

- ✔ `awaiting_confirmation(value=true)` — esperando confirmación: sí
- ✔ `orders(count=0)` — pedidos registrados: 0

> **Suceso externo:** la tienda deja `B08VMR6YL7` (@elegido) con existencias 0.

## Turno 4 (0.0 s)

**Usuario (texto):** Sí.

- `confirmar_pedido(quote_id="48d24ab95d374917ad313465ce2a49fb")` → RECHAZADO: [agotado] El producto B08VMR6YL7 está agotado.

**Agente:** No he registrado el pedido porque la tienda cambió después de la cotización. «Arteza Cuaderno de Dibujo, 15 x 20 cm [Set de 2, Azul Cobalto y…» se ha agotado. Como alternativa tengo: «Arteza Cuaderno de Dibujo, 15 x 20 cm [Set de 3: Rosa Claro, Rosa…» a 10,16 €, con 39 en existencias; «Arteza Cuaderno de dibujo, 5.5x8.5” (14 x 21,6 cm), pack 3 blocs de…» a 11,47 €, con 43 en existencias; «Arteza Bloc de dibujo para pintura acrílica | Tamaño A3 | 16 hojas |…» a 15,18 €, con 2 en existencias. ¿Qué prefieres?

**Enviado al TTS:** No he registrado el pedido porque la tienda cambió después de la cotización. Arteza Cuaderno de Dibujo se ha agotado. Como alternativa tengo: Arteza Cuaderno de Dibujo a diez euros con dieciséis céntimos, con treinta y nueve en existencias, Arteza Cuaderno de dibujo a once euros con cuarenta y siete céntimos, con cuarenta y tres en existencias, Arteza Bloc de dibujo para pintura acrílica a quince euros con dieciocho céntimos, con dos en existencias. ¿Qué prefieres?

- ✔ `orders(count=0)` — pedidos registrados: 0
- ✔ `rejected(code="agotado")` — rechazos del turno: ['agotado']
- ✔ `offered_alternative(instead_of="@elegido")` — alternativas con existencias citadas: ['B08VMTLR4V', 'B07XCPXLBW', 'B084677T8L']
- ✔ `cart(lines=[{"product": "@elegido", "quantity": 2}])` — carrito: 2 × B08VMR6YL7

> `@alternativa` = `B08VMTLR4V` (candidate:1): Arteza Cuaderno de Dibujo, 15 x 20 cm [Set de 3: Rosa Claro, Rosa Oscuro, Granate], Pack Cuadernos de Dibujo, Diarios de Tapa Dura, con Rayas, en Blanco y con Puntos [96 Hojas]

## Turno 5 (6.4 s)

**Usuario (texto):** Quita ese cuaderno y ponme dos de la primera alternativa.

- `quitar_del_carrito(product_id="B08VMR6YL7")` → OK: hecho. Así queda el carrito. CARRITO: vacío
- `agregar_al_carrito(product_id="B07XCPXLBW", cantidad=2)` → OK: hecho. Así queda el carrito. CARRITO: - id=B07XCPXLBW | Arteza Cuaderno de dibujo, 5.5x8.5” (14 x 21,6 cm), pack 3 blocs de… | 2 unidades × 11,47 € = 22,94 € | existencias: 43 Total del carrito: 22,94 €

**Agente:** Hecho, añadidas dos unidades. En el carrito hay 2 unidades de «Arteza Cuaderno de dibujo, 5.5x8.5” (14 x 21,6 cm), pack 3 blocs de…» a 11,47 € cada una, 22,94 €. Total: 22,94 €.

**Enviado al TTS:** Hecho, añadidas dos unidades. En el carrito hay dos unidades de Arteza Cuaderno de dibujo a once euros con cuarenta y siete céntimos cada una, veintidós euros con noventa y cuatro céntimos. Total: veintidós euros con noventa y cuatro céntimos.

- ✘ `cart(lines=[{"product": "@alternativa", "quantity": 2}])` — carrito: 2 × B07XCPXLBW

## Turno 6 (2.9 s)

**Usuario (texto):** Cierra el pedido.

- `cotizar()` → OK: cotización creada; falta la confirmación del usuario.

**Agente:** Te repito el pedido antes de registrarlo: 2 unidades de «Arteza Cuaderno de dibujo, 5.5x8.5” (14 x 21,6 cm), pack 3 blocs de…» a 11,47 € cada una, 22,94 €. Total: 22,94 €. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar. *(esperando confirmación)*

**Enviado al TTS:** Te repito el pedido antes de registrarlo: dos unidades de Arteza Cuaderno de dibujo a once euros con cuarenta y siete céntimos cada una, veintidós euros con noventa y cuatro céntimos. Total: veintidós euros con noventa y cuatro céntimos. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar.

- ✔ `awaiting_confirmation(value=true)` — esperando confirmación: sí
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 7 (0.0 s)

**Usuario (texto):** Sí.

- `confirmar_pedido(quote_id="41c39b7a1a3b454e9a2b727a2757925e")` → OK: pedido registrado

**Agente:** Pedido número 1 registrado: 2 unidades de «Arteza Cuaderno de dibujo, 5.5x8.5” (14 x 21,6 cm), pack 3 blocs de…» a 11,47 € cada una, 22,94 €. Total: 22,94 €. Gracias por tu compra.

**Enviado al TTS:** Pedido número uno registrado: dos unidades de Arteza Cuaderno de dibujo a once euros con cuarenta y siete céntimos cada una, veintidós euros con noventa y cuatro céntimos. Total: veintidós euros con noventa y cuatro céntimos. Gracias por tu compra.

- ✔ `orders(count=1)` — pedidos registrados: 1

## Comprobaciones finales

- ✔ `orders(count=1)` — pedidos registrados: 1
- ✔ `order(lines=[{"not": "@elegido", "quantity": 2}])` — pedido 1: 2 × B07XCPXLBW; total 2294 céntimos
- ✔ `stock(product="@elegido", equals=0)` — existencias de B08VMR6YL7: 0
- ✔ `cart(empty=true)` — carrito: vacío

## Violaciones de restricciones

- Ninguna.

## Estado final de la tienda

- Pedido 1: total 22,94 €
  - pedido 1: 2 × `B07XCPXLBW` a 11,47 €
- Inventario `B07XCPXLBW`: 43 → 41
- Inventario `B08VMR6YL7`: 4 → 0
- Líneas de carrito pendientes: 0

## Latencia por turno (segundos)

| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total | Audio de respuesta |
|---|---|---|---|---|---|---|---|
| 1 | 0.00 | 0.03 | 7.62 | 0.03 | 0.00 | 7.68 | 0.0 s |
| 2 | 0.00 | 0.00 | 4.62 | 0.05 | 0.00 | 4.67 | 0.0 s |
| 3 | 0.00 | 0.00 | 2.30 | 0.03 | 0.00 | 2.33 | 0.0 s |
| 4 | 0.00 | 0.03 | 0.00 | 0.01 | 0.00 | 0.04 | 0.0 s |
| 5 | 0.00 | 0.00 | 6.37 | 0.08 | 0.00 | 6.44 | 0.0 s |
| 6 | 0.00 | 0.00 | 2.81 | 0.04 | 0.00 | 2.85 | 0.0 s |
| 7 | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 | 0.03 | 0.0 s |
| **Media de los turnos con LLM (5)** | 0.00 | 0.01 | 4.74 | 0.04 | 0.00 | 4.79 | |
| **Media de los turnos sin LLM (2)** | 0.00 | 0.01 | 0.00 | 0.02 | 0.00 | 0.03 | |

