# 06_cambio_stock_confirmacion_repetida — Cambio de stock entre cotización y confirmación, y confirmación repetida

- Veredicto: **fallo**
- Entrada: texto
- Tipo: `cambio_stock_confirmacion_repetida`
- Qué se prueba: Con la cotización de tres unidades pendiente, la tienda se queda con una sola. La confirmación debe rechazarse sin tocar nada y ofrecer una salida. El usuario lo deja en una unidad, confirma y repite el sí: debe haber un único pedido.

## Turno 1 (7.5 s)

**Usuario (texto):** Busco una lámpara de escritorio LED.

- `buscar_productos(consulta="lámpara escritorio LED")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B085CHJ9BD | Lámpara Escritorio LED, Flexo de Escritorio, La luz natural protege los ojos, Lampara led Escritorio regulable con puerto de carga USB, 5 Modos, 10 Niveles de Brillo,Temporizador de 30/60min | marca: SLATOR | color: Negr…

**Agente:** Tengo la lámpara de escritorio LED SLATOR por 44,20 €, la SENXINGYAN por 36,61 €, la SOFIL por 38,74 €, la Prtukyt por 23,86 € y la JUKSTG por 34,86 €. ¿Te interesa alguna?

**Enviado al TTS:** Tengo la lámpara de escritorio LED SLATOR por cuarenta y cuatro euros con veinte céntimos, la SENXINGYAN por treinta y seis euros con sesenta y un céntimos, la SOFIL por treinta y ocho euros con setenta y cuatro céntimos, la Prtukyt por veintitrés euros con ochenta y seis céntimos y la JUKSTG por treinta y cuatro euros con ochenta y seis céntimos. ¿Te interesa alguna?

- ✔ `cart(empty=true)` — carrito: vacío

> `@elegida` = `B085CHJ9BD` (candidate:1): Lámpara Escritorio LED, Flexo de Escritorio, La luz natural protege los ojos, Lampara led Escritorio regulable con puerto de carga USB, 5 Modos, 10 Niveles de Brillo,Temporizador de 30/60min

> **Suceso externo:** la tienda deja `B085CHJ9BD` (@elegida) con precio 15,00 € y existencias 10.

## Turno 2 (5.2 s)

**Usuario (texto):** Añade tres de la primera.

- `agregar_al_carrito(product_id="B085CHJ9BD", cantidad=3)` → OK: hecho. Así queda el carrito. CARRITO: - id=B085CHJ9BD | Lámpara Escritorio LED, Flexo de Escritorio, La luz natural protege… | 3 unidades × 15,00 € = 45,00 € | existencias: 10 Total del carrito: 45,00 €

**Agente:** Hecho, añadidas tres unidades. El total es 45,00 €. En el carrito hay 3 unidades de «Lámpara Escritorio LED, Flexo de Escritorio, La luz natural protege…» a 15,00 € cada una, 45,00 €. Total: 45,00 €.

**Enviado al TTS:** Hecho, añadidas tres unidades. El total es cuarenta y cinco euros. En el carrito hay tres unidades de Lámpara Escritorio LED a quince euros cada una, cuarenta y cinco euros. Total: cuarenta y cinco euros.

- ✔ `cart(lines=[{"product": "@elegida", "quantity": 3}])` — carrito: 3 × B085CHJ9BD

## Turno 3 (2.4 s)

**Usuario (texto):** Quiero cerrar el pedido.

- `cotizar()` → OK: cotización creada; falta la confirmación del usuario.

**Agente:** Te repito el pedido antes de registrarlo: 3 unidades de «Lámpara Escritorio LED, Flexo de Escritorio, La luz natural protege…» a 15,00 € cada una, 45,00 €. Total: 45,00 €. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar. *(esperando confirmación)*

**Enviado al TTS:** Te repito el pedido antes de registrarlo: tres unidades de Lámpara Escritorio LED a quince euros cada una, cuarenta y cinco euros. Total: cuarenta y cinco euros. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar.

- ✔ `awaiting_confirmation(value=true)` — esperando confirmación: sí
- ✔ `orders(count=0)` — pedidos registrados: 0

> **Suceso externo:** la tienda deja `B085CHJ9BD` (@elegida) con existencias 1.

## Turno 4 (0.0 s)

**Usuario (texto):** Sí.

- `confirmar_pedido(quote_id="ab2b5b77b4024012a9a4eb7b9dcfc403")` → RECHAZADO: [stock_insuficiente] Solo queda 1 unidad del producto B085CHJ9BD y se pidieron 3.

**Agente:** No he registrado el pedido porque la tienda cambió después de la cotización. De «Lámpara Escritorio LED, Flexo de Escritorio, La luz natural protege…» solo queda 1 unidad y habías pedido 3. Puedo dejarlo en 1. Como alternativa tengo: «Lámpara Escritorio LED, Flexo de Escritorio (Cuidado Ocular, Puerto…» a 23,23 €, con 16 en existencias; «Lámpara Escritorio LED,JUKSTG 5 Modos 10 Niveles de Brillo Lámpara de…» a 34,86 €, con 25 en existencias; «Lámpara de escritorio LED Lámpara de lectura de brazo Eye-Care…» a 23,86 €, con 34 en existencias. ¿Qué prefieres?

**Enviado al TTS:** No he registrado el pedido porque la tienda cambió después de la cotización. De Lámpara Escritorio LED solo queda una unidad y habías pedido tres. Puedo dejarlo en uno. Como alternativa tengo: Lámpara Escritorio LED a veintitrés euros con veintitrés céntimos, con dieciséis en existencias, Lámpara Escritorio LED a treinta y cuatro euros con ochenta y seis céntimos, con veinticinco en existencias, Lámpara de escritorio LED Lámpara de lectura a veintitrés euros con ochenta y seis céntimos, con treinta y cuatro en existencias. ¿Qué prefieres?

- ✔ `orders(count=0)` — pedidos registrados: 0
- ✔ `rejected(code="stock_insuficiente")` — rechazos del turno: ['stock_insuficiente']
- ✔ `cart(lines=[{"product": "@elegida", "quantity": 3}])` — carrito: 3 × B085CHJ9BD
- ✔ `stock(product="@elegida", equals=1)` — existencias de B085CHJ9BD: 1

## Turno 5 (4.1 s)

**Usuario (texto):** Vale, déjalo en una.

- `quitar_del_carrito(product_id="B085CHJ9BD")` → OK: hecho. Así queda el carrito. CARRITO: vacío

**Agente:** Hecho, el carrito está vacío. El carrito está vacío.

**Enviado al TTS:** Hecho, el carrito está vacío. El carrito está vacío.

- ✘ `cart(lines=[{"product": "@elegida", "quantity": 1}])` — carrito: vacío
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 6 (3.9 s)

**Usuario (texto):** Cierra el pedido.

- `cotizar()` → RECHAZADO: [carrito_vacio] El carrito está vacío; no hay nada que cotizar.

**Agente:** El carrito está vacío. ¿Quieres añadir algo?

**Enviado al TTS:** El carrito está vacío. ¿Quieres añadir algo?

- ✘ `awaiting_confirmation(value=true)` — esperando confirmación: no
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 7 (3.7 s)

**Usuario (texto):** Sí.

- `cotizar()` → RECHAZADO: [carrito_vacio] El carrito está vacío; no hay nada que cotizar.

**Agente:** El carrito está vacío. ¿Quieres añadir algo?

**Enviado al TTS:** El carrito está vacío. ¿Quieres añadir algo?

- ✘ `orders(count=1)` — pedidos registrados: 0

## Turno 8 (7.1 s)

**Usuario (texto):** Sí.

- `buscar_productos(consulta="lámpara escritorio")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B085CHJ9BD | Lámpara Escritorio LED, Flexo de Escritorio, La luz natural protege los ojos, Lampara led Escritorio regulable con puerto de carga USB, 5 Modos, 10 Niveles de Brillo,Temporizador de 30/60min | marca: SLATOR | color: Negr…

