# 11_rechazo_confirmacion — Rechazo en la confirmación

- Veredicto: **correcto**
- Entrada: texto
- Tipo: `rechazo_confirmacion`
- Qué se prueba: El usuario llega a la cotización y contesta que no. No debe registrarse ningún pedido y el carrito debe quedar como estaba.

## Turno 1 (7.8 s)

**Usuario (texto):** Busco unas bombillas LED.

- `buscar_productos(consulta="bombillas LED")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B01KHILJ5O | Philips - Bombilla LED cristal 50W, GU10, luz blanca cálida, transparente, no regulable, pack 6 | marca: Philips | color: Blanco Cálido | precio: 14,22 € | existencias: 22 | características (extracto): Con una vida útil …

**Agente:** Tengo estas opciones: bombillas LED de Philips por 14,22 euros, bombillas LED de Global Fortune por 17,01 euros, bombillas LED portátil por 10,83 euros, bombillas LED para coches por 63,71 euros y bombillas LED menta por 24,96 euros. ¿Cuál te interesa?

**Enviado al TTS:** Tengo estas opciones: bombillas LED de Philips por catorce euros con veintidós céntimos, bombillas LED de Global Fortune por diecisiete euros con un céntimo, bombillas LED portátil por diez euros con ochenta y tres céntimos, bombillas LED para coches por sesenta y tres euros con setenta y un céntimos y bombillas LED menta por veinticuatro euros con noventa y seis céntimos. ¿Cuál te interesa?

- ✔ `cart(empty=true)` — carrito: vacío

> `@elegidas` = `B01KHILJ5O` (candidate:1): Philips - Bombilla LED cristal 50W, GU10, luz blanca cálida, transparente, no regulable, pack 6

> **Suceso externo:** la tienda deja `B01KHILJ5O` (@elegidas) con precio 6,00 € y existencias 20.

## Turno 2 (5.1 s)

**Usuario (texto):** Añade dos de la primera opción.

- `agregar_al_carrito(product_id="B01KHILJ5O", cantidad=2)` → OK: hecho. Así queda el carrito. CARRITO: - id=B01KHILJ5O | Philips - Bombilla LED cristal 50W, GU10, luz blanca cálida… | 2 unidades × 6,00 € = 12,00 € | existencias: 20 Total del carrito: 12,00 €

**Agente:** Hecho, añadidas dos unidades. Ahora el total es 12,00 euros. En el carrito hay 2 unidades de «Philips - Bombilla LED cristal 50W, GU10, luz blanca cálida…» a 6,00 € cada una, 12,00 €. Total: 12,00 €.

**Enviado al TTS:** Hecho, añadidas dos unidades. Ahora el total es doce euros. En el carrito hay dos unidades de Philips a seis euros cada una, doce euros. Total: doce euros.

- ✔ `cart(lines=[{"product": "@elegidas", "quantity": 2}])` — carrito: 2 × B01KHILJ5O

## Turno 3 (2.2 s)

**Usuario (texto):** Cierra el pedido.

- `cotizar()` → OK: cotización creada; falta la confirmación del usuario.

**Agente:** Te repito el pedido antes de registrarlo: 2 unidades de «Philips - Bombilla LED cristal 50W, GU10, luz blanca cálida…» a 6,00 € cada una, 12,00 €. Total: 12,00 €. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar. *(esperando confirmación)*

**Enviado al TTS:** Te repito el pedido antes de registrarlo: dos unidades de Philips a seis euros cada una, doce euros. Total: doce euros. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar.

- ✔ `awaiting_confirmation(value=true)` — esperando confirmación: sí
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 4 (0.0 s)

**Usuario (texto):** No, cancélalo.

**Agente:** De acuerdo, no registro el pedido. Tu carrito sigue como estaba; dime si quieres cambiar algo.

**Enviado al TTS:** De acuerdo, no registro el pedido. Tu carrito sigue como estaba, dime si quieres cambiar algo.

- ✔ `orders(count=0)` — pedidos registrados: 0
- ✔ `awaiting_confirmation(value=false)` — esperando confirmación: no
- ✔ `cart(lines=[{"product": "@elegidas", "quantity": 2}])` — carrito: 2 × B01KHILJ5O

## Comprobaciones finales

- ✔ `orders(count=0)` — pedidos registrados: 0
- ✔ `cart(lines=[{"product": "@elegidas", "quantity": 2}])` — carrito: 2 × B01KHILJ5O
- ✔ `stock(product="@elegidas", equals=20)` — existencias de B01KHILJ5O: 20

## Violaciones de restricciones

- Ninguna.

## Estado final de la tienda

- Inventario `B01KHILJ5O`: 22 → 20
- Líneas de carrito pendientes: 1

## Latencia por turno (segundos)

| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total | Audio de respuesta |
|---|---|---|---|---|---|---|---|
| 1 | 0.00 | 0.06 | 7.74 | 0.03 | 0.00 | 7.83 | 0.0 s |
| 2 | 0.00 | 0.00 | 5.09 | 0.05 | 0.00 | 5.14 | 0.0 s |
| 3 | 0.00 | 0.00 | 2.12 | 0.04 | 0.00 | 2.16 | 0.0 s |
| 4 | 0.00 | 0.00 | 0.00 | 0.01 | 0.00 | 0.01 | 0.0 s |
| **Media de los turnos con LLM (3)** | 0.00 | 0.02 | 4.98 | 0.04 | 0.00 | 5.04 | |
| **Media de los turnos sin LLM (1)** | 0.00 | 0.00 | 0.00 | 0.01 | 0.00 | 0.01 | |

