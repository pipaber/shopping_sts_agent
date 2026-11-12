# 19_presupuesto_compartido — Presupuesto compartido entre dos productos

- Veredicto: **correcto**
- Entrada: texto
- Tipo: `presupuesto_compartido`
- Qué se prueba: Con 50 € de presupuesto, dos unidades del primero (28,00 €) caben, pero otras dos del segundo (32,00 €) ya no: solo cabe una (16,00 €). El pedido final suma 44,00 €.

## Turno 1 (13.9 s)

**Usuario (texto):** Busco unas toallas de baño. Mi presupuesto es de 50 euros.

- `fijar_presupuesto(importe_eur=50)` → OK: presupuesto fijado en 50,00 €.
- `buscar_productos(consulta="toallas de baño")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B01M0TJMI7 | Amazon Basics - Juego de toallas (colores resistentes, 2 toallas de baño, 2 de manos y 2 para bidé), color blanco | marca: Amazon Basics | color: Blanco | precio: 11,93 € | existencias: 39 | características (extracto): I…

**Agente:** Tengo estas opciones para ti: las toallas de baño Amazon Basics por 11,93 €, las de Chantarole por 35,15 €, las de Utopia Towels por 48,03 € y las de Utopia Towels en gris por 9,24 €. ¿Te interesa alguna? He anotado un presupuesto de 50,00 €.

**Enviado al TTS:** Tengo estas opciones para ti: las toallas de baño Amazon Basics por once euros con noventa y tres céntimos, las de Chantarole por treinta y cinco euros con quince céntimos, las de Utopia Towels por cuarenta y ocho euros con tres céntimos y las de Utopia Towels en gris por nueve euros con veinticuatro céntimos. ¿Te interesa alguna? He anotado un presupuesto de cincuenta euros.

- ✔ `budget(cents=5000)` — presupuesto en el estado: 5000
- ✔ `cart(empty=true)` — carrito: vacío

> `@primeras` = `B01M0TJMI7` (candidate:1): Amazon Basics - Juego de toallas (colores resistentes, 2 toallas de baño, 2 de manos y 2 para bidé), color blanco

> `@segundas` = `B07P67N2J1` (candidate:2): Chantarole - Juego de Toallas baño Grandes: 1 Toalla de baño + 1 Toalla Manos + 1 Toalla Pelo + 1 Alfombra baño; Toallas Blancas Algodon; Toallas Hotel (Blanco, 4)

> **Suceso externo:** la tienda deja `B01M0TJMI7` (@primeras) con precio 14,00 € y existencias 20.

> **Suceso externo:** la tienda deja `B07P67N2J1` (@segundas) con precio 16,00 € y existencias 20.

## Turno 2 (7.0 s)

**Usuario (texto):** Añade dos de la primera opción.

- `agregar_al_carrito(product_id="B01M0TJMI7", cantidad=2)` → OK: hecho. Así queda el carrito. CARRITO: - id=B01M0TJMI7 | Amazon Basics - Juego de toallas (colores resistentes, 2 toallas de… | 2 unidades × 14,00 € = 28,00 € | existencias: 20 Total del carrito: 28,00 €

**Agente:** Hecho, añadidas dos unidades. En el carrito hay 2 unidades de «Amazon Basics - Juego de toallas (colores resistentes, 2 toallas de…» a 14,00 € cada una, 28,00 €. Total: 28,00 €. Tu presupuesto es de 50,00 € y te quedan 22,00 €.

**Enviado al TTS:** Hecho, añadidas dos unidades. En el carrito hay dos unidades de Amazon Basics a catorce euros cada una, veintiocho euros. Total: veintiocho euros. Tu presupuesto es de cincuenta euros y te quedan veintidós euros.

- ✔ `cart(lines=[{"product": "@primeras", "quantity": 2}])` — carrito: 2 × B01M0TJMI7

## Turno 3 (9.2 s)

**Usuario (texto):** Añade también dos de la segunda opción.

- `agregar_al_carrito(product_id="B07P67N2J1", cantidad=2)` → RECHAZADO: [presupuesto_excedido] El total sería 60,00 € y supera el presupuesto de 50,00 € por 10,00 €. Dentro del presupuesto caben como máximo 1 unidades de este producto.

**Agente:** Ese producto supera tu presupuesto. ¿Quieres añadirlo de todas formas o prefieres otro?

**Enviado al TTS:** Ese producto supera tu presupuesto. ¿Quieres añadirlo de todas formas o prefieres otro?

- ✔ `cart(lines=[{"product": "@primeras", "quantity": 2}])` — carrito: 2 × B01M0TJMI7

## Turno 4 (9.4 s)

**Usuario (texto):** Pues solo una de la segunda.

- `agregar_al_carrito(product_id="B07P67N2J1", cantidad=1)` → OK: hecho. Así queda el carrito. CARRITO: - id=B01M0TJMI7 | Amazon Basics - Juego de toallas (colores resistentes, 2 toallas de… | 2 unidades × 14,00 € = 28,00 € | existencias: 20 - id=B07P67N2J1 | Chantarole - Juego de Toallas baño Grandes: 1 Toalla de baño + 1… | 1 unidad × 16,00 € = 16,00 € | existen…

**Agente:** Hecho, añadida una unidad. En total, 44,00 €. En el carrito hay 2 unidades de «Amazon Basics - Juego de toallas (colores resistentes, 2 toallas de…» a 14,00 € cada una, 28,00 €; 1 unidad de «Chantarole - Juego de Toallas baño Grandes: 1 Toalla de baño + 1…» a 16,00 € cada una, 16,00 €. Total: 44,00 €. Tu presupuesto es de 50,00 € y te quedan 6,00 €.

**Enviado al TTS:** Hecho, añadida una unidad. En total, cuarenta y cuatro euros. En el carrito hay dos unidades de Amazon Basics a catorce euros cada una, veintiocho euros, una unidad de Chantarole a dieciséis euros cada una, dieciséis euros. Total: cuarenta y cuatro euros. Tu presupuesto es de cincuenta euros y te quedan seis euros.

- ✔ `cart(lines=[{"product": "@primeras", "quantity": 2}, {"product": "@segundas", "quantity": 1}])` — carrito: 2 × B01M0TJMI7, 1 × B07P67N2J1

## Turno 5 (3.5 s)

**Usuario (texto):** Cierra el pedido.

- `cotizar()` → OK: cotización creada; falta la confirmación del usuario.

**Agente:** Te repito el pedido antes de registrarlo: 2 unidades de «Amazon Basics - Juego de toallas (colores resistentes, 2 toallas de…» a 14,00 € cada una, 28,00 €; 1 unidad de «Chantarole - Juego de Toallas baño Grandes: 1 Toalla de baño + 1…» a 16,00 € cada una, 16,00 €. Total: 44,00 €. Tu presupuesto es de 50,00 € y te quedan 6,00 €. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar. *(esperando confirmación)*

**Enviado al TTS:** Te repito el pedido antes de registrarlo: dos unidades de Amazon Basics a catorce euros cada una, veintiocho euros, una unidad de Chantarole a dieciséis euros cada una, dieciséis euros. Total: cuarenta y cuatro euros. Tu presupuesto es de cincuenta euros y te quedan seis euros. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar.

- ✔ `awaiting_confirmation(value=true)` — esperando confirmación: sí
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 6 (0.0 s)

**Usuario (texto):** Sí.

- `confirmar_pedido(quote_id="ddb1302e74bc458a81f6c87022133c5d")` → OK: pedido registrado

**Agente:** Pedido número 1 registrado: 2 unidades de «Amazon Basics - Juego de toallas (colores resistentes, 2 toallas de…» a 14,00 € cada una, 28,00 €; 1 unidad de «Chantarole - Juego de Toallas baño Grandes: 1 Toalla de baño + 1…» a 16,00 € cada una, 16,00 €. Total: 44,00 €. Gracias por tu compra.

**Enviado al TTS:** Pedido número uno registrado: dos unidades de Amazon Basics a catorce euros cada una, veintiocho euros, una unidad de Chantarole a dieciséis euros cada una, dieciséis euros. Total: cuarenta y cuatro euros. Gracias por tu compra.

- ✔ `orders(count=1)` — pedidos registrados: 1

## Comprobaciones finales

- ✔ `orders(count=1)` — pedidos registrados: 1
- ✔ `order(lines=[{"product": "@primeras", "quantity": 2}, {"product": "@segundas", "quantity": 1}], total_cents=4400)` — pedido 1: 2 × B01M0TJMI7, 1 × B07P67N2J1; total 4400 céntimos
- ✔ `budget(cents=5000)` — presupuesto en el estado: 5000
- ✔ `cart(empty=true)` — carrito: vacío

## Violaciones de restricciones

- Ninguna.

## Estado final de la tienda

- Pedido 1: total 44,00 €
  - pedido 1: 2 × `B01M0TJMI7` a 14,00 €
  - pedido 1: 1 × `B07P67N2J1` a 16,00 €
- Inventario `B01M0TJMI7`: 39 → 18
- Inventario `B07P67N2J1`: 38 → 19
- Líneas de carrito pendientes: 0

## Latencia por turno (segundos)

| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total | Audio de respuesta |
|---|---|---|---|---|---|---|---|
| 1 | 0.00 | 0.06 | 13.83 | 0.03 | 0.00 | 13.92 | 0.0 s |
| 2 | 0.00 | 0.00 | 6.91 | 0.04 | 0.00 | 6.96 | 0.0 s |
| 3 | 0.00 | 0.00 | 9.19 | 0.03 | 0.00 | 9.22 | 0.0 s |
| 4 | 0.00 | 0.00 | 9.34 | 0.05 | 0.00 | 9.38 | 0.0 s |
| 5 | 0.00 | 0.00 | 3.43 | 0.03 | 0.00 | 3.46 | 0.0 s |
| 6 | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 | 0.03 | 0.0 s |
| **Media de los turnos con LLM (5)** | 0.00 | 0.01 | 8.54 | 0.04 | 0.00 | 8.59 | |
| **Media de los turnos sin LLM (1)** | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 | 0.03 | |

