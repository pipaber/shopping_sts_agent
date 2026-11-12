# 04_sin_existencias — Producto sin existencias que requiere alternativa

- Veredicto: **correcto**
- Entrada: audio (grabaciones del usuario)
- Tipo: `sin_existencias`
- Qué se prueba: Tras la búsqueda, el primer candidato se agota (la tienda lo deja en 0) y el segundo queda con 10 unidades. El usuario pide el primero: el agente no puede añadirlo y debe ofrecer otro con existencias. El usuario compra entonces el segundo de la lista que tenga delante.

## Turno 1 (13.5 s)

**Usuario (transcripción del ASR):** Necesito una esterilla de yoga.

- `buscar_productos(consulta="esterilla yoga")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B08GPGJY8M | TENQUAN Esterilla Yoga Antideslizante – 8mm Esterilla Yoga con Correa para Yoga Pilates y Ejercicios de Piso | marca: TENQUAN | color: Dark Blue | precio: 26,22 € | existencias: 4 | características (extracto): Espesor óp…

**Agente:** Tengo la esterilla de yoga de TENQUAN por 26,22 €, la de LynnsGraceland por 20 €, la de Rayline por 16,75 €, la de Glymnis por 19,74 € y la de Hatonky por 12,42 €. ¿Te interesa alguna?

**Enviado al TTS:** Tengo la esterilla de yoga de TENQUAN por veintiséis euros con veintidós céntimos, la de LynnsGraceland por veinte euros, la de Rayline por dieciséis euros con setenta y cinco céntimos, la de Glymnis por diecinueve euros con setenta y cuatro céntimos y la de Hatonky por doce euros con cuarenta y dos céntimos. ¿Te interesa alguna?

- ✔ `cart(empty=true)` — carrito: vacío

> `@agotada` = `B08GPGJY8M` (candidate:1): TENQUAN Esterilla Yoga Antideslizante – 8mm Esterilla Yoga con Correa para Yoga Pilates y Ejercicios de Piso

> `@alternativa` = `B09738BXB2` (candidate:2): Esterilla Yoga,Ya no es quien vive, sino a Cristo que vive en mí. ,Esterilla Deporte Antideslizante Ecológica y 100% Natural de,No tóxico,para Pilates,Fitness

> **Suceso externo:** la tienda deja `B08GPGJY8M` (@agotada) con existencias 0.

> **Suceso externo:** la tienda deja `B09738BXB2` (@alternativa) con precio 18,00 € y existencias 10.

## Turno 2 (10.3 s)

**Usuario (transcripción del ASR):** Ponme una de la primera.

- `agregar_al_carrito(product_id="B08GPGJY8M", cantidad=1)` → RECHAZADO: [agotado] El producto B08GPGJY8M está agotado.

**Agente:** Ese producto se ha agotado. ¿Te interesa alguna de las demás opciones? Como alternativa tengo: «Esterilla Yoga,Ya no es quien vive, sino a Cristo que vive en mí…» a 18,00 €, con 10 en existencias; «Rayline - Esterilla de yoga, esterilla de deporte, correa de…» a 16,75 €, con 40 en existencias.

**Enviado al TTS:** Ese producto se ha agotado. ¿Te interesa alguna de las demás opciones? Como alternativa tengo: Esterilla Yoga a dieciocho euros, con diez en existencias, Rayline a dieciséis euros con setenta y cinco céntimos, con cuarenta en existencias.

- ✔ `cart(empty=true)` — carrito: vacío
- ✔ `offered_alternative(instead_of="@agotada")` — alternativas con existencias citadas: ['B09738BXB2', 'B08DNYZKHM']
- ✔ `orders(count=0)` — pedidos registrados: 0

> `@segunda` = `B09738BXB2` (candidate:2): Esterilla Yoga,Ya no es quien vive, sino a Cristo que vive en mí. ,Esterilla Deporte Antideslizante Ecológica y 100% Natural de,No tóxico,para Pilates,Fitness

## Turno 3 (8.8 s)

**Usuario (transcripción del ASR):** Entonces ponme una de la segunda.

- `agregar_al_carrito(product_id="B09738BXB2", cantidad=1)` → OK: hecho. Así queda el carrito. CARRITO: - id=B09738BXB2 | Esterilla Yoga,Ya no es quien vive, sino a Cristo que vive en mí… | 1 unidad × 18,00 € = 18,00 € | existencias: 10 Total del carrito: 18,00 €

**Agente:** Hecho, añadida una unidad al carrito. En el carrito hay 1 unidad de «Esterilla Yoga,Ya no es quien vive, sino a Cristo que vive en mí…» a 18,00 € cada una, 18,00 €. Total: 18,00 €.

**Enviado al TTS:** Hecho, añadida una unidad al carrito. En el carrito hay una unidad de Esterilla Yoga a dieciocho euros cada una, dieciocho euros. Total: dieciocho euros.

- ✔ `cart(lines=[{"product": "@segunda", "quantity": 1}])` — carrito: 1 × B09738BXB2

## Turno 4 (7.1 s)

**Usuario (transcripción del ASR):** Cierra el pedido.

- `cotizar()` → OK: cotización creada; falta la confirmación del usuario.

**Agente:** Te repito el pedido antes de registrarlo: 1 unidad de «Esterilla Yoga,Ya no es quien vive, sino a Cristo que vive en mí…» a 18,00 € cada una, 18,00 €. Total: 18,00 €. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar. *(esperando confirmación)*

**Enviado al TTS:** Te repito el pedido antes de registrarlo: una unidad de Esterilla Yoga a dieciocho euros cada una, dieciocho euros. Total: dieciocho euros. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar.

- ✔ `awaiting_confirmation(value=true)` — esperando confirmación: sí
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 5 (4.5 s)

**Usuario (transcripción del ASR):** Sí, confirmo.

- `confirmar_pedido(quote_id="ea987c1e325d4becbc12b36d25c826be")` → OK: pedido registrado

**Agente:** Pedido número 1 registrado: 1 unidad de «Esterilla Yoga,Ya no es quien vive, sino a Cristo que vive en mí…» a 18,00 € cada una, 18,00 €. Total: 18,00 €. Gracias por tu compra.

**Enviado al TTS:** Pedido número uno registrado: una unidad de Esterilla Yoga a dieciocho euros cada una, dieciocho euros. Total: dieciocho euros. Gracias por tu compra.

- ✔ `orders(count=1)` — pedidos registrados: 1

## Comprobaciones finales

- ✔ `orders(count=1)` — pedidos registrados: 1
- ✔ `order(lines=[{"not": "@agotada", "quantity": 1}])` — pedido 1: 1 × B09738BXB2; total 1800 céntimos
- ✔ `stock(product="@agotada", equals=0)` — existencias de B08GPGJY8M: 0
- ✔ `cart(empty=true)` — carrito: vacío

## Violaciones de restricciones

- Ninguna.

## Estado final de la tienda

- Pedido 1: total 18,00 €
  - pedido 1: 1 × `B09738BXB2` a 18,00 €
- Inventario `B08GPGJY8M`: 4 → 0
- Inventario `B09738BXB2`: 50 → 9
- Líneas de carrito pendientes: 0

## Latencia por turno (segundos)

| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total | Audio de respuesta |
|---|---|---|---|---|---|---|---|
| 1 | 0.34 | 0.03 | 7.07 | 0.03 | 6.07 | 13.54 | 22.7 s |
| 2 | 0.33 | 0.00 | 5.45 | 0.03 | 4.45 | 10.27 | 16.6 s |
| 3 | 0.34 | 0.00 | 4.95 | 0.04 | 3.48 | 8.81 | 12.6 s |
| 4 | 0.33 | 0.00 | 2.32 | 0.04 | 4.40 | 7.09 | 16.4 s |
| 5 | 0.33 | 0.00 | 0.00 | 0.04 | 4.11 | 4.48 | 14.7 s |
| **Media de los turnos con LLM (4)** | 0.34 | 0.01 | 4.95 | 0.04 | 4.60 | 9.93 | |
| **Media de los turnos sin LLM (1)** | 0.33 | 0.00 | 0.00 | 0.04 | 4.11 | 4.48 | |

