# 03_cambio_cantidad — Cambio de cantidad manteniendo las demás restricciones

- Veredicto: **correcto**
- Entrada: texto
- Tipo: `cambio_cantidad`
- Qué se prueba: El usuario añade dos unidades y después corrige a cuatro. El producto y el presupuesto deben seguir siendo los mismos y el pedido final debe llevar cuatro unidades (38,00 € de un presupuesto de 45 €).

## Turno 1 (7.7 s)

**Usuario (texto):** Busco una botella de agua de acero inoxidable. Mi presupuesto es de 45 euros.

- `fijar_presupuesto(importe_eur=45)` → OK: presupuesto fijado en 45,00 €.
- `buscar_productos(consulta="botella de agua acero inoxidable")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B07VQNY8PK | Newdora Botella de Agua Acero Inoxidable 500ml, Aislamiento de Vacío de Doble Pared, Botellas de Frío/Caliente, con 1 un Cepillo de Limpieza, para Niños, Deporte, Oficina, Gimnasio, Ciclismo, Negro | marca: Newdora | col…

**Agente:** Tengo la botella de Newdora por 6,72 euros, la de KOUAJ por 18,29, la de BlenderBottle por 2,46 y la de KOSAD por 12,37. ¿Te interesa alguna? He anotado un presupuesto de 45,00 €.

**Enviado al TTS:** Tengo la botella de Newdora por seis euros con setenta y dos céntimos, la de KOUAJ por dieciocho coma veintinueve, la de BlenderBottle por dos coma cuarenta y seis y la de KOSAD por doce coma treinta y siete. ¿Te interesa alguna? He anotado un presupuesto de cuarenta y cinco euros.

- ✔ `budget(cents=4500)` — presupuesto en el estado: 4500

> `@elegida` = `B07VQNY8PK` (candidate:1): Newdora Botella de Agua Acero Inoxidable 500ml, Aislamiento de Vacío de Doble Pared, Botellas de Frío/Caliente, con 1 un Cepillo de Limpieza, para Niños, Deporte, Oficina, Gimnasio, Ciclismo, Negro

> **Suceso externo:** la tienda deja `B07VQNY8PK` (@elegida) con precio 9,50 € y existencias 20.

## Turno 2 (5.1 s)

**Usuario (texto):** Añade dos de la primera.

- `agregar_al_carrito(product_id="B07VQNY8PK", cantidad=2)` → OK: hecho. Así queda el carrito. CARRITO: - id=B07VQNY8PK | Newdora Botella de Agua Acero Inoxidable 500ml, Aislamiento de Vacío… | 2 unidades × 9,50 € = 19,00 € | existencias: 20 Total del carrito: 19,00 €

**Agente:** Hecho, añadidas dos unidades. El total es 19,00 €. En el carrito hay 2 unidades de «Newdora Botella de Agua Acero Inoxidable 500ml, Aislamiento de Vacío…» a 9,50 € cada una, 19,00 €. Total: 19,00 €. Tu presupuesto es de 45,00 € y te quedan 26,00 €.

**Enviado al TTS:** Hecho, añadidas dos unidades. El total es diecinueve euros. En el carrito hay dos unidades de Newdora Botella de Agua Acero Inoxidable quinientos mililitros a nueve euros con cincuenta céntimos cada una, diecinueve euros. Total: diecinueve euros. Tu presupuesto es de cuarenta y cinco euros y te quedan veintiséis euros.

- ✔ `cart(lines=[{"product": "@elegida", "quantity": 2}])` — carrito: 2 × B07VQNY8PK

## Turno 3 (5.3 s)

**Usuario (texto):** Mejor que sean cuatro.

- `cambiar_cantidad(product_id="B07VQNY8PK", cantidad=4)` → OK: hecho. Así queda el carrito. CARRITO: - id=B07VQNY8PK | Newdora Botella de Agua Acero Inoxidable 500ml, Aislamiento de Vacío… | 4 unidades × 9,50 € = 38,00 € | existencias: 20 Total del carrito: 38,00 €

**Agente:** Hecho, añadidas dos unidades más. El total es 38,00 €. En el carrito hay 4 unidades de «Newdora Botella de Agua Acero Inoxidable 500ml, Aislamiento de Vacío…» a 9,50 € cada una, 38,00 €. Total: 38,00 €. Tu presupuesto es de 45,00 € y te quedan 7,00 €.

**Enviado al TTS:** Hecho, añadidas dos unidades más. El total es treinta y ocho euros. En el carrito hay cuatro unidades de Newdora Botella de Agua Acero Inoxidable quinientos mililitros a nueve euros con cincuenta céntimos cada una, treinta y ocho euros. Total: treinta y ocho euros. Tu presupuesto es de cuarenta y cinco euros y te quedan siete euros.

- ✔ `cart(lines=[{"product": "@elegida", "quantity": 4}])` — carrito: 4 × B07VQNY8PK
- ✔ `budget(cents=4500)` — presupuesto en el estado: 4500

## Turno 4 (2.3 s)

**Usuario (texto):** Ciérralo.

- `cotizar()` → OK: cotización creada; falta la confirmación del usuario.

**Agente:** Te repito el pedido antes de registrarlo: 4 unidades de «Newdora Botella de Agua Acero Inoxidable 500ml, Aislamiento de Vacío…» a 9,50 € cada una, 38,00 €. Total: 38,00 €. Tu presupuesto es de 45,00 € y te quedan 7,00 €. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar. *(esperando confirmación)*

**Enviado al TTS:** Te repito el pedido antes de registrarlo: cuatro unidades de Newdora Botella de Agua Acero Inoxidable quinientos mililitros a nueve euros con cincuenta céntimos cada una, treinta y ocho euros. Total: treinta y ocho euros. Tu presupuesto es de cuarenta y cinco euros y te quedan siete euros. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar.

- ✔ `awaiting_confirmation(value=true)` — esperando confirmación: sí
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 5 (0.0 s)

**Usuario (texto):** Sí.

- `confirmar_pedido(quote_id="9129d7dffa2f48e6b669f523d5c1f65a")` → OK: pedido registrado

**Agente:** Pedido número 1 registrado: 4 unidades de «Newdora Botella de Agua Acero Inoxidable 500ml, Aislamiento de Vacío…» a 9,50 € cada una, 38,00 €. Total: 38,00 €. Gracias por tu compra.

**Enviado al TTS:** Pedido número uno registrado: cuatro unidades de Newdora Botella de Agua Acero Inoxidable quinientos mililitros a nueve euros con cincuenta céntimos cada una, treinta y ocho euros. Total: treinta y ocho euros. Gracias por tu compra.

- ✔ `orders(count=1)` — pedidos registrados: 1

## Comprobaciones finales

- ✔ `orders(count=1)` — pedidos registrados: 1
- ✔ `order(lines=[{"product": "@elegida", "quantity": 4}], total_cents=3800)` — pedido 1: 4 × B07VQNY8PK; total 3800 céntimos
- ✔ `stock(product="@elegida", equals=16)` — existencias de B07VQNY8PK: 16
- ✔ `cart(empty=true)` — carrito: vacío
- ✔ `budget(cents=4500)` — presupuesto en el estado: 4500

## Violaciones de restricciones

- Ninguna.

## Estado final de la tienda

- Pedido 1: total 38,00 €
  - pedido 1: 4 × `B07VQNY8PK` a 9,50 €
- Inventario `B07VQNY8PK`: 46 → 16
- Líneas de carrito pendientes: 0

## Latencia por turno (segundos)

| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total | Audio de respuesta |
|---|---|---|---|---|---|---|---|
| 1 | 0.00 | 0.03 | 7.65 | 0.03 | 0.00 | 7.71 | 0.0 s |
| 2 | 0.00 | 0.00 | 5.03 | 0.04 | 0.00 | 5.07 | 0.0 s |
| 3 | 0.00 | 0.00 | 5.20 | 0.06 | 0.00 | 5.26 | 0.0 s |
| 4 | 0.00 | 0.00 | 2.22 | 0.04 | 0.00 | 2.26 | 0.0 s |
| 5 | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 | 0.03 | 0.0 s |
| **Media de los turnos con LLM (4)** | 0.00 | 0.01 | 5.03 | 0.04 | 0.00 | 5.08 | |
| **Media de los turnos sin LLM (1)** | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 | 0.03 | |

