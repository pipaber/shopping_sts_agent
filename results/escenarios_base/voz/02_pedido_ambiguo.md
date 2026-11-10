# 02_pedido_ambiguo — Pedido ambiguo que requiere aclaración

- Veredicto: **correcto**
- Entrada: audio (sintéticos, hablante de prueba «Luis Moray» de XTTS-v2 (no es la voz del usuario))
- Tipo: `pedido_ambiguo`
- Qué se prueba: El primer mensaje no dice qué producto se busca: el agente debe preguntar en lugar de suponer. Después el usuario concreta el producto y el presupuesto, y añade una unidad.

## Turno 1 (3.5 s)

**Usuario (transcripción del ASR):** Quiero comprar un regalo para mi hermana.

- `pedir_aclaracion(pregunta="¿Qué tipo de regalo estás buscando para tu hermana?")` → OK: pregunta enviada al usuario

**Agente:** ¿Qué tipo de regalo estás buscando para tu hermana?

**Enviado al TTS:** ¿Qué tipo de regalo estás buscando para tu hermana?

- ✔ `asked_clarification()` — pidió aclaración
- ✔ `cart(empty=true)` — carrito: vacío
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 2 (15.2 s)

**Usuario (transcripción del ASR):** unos auriculares Bluetooth y no quiero gastar más de 50 euros.

**Texto correcto:** Unos auriculares bluetooth, y no quiero gastar más de 50 euros.

- `fijar_presupuesto(importe_eur=50)` → OK: presupuesto fijado en 50,00 €.
- `buscar_productos(consulta="auriculares Bluetooth")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B081C31KV4 | Auriculares Bluetooth, 5.0 Auriculares Bluetooth In Ear Inalámbricos Auricular Estéreo en Oreja Manos Libres con Caja de Carga Portátil para Airpods Android/iPhone (Rosa1) | marca: Mgrett | color: Rosa1 | precio: 9,18 € …

**Agente:** Tengo varios modelos de auriculares Bluetooth para ti. El primero, de Mgrett, cuesta 9,18 euros. El segundo, de TAIN, es 9,84 euros. El tercero, de WDGP, vale 32,06 euros. ¿Te interesa alguno de estos? He anotado un presupuesto de 50,00 €.

**Enviado al TTS:** Tengo varios modelos de auriculares Bluetooth para ti. El primero, de Mgrett, cuesta nueve euros con dieciocho céntimos. El segundo, de TAIN, es nueve euros con ochenta y cuatro céntimos. El tercero, de WDGP, vale treinta y dos euros con seis céntimos. ¿Te interesa alguno de estos? He anotado un presupuesto de cincuenta euros.

- ✔ `budget(cents=5000)` — presupuesto en el estado: 5000
- ✔ `cart(empty=true)` — carrito: vacío

> `@elegido` = `B081C31KV4` (candidate:1): Auriculares Bluetooth, 5.0 Auriculares Bluetooth In Ear Inalámbricos Auricular Estéreo en Oreja Manos Libres con Caja de Carga Portátil para Airpods Android/iPhone (Rosa1)

> **Suceso externo:** la tienda deja `B081C31KV4` (@elegido) con precio 19,90 € y existencias 20.

## Turno 3 (13.4 s)

**Usuario (transcripción del ASR):** Ponme uno del primero.

- `agregar_al_carrito(product_id="B081C31KV4", cantidad=1)` → OK: hecho. Así queda el carrito. CARRITO: - id=B081C31KV4 | Auriculares Bluetooth, 5.0 Auriculares Bluetooth In Ear Inalámbricos… | 1 unidad × 19,90 € = 19,90 € | existencias: 20 Total del carrito: 19,90 €

**Agente:** Hecho, añadido un auricular al carrito. En el carrito hay 1 unidad de «Auriculares Bluetooth, 5.0 Auriculares Bluetooth In Ear Inalámbricos…» a 19,90 € cada una, 19,90 €. Total: 19,90 €. Tu presupuesto es de 50,00 € y te quedan 30,10 €.

**Enviado al TTS:** Hecho, añadido un auricular al carrito. En el carrito hay una unidad de Auriculares Bluetooth a diecinueve euros con noventa céntimos cada una, diecinueve euros con noventa céntimos. Total: diecinueve euros con noventa céntimos. Tu presupuesto es de cincuenta euros y te quedan treinta euros con diez céntimos.

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
| 1 | 0.33 | 0.00 | 1.79 | 0.03 | 1.36 | 3.50 | 6.1 s |
| 2 | 0.35 | 0.03 | 7.81 | 0.03 | 6.94 | 15.17 | 29.2 s |
| 3 | 0.32 | 0.00 | 4.76 | 0.05 | 8.31 | 13.45 | 34.1 s |
| **Media de los turnos con LLM (3)** | 0.34 | 0.01 | 4.79 | 0.04 | 5.54 | 10.71 | |

