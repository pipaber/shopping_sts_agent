# 02_pedido_ambiguo — Pedido ambiguo que requiere aclaración

- Veredicto: **correcto**
- Entrada: texto
- Tipo: `pedido_ambiguo`
- Qué se prueba: El primer mensaje no dice qué producto se busca: el agente debe preguntar en lugar de suponer. Después el usuario concreta el producto y el presupuesto, y añade una unidad.

## Turno 1 (1.9 s)

**Usuario (texto):** Quiero comprar un regalo para mi hermana.

- `pedir_aclaracion(pregunta="¿Qué tipo de regalo tienes en mente para tu hermana?")` → OK: pregunta enviada al usuario

**Agente:** ¿Qué tipo de regalo tienes en mente para tu hermana?

**Enviado al TTS:** ¿Qué tipo de regalo tienes en mente para tu hermana?

- ✔ `asked_clarification()` — pidió aclaración
- ✔ `cart(empty=true)` — carrito: vacío
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 2 (8.5 s)

**Usuario (texto):** Unos auriculares bluetooth, y no quiero gastar más de 50 euros.

- `fijar_presupuesto(importe_eur=50)` → OK: presupuesto fijado en 50,00 €.
- `buscar_productos(consulta="auriculares bluetooth")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B07TXSV5X6 | Auriculares Bluetooth,Auriculares Inalámbricos Bluetooth táctiles, Auriculares estéreo Bluetooth IPX7 a Prueba de Agua, con Estuche de Carga para Apple Airpods Android iPhone | marca: WDGP | color: desconocido | precio: …

**Agente:** Tengo auriculares Bluetooth de WDGP por 32,06 euros, de Mgrett en Rosa1 por 9,18 euros, de DZTA en White1 por 14,19 euros, de Leynatic con Q13S1 por 7,71 euros y de OVIFM por 4,61 euros. ¿Te interesa alguno? He anotado un presupuesto de 50,00 €.

**Enviado al TTS:** Tengo auriculares Bluetooth de WDGP por treinta y dos euros con seis céntimos, de Mgrett en Rosa1 por nueve euros con dieciocho céntimos, de DZTA en White1 por catorce euros con diecinueve céntimos, de Leynatic con por siete euros con setenta y un céntimos y de OVIFM por cuatro euros con sesenta y un céntimos. ¿Te interesa alguno? He anotado un presupuesto de cincuenta euros.

- ✔ `budget(cents=5000)` — presupuesto en el estado: 5000
- ✔ `cart(empty=true)` — carrito: vacío

> `@elegido` = `B07TXSV5X6` (candidate:1): Auriculares Bluetooth,Auriculares Inalámbricos Bluetooth táctiles, Auriculares estéreo Bluetooth IPX7 a Prueba de Agua, con Estuche de Carga para Apple Airpods Android iPhone

> **Suceso externo:** la tienda deja `B07TXSV5X6` (@elegido) con precio 19,90 € y existencias 20.

## Turno 3 (5.0 s)

**Usuario (texto):** Ponme uno del primero.

- `agregar_al_carrito(product_id="B07TXSV5X6", cantidad=1)` → OK: hecho. Así queda el carrito. CARRITO: - id=B07TXSV5X6 | Auriculares Bluetooth,Auriculares Inalámbricos Bluetooth táctiles… | 1 unidad × 19,90 € = 19,90 € | existencias: 20 Total del carrito: 19,90 €

**Agente:** Hecho, añadido uno de los auriculares Bluetooth WDGP al carrito. En el carrito hay 1 unidad de «Auriculares Bluetooth,Auriculares Inalámbricos Bluetooth táctiles…» a 19,90 € cada una, 19,90 €. Total: 19,90 €. Tu presupuesto es de 50,00 € y te quedan 30,10 €.

**Enviado al TTS:** Hecho, añadido uno de los auriculares Bluetooth WDGP al carrito. En el carrito hay una unidad de Auriculares Bluetooth a diecinueve euros con noventa céntimos cada una, diecinueve euros con noventa céntimos. Total: diecinueve euros con noventa céntimos. Tu presupuesto es de cincuenta euros y te quedan treinta euros con diez céntimos.

- ✔ `cart(lines=[{"product": "@elegido", "quantity": 1}])` — carrito: 1 × B07TXSV5X6

## Comprobaciones finales

- ✔ `orders(count=0)` — pedidos registrados: 0
- ✔ `cart(lines=[{"product": "@elegido", "quantity": 1}])` — carrito: 1 × B07TXSV5X6
- ✔ `budget(cents=5000)` — presupuesto en el estado: 5000
- ✔ `stock(product="@elegido", equals=20)` — existencias de B07TXSV5X6: 20

## Violaciones de restricciones

- Ninguna.

## Estado final de la tienda

- Inventario `B07TXSV5X6`: 29 → 20
- Líneas de carrito pendientes: 1

## Latencia por turno (segundos)

| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total | Audio de respuesta |
|---|---|---|---|---|---|---|---|
| 1 | 0.00 | 0.00 | 1.84 | 0.01 | 0.00 | 1.86 | 0.0 s |
| 2 | 0.00 | 0.03 | 8.49 | 0.03 | 0.00 | 8.55 | 0.0 s |
| 3 | 0.00 | 0.00 | 4.93 | 0.05 | 0.00 | 4.99 | 0.0 s |
| **Media de los turnos con LLM (3)** | 0.00 | 0.01 | 5.09 | 0.03 | 0.00 | 5.13 | |

