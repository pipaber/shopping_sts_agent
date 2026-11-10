# 22_agotado_otro_candidato — Producto agotado que no es el primero

- Veredicto: **correcto**
- Entrada: texto
- Tipo: `agotado_otro_candidato`
- Qué se prueba: Escenario de reserva, escrito antes de corregir el agente y sin ejecutarlo. Tras la búsqueda se agota el tercer candidato y el cuarto queda con 10 unidades a 9,00 €. El usuario pide dos del tercero: el agente no puede añadirlo, no debe añadir otro por su cuenta y debe ofrecer uno con existencias. Después el usuario pide dos del cuarto y compra.

## Turno 1 (6.0 s)

**Usuario (texto):** Quiero unos calcetines de deporte.

- `buscar_productos(consulta="calcetines deporte")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B07WL8FQ45 | coskefy Calcetines Cortos para Hombre y Mujer 6 Pares Calcetines Deportivos Algodon Transpirable Low Cut Calcetin Deporte Running Ciclismo Antideslizantes, Gris Oscuro(39-42) | marca: coskefy | color: Gris Oscuro-04 | pr…

**Agente:** Tengo los calcetines de coskefy por 25,75 euros, los de Cerdá por 36,32 y los de RUNNING - CRONOS ONE por 10,28. ¿Te interesa alguno?

**Enviado al TTS:** Tengo los calcetines de coskefy por veinticinco euros con setenta y cinco céntimos, los de Cerdá por treinta y seis coma treinta y dos y los de RUNNING, CRONOS ONE por diez coma veintiocho. ¿Te interesa alguno?

- ✔ `cart(empty=true)` — carrito: vacío

> `@agotado` = `B07HJ33XGV` (candidate:3): Calcetines (3 Pares) de RUNNING, CICLISMO, TENIS, PADEL,… Calcetines SIN COSTURAS unisex con puntera y talón reforzados. Calcetines tobilleros de deporte. Anti-rozaduras y con gomas anti-presión.

> `@cuarto` = `B08G8D9267` (candidate:4): TANSTC Calcetines Altos Hombres Mujeres Calcetines De Algodón De Deporte Ciclismo Futbol Running Invierno Verano Antiampollas Senderismo Trekking Skate Calcetines Largos Multipack 6 Pares

> **Suceso externo:** la tienda deja `B07HJ33XGV` (@agotado) con existencias 0.

> **Suceso externo:** la tienda deja `B08G8D9267` (@cuarto) con precio 9,00 € y existencias 10.

## Turno 2 (5.5 s)

**Usuario (texto):** Quiero dos del tercero.

- `agregar_al_carrito(product_id="B07HJ33XGV", cantidad=2)` → RECHAZADO: [agotado] El producto B07HJ33XGV está agotado.

**Agente:** Ese producto se ha agotado. ¿Te interesa alguno de los otros? Como alternativa tengo: «coskefy Calcetines Cortos para Hombre y Mujer 6 Pares Calcetines…» a 25,75 €, con 2 en existencias; «Cerdá Calcetines modelo CALCETINES ADULTO THE MANDALORIAN marca» a 36,32 €, con 3 en existencias.

**Enviado al TTS:** Ese producto se ha agotado. ¿Te interesa alguno de los otros? Como alternativa tengo: coskefy Calcetines Cortos para Hombre y Mujer a veinticinco euros con setenta y cinco céntimos, con dos en existencias, Cerdá Calcetines modelo CALCETINES ADULTO THE MANDALORIAN a treinta y seis euros con treinta y dos céntimos, con tres en existencias.

- ✔ `cart(empty=true)` — carrito: vacío
- ✔ `offered_alternative(instead_of="@agotado")` — alternativas con existencias citadas: ['B07WL8FQ45', 'B07D2BWWC1']
- ✔ `orders(count=0)` — pedidos registrados: 0

> `@elegido` = `B08G8D9267` (candidate:4): TANSTC Calcetines Altos Hombres Mujeres Calcetines De Algodón De Deporte Ciclismo Futbol Running Invierno Verano Antiampollas Senderismo Trekking Skate Calcetines Largos Multipack 6 Pares

## Turno 3 (5.6 s)

**Usuario (texto):** Vale, pues dos del cuarto.

- `agregar_al_carrito(product_id="B08G8D9267", cantidad=2)` → OK: hecho. Así queda el carrito. CARRITO: - id=B08G8D9267 | TANSTC Calcetines Altos Hombres Mujeres Calcetines De Algodón De… | 2 unidades × 9,00 € = 18,00 € | existencias: 10 Total del carrito: 18,00 €

**Agente:** Hecho, añadidas dos unidades. Ahora el carrito tiene 18,00 €. En el carrito hay 2 unidades de «TANSTC Calcetines Altos Hombres Mujeres Calcetines De Algodón De…» a 9,00 € cada una, 18,00 €. Total: 18,00 €.

**Enviado al TTS:** Hecho, añadidas dos unidades. Ahora el carrito tiene dieciocho euros. En el carrito hay dos unidades de TANSTC Calcetines Altos Hombres Mujeres Calcetines a nueve euros cada una, dieciocho euros. Total: dieciocho euros.

- ✔ `cart(lines=[{"product": "@elegido", "quantity": 2}])` — carrito: 2 × B08G8D9267

## Turno 4 (2.3 s)

**Usuario (texto):** Ya está, finaliza la compra.

- `cotizar()` → OK: cotización creada; falta la confirmación del usuario.

**Agente:** Te repito el pedido antes de registrarlo: 2 unidades de «TANSTC Calcetines Altos Hombres Mujeres Calcetines De Algodón De…» a 9,00 € cada una, 18,00 €. Total: 18,00 €. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar. *(esperando confirmación)*

**Enviado al TTS:** Te repito el pedido antes de registrarlo: dos unidades de TANSTC Calcetines Altos Hombres Mujeres Calcetines a nueve euros cada una, dieciocho euros. Total: dieciocho euros. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar.

- ✔ `awaiting_confirmation(value=true)` — esperando confirmación: sí
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 5 (0.0 s)

**Usuario (texto):** Sí, confirmo.

- `confirmar_pedido(quote_id="9ec5a542e3334c87991438da8ad0444d")` → OK: pedido registrado

**Agente:** Pedido número 1 registrado: 2 unidades de «TANSTC Calcetines Altos Hombres Mujeres Calcetines De Algodón De…» a 9,00 € cada una, 18,00 €. Total: 18,00 €. Gracias por tu compra.

**Enviado al TTS:** Pedido número uno registrado: dos unidades de TANSTC Calcetines Altos Hombres Mujeres Calcetines a nueve euros cada una, dieciocho euros. Total: dieciocho euros. Gracias por tu compra.

- ✔ `orders(count=1)` — pedidos registrados: 1

## Comprobaciones finales

- ✔ `orders(count=1)` — pedidos registrados: 1
- ✔ `order(lines=[{"not": "@agotado", "quantity": 2}])` — pedido 1: 2 × B08G8D9267; total 1800 céntimos
- ✔ `stock(product="@agotado", equals=0)` — existencias de B07HJ33XGV: 0
- ✔ `cart(empty=true)` — carrito: vacío

## Violaciones de restricciones

- Ninguna.

## Estado final de la tienda

- Pedido 1: total 18,00 €
  - pedido 1: 2 × `B08G8D9267` a 9,00 €
- Inventario `B07HJ33XGV`: 50 → 0
- Inventario `B08G8D9267`: 12 → 8
- Líneas de carrito pendientes: 0

## Latencia por turno (segundos)

| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total | Audio de respuesta |
|---|---|---|---|---|---|---|---|
| 1 | 0.00 | 0.03 | 5.92 | 0.03 | 0.00 | 5.97 | 0.0 s |
| 2 | 0.00 | 0.00 | 5.42 | 0.03 | 0.00 | 5.46 | 0.0 s |
| 3 | 0.00 | 0.00 | 5.52 | 0.06 | 0.00 | 5.58 | 0.0 s |
| 4 | 0.00 | 0.00 | 2.25 | 0.03 | 0.00 | 2.27 | 0.0 s |
| 5 | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 | 0.03 | 0.0 s |
| **Media de los turnos con LLM (4)** | 0.00 | 0.01 | 4.78 | 0.04 | 0.00 | 4.82 | |
| **Media de los turnos sin LLM (1)** | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 | 0.03 | |

