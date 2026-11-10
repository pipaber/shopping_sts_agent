# 04_sin_existencias — Producto sin existencias que requiere alternativa

- Veredicto: **correcto**
- Entrada: texto
- Tipo: `sin_existencias`
- Qué se prueba: Tras la búsqueda, el primer candidato se agota (la tienda lo deja en 0) y el segundo queda con 10 unidades. El usuario pide el primero: el agente no puede añadirlo y debe ofrecer otro con existencias. El usuario compra entonces el segundo de la lista que tenga delante.

## Turno 1 (7.1 s)

**Usuario (texto):** Necesito una esterilla de yoga.

- `buscar_productos(consulta="esterilla yoga")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B083DM54G6 | Glymnis Esterilla Yoga Antideslizante Colchoneta Yoga Mat Esterilla Deporte de Material Ecológico TPE Esterilla Pilates con Correa 183mm x 61mm x 6mm Negro | marca: Glymnis | color: Negro | precio: 19,74 € | existencias:…

**Agente:** Tengo la esterilla de yoga Glymnis por 19,74 €, la de TENQUAN por 26,22 €, la de Rayline por 16,75 €, la de Hatonky por 12,42 € y la de NAFFIC por 16,46 €. ¿Te interesa alguna?

**Enviado al TTS:** Tengo la esterilla de yoga Glymnis por diecinueve euros con setenta y cuatro céntimos, la de TENQUAN por veintiséis euros con veintidós céntimos, la de Rayline por dieciséis euros con setenta y cinco céntimos, la de Hatonky por doce euros con cuarenta y dos céntimos y la de NAFFIC por dieciséis euros con cuarenta y seis céntimos. ¿Te interesa alguna?

- ✔ `cart(empty=true)` — carrito: vacío

> `@agotada` = `B083DM54G6` (candidate:1): Glymnis Esterilla Yoga Antideslizante Colchoneta Yoga Mat Esterilla Deporte de Material Ecológico TPE Esterilla Pilates con Correa 183mm x 61mm x 6mm Negro

> `@alternativa` = `B08GPGJY8M` (candidate:2): TENQUAN Esterilla Yoga Antideslizante – 8mm Esterilla Yoga con Correa para Yoga Pilates y Ejercicios de Piso

> **Suceso externo:** la tienda deja `B083DM54G6` (@agotada) con existencias 0.

> **Suceso externo:** la tienda deja `B08GPGJY8M` (@alternativa) con precio 18,00 € y existencias 10.

## Turno 2 (6.4 s)

**Usuario (texto):** Ponme una de la primera.

- `agregar_al_carrito(product_id="B083DM54G6", cantidad=1)` → RECHAZADO: [agotado] El producto B083DM54G6 está agotado.

**Agente:** Lo siento, el producto que has elegido está agotado. ¿Te interesa la esterilla de yoga de TENQUAN por 18,00 €?

**Enviado al TTS:** Lo siento, el producto que has elegido está agotado. ¿Te interesa la esterilla de yoga de TENQUAN por dieciocho euros?

- ✔ `cart(empty=true)` — carrito: vacío
- ✔ `offered_alternative(instead_of="@agotada")` — alternativas con existencias citadas: ['B08GPGJY8M']
- ✔ `orders(count=0)` — pedidos registrados: 0

> `@segunda` = `B08GPGJY8M` (candidate:2): TENQUAN Esterilla Yoga Antideslizante – 8mm Esterilla Yoga con Correa para Yoga Pilates y Ejercicios de Piso

## Turno 3 (5.7 s)

**Usuario (texto):** Entonces ponme una de la segunda.

- `agregar_al_carrito(product_id="B08GPGJY8M", cantidad=1)` → OK: hecho. Así queda el carrito. CARRITO: - id=B08GPGJY8M | TENQUAN Esterilla Yoga Antideslizante – 8mm Esterilla Yoga con Correa… | 1 unidad × 18,00 € = 18,00 € | existencias: 10 Total del carrito: 18,00 €

**Agente:** Hecho, añadida una esterilla de yoga de TENQUAN al carrito. En el carrito hay 1 unidad de «TENQUAN Esterilla Yoga Antideslizante – 8mm Esterilla Yoga con Correa…» a 18,00 € cada una, 18,00 €. Total: 18,00 €.

**Enviado al TTS:** Hecho, añadida una esterilla de yoga de TENQUAN al carrito. En el carrito hay una unidad de TENQUAN Esterilla Yoga Antideslizante a dieciocho euros cada una, dieciocho euros. Total: dieciocho euros.

- ✔ `cart(lines=[{"product": "@segunda", "quantity": 1}])` — carrito: 1 × B08GPGJY8M

## Turno 4 (2.3 s)

**Usuario (texto):** Cierra el pedido.

- `cotizar()` → OK: cotización creada; falta la confirmación del usuario.

**Agente:** Te repito el pedido antes de registrarlo: 1 unidad de «TENQUAN Esterilla Yoga Antideslizante – 8mm Esterilla Yoga con Correa…» a 18,00 € cada una, 18,00 €. Total: 18,00 €. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar. *(esperando confirmación)*

**Enviado al TTS:** Te repito el pedido antes de registrarlo: una unidad de TENQUAN Esterilla Yoga Antideslizante a dieciocho euros cada una, dieciocho euros. Total: dieciocho euros. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar.

- ✔ `awaiting_confirmation(value=true)` — esperando confirmación: sí
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 5 (0.0 s)

**Usuario (texto):** Sí, confirmo.

- `confirmar_pedido(quote_id="c1f8b8ddebd241c18a55083e436d095f")` → OK: pedido registrado

**Agente:** Pedido número 1 registrado: 1 unidad de «TENQUAN Esterilla Yoga Antideslizante – 8mm Esterilla Yoga con Correa…» a 18,00 € cada una, 18,00 €. Total: 18,00 €. Gracias por tu compra.

**Enviado al TTS:** Pedido número uno registrado: una unidad de TENQUAN Esterilla Yoga Antideslizante a dieciocho euros cada una, dieciocho euros. Total: dieciocho euros. Gracias por tu compra.

- ✔ `orders(count=1)` — pedidos registrados: 1

## Comprobaciones finales

- ✔ `orders(count=1)` — pedidos registrados: 1
- ✔ `order(lines=[{"not": "@agotada", "quantity": 1}])` — pedido 1: 1 × B08GPGJY8M; total 1800 céntimos
- ✔ `stock(product="@agotada", equals=0)` — existencias de B083DM54G6: 0
- ✔ `cart(empty=true)` — carrito: vacío

## Violaciones de restricciones

- Ninguna.

## Estado final de la tienda

- Pedido 1: total 18,00 €
  - pedido 1: 1 × `B08GPGJY8M` a 18,00 €
- Inventario `B083DM54G6`: 37 → 0
- Inventario `B08GPGJY8M`: 4 → 9
- Líneas de carrito pendientes: 0

## Latencia por turno (segundos)

| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total | Audio de respuesta |
|---|---|---|---|---|---|---|---|
| 1 | 0.00 | 0.03 | 7.07 | 0.02 | 0.00 | 7.11 | 0.0 s |
| 2 | 0.00 | 0.00 | 6.35 | 0.03 | 0.00 | 6.38 | 0.0 s |
| 3 | 0.00 | 0.00 | 5.64 | 0.05 | 0.00 | 5.69 | 0.0 s |
| 4 | 0.00 | 0.00 | 2.29 | 0.04 | 0.00 | 2.33 | 0.0 s |
| 5 | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 | 0.03 | 0.0 s |
| **Media de los turnos con LLM (4)** | 0.00 | 0.01 | 5.34 | 0.04 | 0.00 | 5.38 | |
| **Media de los turnos sin LLM (1)** | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 | 0.03 | |

