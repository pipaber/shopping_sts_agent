# 02_pedido_ambiguo — Pedido ambiguo que requiere aclaración

- Veredicto: **correcto**
- Entrada: texto
- Tipo: `pedido_ambiguo`
- Qué se prueba: El primer mensaje no dice qué producto se busca: el agente debe preguntar en lugar de suponer. Después el usuario concreta el producto y el presupuesto, y añade una unidad.

## Turno 1 (1.8 s)

**Usuario (texto):** Quiero comprar un regalo para mi hermana.

- `pedir_aclaracion(pregunta="¿Qué tipo de regalo tienes en mente para tu hermana?")` → OK: pregunta enviada al usuario

**Agente:** ¿Qué tipo de regalo tienes en mente para tu hermana?

**Enviado al TTS:** ¿Qué tipo de regalo tienes en mente para tu hermana?

- ✔ `asked_clarification()` — pidió aclaración
- ✔ `cart(empty=true)` — carrito: vacío
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 2 (7.8 s)

**Usuario (texto):** Unos auriculares bluetooth, y no quiero gastar más de 50 euros.

- `fijar_presupuesto(importe_eur=50)` → OK: presupuesto fijado en 50,00 €.
- `buscar_productos(consulta="auriculares bluetooth")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B081C31KV4 | Auriculares Bluetooth, 5.0 Auriculares Bluetooth In Ear Inalámbricos Auricular Estéreo en Oreja Manos Libres con Caja de Carga Portátil para Airpods Android/iPhone (Rosa1) | marca: Mgrett | color: Rosa1 | precio: 9,18 € …

**Agente:** Tengo auriculares Bluetooth de Mgrett por 9,18 euros, de WDGP por 32,06 euros, de TAIN por 9,84 euros, de GSBLBL por 25,15 euros y de Bose por 24,57 euros. ¿Te interesa alguno? He anotado un presupuesto de 50,00 €.

**Enviado al TTS:** Tengo auriculares Bluetooth de Mgrett por nueve euros con dieciocho céntimos, de WDGP por treinta y dos euros con seis céntimos, de TAIN por nueve euros con ochenta y cuatro céntimos, de GSBLBL por veinticinco euros con quince céntimos y de Bose por veinticuatro euros con cincuenta y siete céntimos. ¿Te interesa alguno? He anotado un presupuesto de cincuenta euros.

- ✔ `budget(cents=5000)` — presupuesto en el estado: 5000
- ✔ `cart(empty=true)` — carrito: vacío

> `@elegido` = `B081C31KV4` (candidate:1): Auriculares Bluetooth, 5.0 Auriculares Bluetooth In Ear Inalámbricos Auricular Estéreo en Oreja Manos Libres con Caja de Carga Portátil para Airpods Android/iPhone (Rosa1)

> **Suceso externo:** la tienda deja `B081C31KV4` (@elegido) con precio 19,90 € y existencias 20.

## Turno 3 (5.1 s)

**Usuario (texto):** Ponme uno del primero.

- `agregar_al_carrito(product_id="B081C31KV4", cantidad=1)` → OK: hecho. Así queda el carrito. CARRITO: - id=B081C31KV4 | Auriculares Bluetooth, 5.0 Auriculares Bluetooth In Ear Inalámbricos… | 1 unidad × 19,90 € = 19,90 € | existencias: 20 Total del carrito: 19,90 €

**Agente:** Hecho, añadido uno de los auriculares. El total es 19,90 €. En el carrito hay 1 unidad de «Auriculares Bluetooth, 5.0 Auriculares Bluetooth In Ear Inalámbricos…» a 19,90 € cada una, 19,90 €. Total: 19,90 €. Tu presupuesto es de 50,00 € y te quedan 30,10 €.

**Enviado al TTS:** Hecho, añadido uno de los auriculares. El total es diecinueve euros con noventa céntimos. En el carrito hay una unidad de Auriculares Bluetooth a diecinueve euros con noventa céntimos cada una, diecinueve euros con noventa céntimos. Total: diecinueve euros con noventa céntimos. Tu presupuesto es de cincuenta euros y te quedan treinta euros con diez céntimos.

- ✔ `cart(lines=[{"product": "@elegido", "quantity": 1}])` — carrito: 1 × B081C31KV4

## Comprobaciones finales

- ✔ `orders(count=0)` — pedidos registrados: 0
- ✔ `cart(lines=[{"product": "@elegido", "quantity": 1}])` — carrito: 1 × B081C31KV4
- ✔ `budget(cents=5000)` — presupuesto en el estado: 5000
- ✔ `stock(product="@elegido", equals=20)` — existencias de B081C31KV4: 20

## Violaciones de restricciones

- Ninguna.

## Estado final de la tienda

- Inventario `B081C31KV4`: 14 → 20
- Líneas de carrito pendientes: 1

## Latencia por turno (segundos)

| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total | Audio de respuesta |
|---|---|---|---|---|---|---|---|
| 1 | 0.00 | 0.00 | 1.82 | 0.02 | 0.00 | 1.85 | 0.0 s |
| 2 | 0.00 | 0.04 | 7.77 | 0.03 | 0.00 | 7.83 | 0.0 s |
| 3 | 0.00 | 0.00 | 5.05 | 0.05 | 0.00 | 5.10 | 0.0 s |
| **Media de los turnos con LLM (3)** | 0.00 | 0.01 | 4.88 | 0.03 | 0.00 | 4.93 | |

