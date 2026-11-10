# 22_agotado_otro_candidato — Producto agotado que no es el primero

- Veredicto: **correcto**
- Entrada: texto
- Tipo: `agotado_otro_candidato`
- Qué se prueba: Escenario de reserva, escrito antes de corregir el agente y sin ejecutarlo. Tras la búsqueda se agota el tercer candidato y el cuarto queda con 10 unidades a 9,00 €. El usuario pide dos del tercero: el agente no puede añadirlo, no debe añadir otro por su cuenta y debe ofrecer uno con existencias. Después el usuario pide dos del cuarto y compra.

## Turno 1 (7.6 s)

**Usuario (texto):** Quiero unos calcetines de deporte.

- `buscar_productos(consulta="calcetines deporte")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B08G8D9267 | TANSTC Calcetines Altos Hombres Mujeres Calcetines De Algodón De Deporte Ciclismo Futbol Running Invierno Verano Antiampollas Senderismo Trekking Skate Calcetines Largos Multipack 6 Pares | marca: TANSTC | color: Negro y…

**Agente:** Tengo estos calcetines de deporte: los de TANSTC por 93,79 euros, los de RUNNING - CRONOS ONE por 10,28 euros, los de coskefy por 25,75 euros, los de DEPORTE – CRONOS ONE por 19,39 euros y los de Cerdá por 36,32 euros. ¿Te interesa alguno?

**Enviado al TTS:** Tengo estos calcetines de deporte: los de TANSTC por noventa y tres euros con setenta y nueve céntimos, los de RUNNING, CRONOS ONE por diez euros con veintiocho céntimos, los de coskefy por veinticinco euros con setenta y cinco céntimos, los de DEPORTE, CRONOS ONE por diecinueve euros con treinta y nueve céntimos y los de Cerdá por treinta y seis euros con treinta y dos céntimos. ¿Te interesa alguno?

- ✔ `cart(empty=true)` — carrito: vacío

> `@agotado` = `B07WL8FQ45` (candidate:3): coskefy Calcetines Cortos para Hombre y Mujer 6 Pares Calcetines Deportivos Algodon Transpirable Low Cut Calcetin Deporte Running Ciclismo Antideslizantes, Gris Oscuro(39-42)

> `@cuarto` = `B07NWRML8S` (candidate:4): Calcetines deportivos (3 pares) SIN COSTURAS de alto rendimiento para hombre o mujer. Ideales para deportes como running, crossfit, ciclismo, pádel, trekking; Cómodos y resistentes. (Am/Az/Na, 39-42)

> **Suceso externo:** la tienda deja `B07WL8FQ45` (@agotado) con existencias 0.

> **Suceso externo:** la tienda deja `B07NWRML8S` (@cuarto) con precio 9,00 € y existencias 10.

## Turno 2 (5.3 s)

**Usuario (texto):** Quiero dos del tercero.

- `agregar_al_carrito(product_id="B07WL8FQ45", cantidad=2)` → RECHAZADO: [agotado] El producto B07WL8FQ45 está agotado.

**Agente:** Ese producto está agotado. ¿Te interesa alguno de los demás? Como alternativa tengo: «TANSTC Calcetines Altos Hombres Mujeres Calcetines De Algodón De…» a 93,79 €, con 12 en existencias; «Calcetines (3 Pares) de RUNNING, CICLISMO, TENIS, PADEL,… Calcetines…» a 10,28 €, con 50 en existencias.

**Enviado al TTS:** Ese producto está agotado. ¿Te interesa alguno de los demás? Como alternativa tengo: TANSTC Calcetines Altos Hombres Mujeres Calcetines a noventa y tres euros con setenta y nueve céntimos, con doce en existencias, Calcetines a diez euros con veintiocho céntimos, con cincuenta en existencias.

- ✔ `cart(empty=true)` — carrito: vacío
- ✔ `offered_alternative(instead_of="@agotado")` — alternativas con existencias citadas: ['B08G8D9267', 'B07HJ33XGV']
- ✔ `orders(count=0)` — pedidos registrados: 0

> `@elegido` = `B07NWRML8S` (candidate:4): Calcetines deportivos (3 pares) SIN COSTURAS de alto rendimiento para hombre o mujer. Ideales para deportes como running, crossfit, ciclismo, pádel, trekking; Cómodos y resistentes. (Am/Az/Na, 39-42)

## Turno 3 (5.4 s)

**Usuario (texto):** Vale, pues dos del cuarto.

- `agregar_al_carrito(product_id="B07NWRML8S", cantidad=2)` → OK: hecho. Así queda el carrito. CARRITO: - id=B07NWRML8S | Calcetines deportivos (3 pares) SIN COSTURAS de alto rendimiento para… | 2 unidades × 9,00 € = 18,00 € | existencias: 10 Total del carrito: 18,00 €

**Agente:** Hecho, añadidas dos unidades. Ahora el carrito tiene 18,00 €. En el carrito hay 2 unidades de «Calcetines deportivos (3 pares) SIN COSTURAS de alto rendimiento para…» a 9,00 € cada una, 18,00 €. Total: 18,00 €.

**Enviado al TTS:** Hecho, añadidas dos unidades. Ahora el carrito tiene dieciocho euros. En el carrito hay dos unidades de Calcetines deportivos a nueve euros cada una, dieciocho euros. Total: dieciocho euros.

- ✔ `cart(lines=[{"product": "@elegido", "quantity": 2}])` — carrito: 2 × B07NWRML8S

## Turno 4 (2.3 s)

**Usuario (texto):** Ya está, finaliza la compra.

- `cotizar()` → OK: cotización creada; falta la confirmación del usuario.

**Agente:** Te repito el pedido antes de registrarlo: 2 unidades de «Calcetines deportivos (3 pares) SIN COSTURAS de alto rendimiento para…» a 9,00 € cada una, 18,00 €. Total: 18,00 €. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar. *(esperando confirmación)*

**Enviado al TTS:** Te repito el pedido antes de registrarlo: dos unidades de Calcetines deportivos a nueve euros cada una, dieciocho euros. Total: dieciocho euros. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar.

- ✔ `awaiting_confirmation(value=true)` — esperando confirmación: sí
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 5 (0.0 s)

**Usuario (texto):** Sí, confirmo.

- `confirmar_pedido(quote_id="e81977eb854b4ebd88471ac074f81641")` → OK: pedido registrado

**Agente:** Pedido número 1 registrado: 2 unidades de «Calcetines deportivos (3 pares) SIN COSTURAS de alto rendimiento para…» a 9,00 € cada una, 18,00 €. Total: 18,00 €. Gracias por tu compra.

**Enviado al TTS:** Pedido número uno registrado: dos unidades de Calcetines deportivos a nueve euros cada una, dieciocho euros. Total: dieciocho euros. Gracias por tu compra.

- ✔ `orders(count=1)` — pedidos registrados: 1

## Comprobaciones finales

- ✔ `orders(count=1)` — pedidos registrados: 1
- ✔ `order(lines=[{"not": "@agotado", "quantity": 2}])` — pedido 1: 2 × B07NWRML8S; total 1800 céntimos
- ✔ `stock(product="@agotado", equals=0)` — existencias de B07WL8FQ45: 0
- ✔ `cart(empty=true)` — carrito: vacío

## Violaciones de restricciones

- Ninguna.

## Estado final de la tienda

- Pedido 1: total 18,00 €
  - pedido 1: 2 × `B07NWRML8S` a 9,00 €
- Inventario `B07NWRML8S`: 47 → 8
- Inventario `B07WL8FQ45`: 2 → 0
- Líneas de carrito pendientes: 0

## Latencia por turno (segundos)

| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total | Audio de respuesta |
|---|---|---|---|---|---|---|---|
| 1 | 0.00 | 0.03 | 7.59 | 0.03 | 0.00 | 7.64 | 0.0 s |
| 2 | 0.00 | 0.00 | 5.27 | 0.02 | 0.00 | 5.29 | 0.0 s |
| 3 | 0.00 | 0.00 | 5.39 | 0.05 | 0.00 | 5.44 | 0.0 s |
| 4 | 0.00 | 0.00 | 2.22 | 0.04 | 0.00 | 2.25 | 0.0 s |
| 5 | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 | 0.03 | 0.0 s |
| **Media de los turnos con LLM (4)** | 0.00 | 0.01 | 5.12 | 0.03 | 0.00 | 5.16 | |
| **Media de los turnos sin LLM (1)** | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 | 0.03 | |

