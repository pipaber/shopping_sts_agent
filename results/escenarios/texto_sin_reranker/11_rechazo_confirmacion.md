# 11_rechazo_confirmacion — Rechazo en la confirmación

- Veredicto: **correcto**
- Entrada: texto
- Tipo: `rechazo_confirmacion`
- Qué se prueba: El usuario llega a la cotización y contesta que no. No debe registrarse ningún pedido y el carrito debe quedar como estaba.

## Turno 1 (8.7 s)

**Usuario (texto):** Busco unas bombillas LED.

- `buscar_productos(consulta="bombillas LED")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B072BG3H7Y | 1 bombilla LED de xenón blanco con halo | marca: Global Fortune | color: desconocido | precio: 17,01 € | existencias: 4 | características (extracto): 1 par de bombillas para faros LED para BMW con halo de alta potencia, …

**Agente:** Tengo estas opciones: 1 bombilla LED de xenón blanco por 17,01 €, 10 unidades de bombillas LED MENTA blancas frías por 24,96 €, 12000LM H1 LED para coches por 63,71 €, 6 bombillas LED Philips blancas cálidas por 14,22 € y 10 bombillas LED Eofiti blancas frías por 16,77 €. ¿Cuál te interesa?

**Enviado al TTS:** Tengo estas opciones: uno bombilla LED de xenón blanco por diecisiete euros con un céntimo, diez unidades de bombillas LED MENTA blancas frías por veinticuatro euros con noventa y seis céntimos, H1 LED para coches por sesenta y tres euros con setenta y un céntimos, seis bombillas LED Philips blancas cálidas por catorce euros con veintidós céntimos y diez bombillas LED Eofiti blancas frías por dieciséis euros con setenta y siete céntimos. ¿Cuál te interesa?

- ✔ `cart(empty=true)` — carrito: vacío

> `@elegidas` = `B072BG3H7Y` (candidate:1): 1 bombilla LED de xenón blanco con halo

> **Suceso externo:** la tienda deja `B072BG3H7Y` (@elegidas) con precio 6,00 € y existencias 20.

## Turno 2 (4.8 s)

**Usuario (texto):** Añade dos de la primera opción.

- `agregar_al_carrito(product_id="B072BG3H7Y", cantidad=2)` → OK: hecho. Así queda el carrito. CARRITO: - id=B072BG3H7Y | 1 bombilla LED de xenón blanco con halo | 2 unidades × 6,00 € = 12,00 € | existencias: 20 Total del carrito: 12,00 €

**Agente:** Hecho, añadidas dos unidades. En el carrito hay 2 unidades de «1 bombilla LED de xenón blanco con halo» a 6,00 € cada una, 12,00 €. Total: 12,00 €.

**Enviado al TTS:** Hecho, añadidas dos unidades. En el carrito hay dos unidades de uno bombilla LED de xenón blanco a seis euros cada una, doce euros. Total: doce euros.

- ✔ `cart(lines=[{"product": "@elegidas", "quantity": 2}])` — carrito: 2 × B072BG3H7Y

## Turno 3 (2.3 s)

**Usuario (texto):** Cierra el pedido.

- `cotizar()` → OK: cotización creada; falta la confirmación del usuario.

**Agente:** Te repito el pedido antes de registrarlo: 2 unidades de «1 bombilla LED de xenón blanco con halo» a 6,00 € cada una, 12,00 €. Total: 12,00 €. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar. *(esperando confirmación)*

**Enviado al TTS:** Te repito el pedido antes de registrarlo: dos unidades de uno bombilla LED de xenón blanco a seis euros cada una, doce euros. Total: doce euros. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar.

- ✔ `awaiting_confirmation(value=true)` — esperando confirmación: sí
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 4 (0.0 s)

**Usuario (texto):** No, cancélalo.

**Agente:** De acuerdo, no registro el pedido. Tu carrito sigue como estaba; dime si quieres cambiar algo.

**Enviado al TTS:** De acuerdo, no registro el pedido. Tu carrito sigue como estaba, dime si quieres cambiar algo.

- ✔ `orders(count=0)` — pedidos registrados: 0
- ✔ `awaiting_confirmation(value=false)` — esperando confirmación: no
- ✔ `cart(lines=[{"product": "@elegidas", "quantity": 2}])` — carrito: 2 × B072BG3H7Y

## Comprobaciones finales

- ✔ `orders(count=0)` — pedidos registrados: 0
- ✔ `cart(lines=[{"product": "@elegidas", "quantity": 2}])` — carrito: 2 × B072BG3H7Y
- ✔ `stock(product="@elegidas", equals=20)` — existencias de B072BG3H7Y: 20

## Violaciones de restricciones

- Ninguna.

## Estado final de la tienda

- Inventario `B072BG3H7Y`: 4 → 20
- Líneas de carrito pendientes: 1

## Latencia por turno (segundos)

| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total | Audio de respuesta |
|---|---|---|---|---|---|---|---|
| 1 | 0.00 | 0.03 | 8.60 | 0.03 | 0.00 | 8.65 | 0.0 s |
| 2 | 0.00 | 0.00 | 4.77 | 0.05 | 0.00 | 4.83 | 0.0 s |
| 3 | 0.00 | 0.00 | 2.21 | 0.04 | 0.00 | 2.25 | 0.0 s |
| 4 | 0.00 | 0.00 | 0.00 | 0.01 | 0.00 | 0.01 | 0.0 s |
| **Media de los turnos con LLM (3)** | 0.00 | 0.01 | 5.19 | 0.04 | 0.00 | 5.24 | |
| **Media de los turnos sin LLM (1)** | 0.00 | 0.00 | 0.00 | 0.01 | 0.00 | 0.01 | |