**Agente:** Tengo la lámpara de escritorio SLATOR por 15 euros, la JUKSTG por 34,86 y la SENXINGYAN por 36,61. ¿Te interesa alguna?

**Enviado al TTS:** Tengo la lámpara de escritorio SLATOR por quince euros, la JUKSTG por treinta y cuatro coma ochenta y seis y la SENXINGYAN por treinta y seis coma sesenta y uno. ¿Te interesa alguna?

- ✘ `orders(count=1)` — pedidos registrados: 0

## Comprobaciones finales

- ✘ `orders(count=1)` — pedidos registrados: 0
- ✘ `order(lines=[{"product": "@elegida", "quantity": 1}], total_cents=1500)` — no hay ningún pedido
- ✘ `stock(product="@elegida", equals=0)` — existencias de B085CHJ9BD: 1
- ✔ `cart(empty=true)` — carrito: vacío

## Violaciones de restricciones

- Ninguna.

## Estado final de la tienda

- Inventario `B085CHJ9BD`: 34 → 1
- Líneas de carrito pendientes: 0

## Latencia por turno (segundos)

| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total | Audio de respuesta |
|---|---|---|---|---|---|---|---|
| 1 | 0.00 | 0.04 | 7.42 | 0.03 | 0.00 | 7.49 | 0.0 s |
| 2 | 0.00 | 0.00 | 5.14 | 0.05 | 0.00 | 5.19 | 0.0 s |
| 3 | 0.00 | 0.00 | 2.32 | 0.04 | 0.00 | 2.36 | 0.0 s |
| 4 | 0.00 | 0.03 | 0.00 | 0.01 | 0.00 | 0.04 | 0.0 s |
| 5 | 0.00 | 0.00 | 4.01 | 0.05 | 0.00 | 4.07 | 0.0 s |
| 6 | 0.00 | 0.00 | 3.88 | 0.03 | 0.00 | 3.91 | 0.0 s |
| 7 | 0.00 | 0.00 | 3.68 | 0.03 | 0.00 | 3.71 | 0.0 s |
| 8 | 0.00 | 0.04 | 7.07 | 0.03 | 0.00 | 7.14 | 0.0 s |
| **Media de los turnos con LLM (7)** | 0.00 | 0.01 | 4.79 | 0.04 | 0.00 | 4.84 | |
| **Media de los turnos sin LLM (1)** | 0.00 | 0.03 | 0.00 | 0.01 | 0.00 | 0.04 | |

