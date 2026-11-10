# 11_rechazo_confirmacion — Rechazo en la confirmación

- Veredicto: **correcto**
- Entrada: texto
- Tipo: `rechazo_confirmacion`
- Qué se prueba: El usuario llega a la cotización y contesta que no. No debe registrarse ningún pedido y el carrito debe quedar como estaba.

## Turno 1 (6.8 s)

**Usuario (texto):** Busco unas bombillas LED.

- `buscar_productos(consulta="bombillas LED")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B01KHILJ5O | Philips - Bombilla LED cristal 50W, GU10, luz blanca cálida, transparente, no regulable, pack 6 | marca: Philips | color: Blanco Cálido | precio: 14,22 € | existencias: 22 | características (extracto): Con una vida útil …

**Agente:** Tengo la bombilla LED Philips por 14,22 euros, la de Global Fortune por 17,01 euros, la de Amazingdeal365 por 10,83 euros, la de CAR WORK BOX por 63,71 euros y la de MENTA por 24,96 euros. ¿Te interesa alguna?

**Enviado al TTS:** Tengo la bombilla LED Philips por catorce euros con veintidós céntimos, la de Global Fortune por diecisiete euros con un céntimo, la de Amazingdeal365 por diez euros con ochenta y tres céntimos, la de CAR WORK BOX por sesenta y tres euros con setenta y un céntimos y la de MENTA por veinticuatro euros con noventa y seis céntimos. ¿Te interesa alguna?

- ✔ `cart(empty=true)` — carrito: vacío

> `@elegidas` = `B01KHILJ5O` (candidate:1): Philips - Bombilla LED cristal 50W, GU10, luz blanca cálida, transparente, no regulable, pack 6

> **Suceso externo:** la tienda deja `B01KHILJ5O` (@elegidas) con precio 6,00 € y existencias 20.

## Turno 2 (4.7 s)

**Usuario (texto):** Añade dos de la primera opción.

- `agregar_al_carrito(product_id="B01KHILJ5O", cantidad=2)` → OK: hecho. Así queda el carrito. CARRITO: - id=B01KHILJ5O | Philips - Bombilla LED cristal 50W, GU10, luz blanca cálida… | 2 unidades × 6,00 € = 12,00 € | existencias: 20 Total del carrito: 12,00 €

**Agente:** Hecho, añadidas dos unidades. En el carrito hay 2 unidades de «Philips - Bombilla LED cristal 50W, GU10, luz blanca cálida…» a 6,00 € cada una, 12,00 €. Total: 12,00 €.

**Enviado al TTS:** Hecho, añadidas dos unidades. En el carrito hay dos unidades de Philips a seis euros cada una, doce euros. Total: doce euros.

- ✔ `cart(lines=[{"product": "@elegidas", "quantity": 2}])` — carrito: 2 × B01KHILJ5O

## Turno 3 (2.3 s)

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
| 1 | 0.00 | 0.04 | 6.72 | 0.03 | 0.00 | 6.78 | 0.0 s |
| 2 | 0.00 | 0.00 | 4.60 | 0.05 | 0.00 | 4.65 | 0.0 s |
| 3 | 0.00 | 0.00 | 2.22 | 0.04 | 0.00 | 2.26 | 0.0 s |
| 4 | 0.00 | 0.00 | 0.00 | 0.01 | 0.00 | 0.01 | 0.0 s |
| **Media de los turnos con LLM (3)** | 0.00 | 0.01 | 4.51 | 0.04 | 0.00 | 4.57 | |
| **Media de los turnos sin LLM (1)** | 0.00 | 0.00 | 0.00 | 0.01 | 0.00 | 0.01 | |

