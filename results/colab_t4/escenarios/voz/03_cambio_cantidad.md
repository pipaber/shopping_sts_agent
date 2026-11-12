# 03_cambio_cantidad — Cambio de cantidad manteniendo las demás restricciones

- Veredicto: **correcto**
- Entrada: audio (grabaciones del usuario)
- Tipo: `cambio_cantidad`
- Qué se prueba: El usuario añade dos unidades y después corrige a cuatro. El producto y el presupuesto deben seguir siendo los mismos y el pedido final debe llevar cuatro unidades (38,00 € de un presupuesto de 45 €).

## Turno 1 (26.2 s)

**Usuario (transcripción del ASR):** Busco una botella de agua de acero inoxidable. Mi presupuesto es de 45 euros.

- `fijar_presupuesto(importe_eur=45)` → OK: presupuesto fijado en 45,00 €.
- `buscar_productos(consulta="botella de agua acero inoxidable")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B07VQNY8PK | Newdora Botella de Agua Acero Inoxidable 500ml, Aislamiento de Vacío de Doble Pared, Botellas de Frío/Caliente, con 1 un Cepillo de Limpieza, para Niños, Deporte, Oficina, Gimnasio, Ciclismo, Negro | marca: Newdora | col…

**Agente:** Tengo la botella de agua de Newdora por 6,72 euros, la de KOSAD por 12,37, la de KOUAJ por 18,29 y las de ion8 por 4,97 y 10,79 euros. ¿Te interesa alguna? He anotado un presupuesto de 45,00 €.

**Enviado al TTS:** Tengo la botella de agua de Newdora por seis euros con setenta y dos céntimos, la de KOSAD por doce coma treinta y siete, la de KOUAJ por dieciocho coma veintinueve y las de ion8 por cuatro coma noventa y siete y diez euros con setenta y nueve céntimos. ¿Te interesa alguna? He anotado un presupuesto de cuarenta y cinco euros.

- ✔ `budget(cents=4500)` — presupuesto en el estado: 4500

> `@elegida` = `B07VQNY8PK` (candidate:1): Newdora Botella de Agua Acero Inoxidable 500ml, Aislamiento de Vacío de Doble Pared, Botellas de Frío/Caliente, con 1 un Cepillo de Limpieza, para Niños, Deporte, Oficina, Gimnasio, Ciclismo, Negro

> **Suceso externo:** la tienda deja `B07VQNY8PK` (@elegida) con precio 9,50 € y existencias 20.

## Turno 2 (24.5 s)

**Usuario (transcripción del ASR):** Añade dos de la primera.

- `agregar_al_carrito(product_id="B07VQNY8PK", cantidad=2)` → OK: hecho. Así queda el carrito. CARRITO: - id=B07VQNY8PK | Newdora Botella de Agua Acero Inoxidable 500ml, Aislamiento de Vacío… | 2 unidades × 9,50 € = 19,00 € | existencias: 20 Total del carrito: 19,00 €

**Agente:** Hecho, añadidas dos unidades. El total es 19,00 €. En el carrito hay 2 unidades de «Newdora Botella de Agua Acero Inoxidable 500ml, Aislamiento de Vacío…» a 9,50 € cada una, 19,00 €. Total: 19,00 €. Tu presupuesto es de 45,00 € y te quedan 26,00 €.

**Enviado al TTS:** Hecho, añadidas dos unidades. El total es diecinueve euros. En el carrito hay dos unidades de Newdora Botella de Agua Acero Inoxidable quinientos mililitros a nueve euros con cincuenta céntimos cada una, diecinueve euros. Total: diecinueve euros. Tu presupuesto es de cuarenta y cinco euros y te quedan veintiséis euros.

- ✔ `cart(lines=[{"product": "@elegida", "quantity": 2}])` — carrito: 2 × B07VQNY8PK

## Turno 3 (24.2 s)

**Usuario (transcripción del ASR):** Mejor que sean cuatro.

- `cambiar_cantidad(product_id="B07VQNY8PK", cantidad=4)` → OK: hecho. Así queda el carrito. CARRITO: - id=B07VQNY8PK | Newdora Botella de Agua Acero Inoxidable 500ml, Aislamiento de Vacío… | 4 unidades × 9,50 € = 38,00 € | existencias: 20 Total del carrito: 38,00 €

**Agente:** Hecho, el total es 38,00 €. En el carrito hay 4 unidades de «Newdora Botella de Agua Acero Inoxidable 500ml, Aislamiento de Vacío…» a 9,50 € cada una, 38,00 €. Total: 38,00 €. Tu presupuesto es de 45,00 € y te quedan 7,00 €.

**Enviado al TTS:** Hecho, el total es treinta y ocho euros. En el carrito hay cuatro unidades de Newdora Botella de Agua Acero Inoxidable quinientos mililitros a nueve euros con cincuenta céntimos cada una, treinta y ocho euros. Total: treinta y ocho euros. Tu presupuesto es de cuarenta y cinco euros y te quedan siete euros.

- ✔ `cart(lines=[{"product": "@elegida", "quantity": 4}])` — carrito: 4 × B07VQNY8PK
- ✔ `budget(cents=4500)` — presupuesto en el estado: 4500

## Turno 4 (20.7 s)

**Usuario (transcripción del ASR):** Cierralo.

**Texto correcto:** Ciérralo.

- `cotizar()` → OK: cotización creada; falta la confirmación del usuario.

**Agente:** Te repito el pedido antes de registrarlo: 4 unidades de «Newdora Botella de Agua Acero Inoxidable 500ml, Aislamiento de Vacío…» a 9,50 € cada una, 38,00 €. Total: 38,00 €. Tu presupuesto es de 45,00 € y te quedan 7,00 €. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar. *(esperando confirmación)*

**Enviado al TTS:** Te repito el pedido antes de registrarlo: cuatro unidades de Newdora Botella de Agua Acero Inoxidable quinientos mililitros a nueve euros con cincuenta céntimos cada una, treinta y ocho euros. Total: treinta y ocho euros. Tu presupuesto es de cuarenta y cinco euros y te quedan siete euros. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar.

- ✔ `awaiting_confirmation(value=true)` — esperando confirmación: sí
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 5 (11.1 s)

**Usuario (transcripción del ASR):** Sí.

- `confirmar_pedido(quote_id="ddbb7f4c2dd042b38f1564150c35982b")` → OK: pedido registrado

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
| 1 | 0.48 | 0.07 | 12.47 | 0.03 | 13.16 | 26.20 | 23.1 s |
| 2 | 0.38 | 0.00 | 7.45 | 0.04 | 16.59 | 24.47 | 29.3 s |
| 3 | 0.35 | 0.00 | 8.10 | 0.05 | 15.68 | 24.18 | 28.0 s |
| 4 | 0.34 | 0.00 | 2.94 | 0.03 | 17.41 | 20.73 | 30.0 s |
| 5 | 0.36 | 0.00 | 0.00 | 0.04 | 10.70 | 11.09 | 18.7 s |
| **Media de los turnos con LLM (4)** | 0.39 | 0.02 | 7.74 | 0.04 | 15.71 | 23.89 | |
| **Media de los turnos sin LLM (1)** | 0.36 | 0.00 | 0.00 | 0.04 | 10.70 | 11.09 | |

