# 16_quitar_del_carrito — Dos productos y quitar uno

- Veredicto: **correcto**
- Entrada: texto
- Tipo: `quitar_del_carrito`
- Qué se prueba: El usuario añade dos productos en un mismo turno, quita el primero y compra. El pedido solo debe llevar el segundo y el inventario del primero no debe cambiar.

## Turno 1 (12.1 s)

**Usuario (texto):** Busco un teclado inalámbrico.

- `buscar_productos(consulta="teclado inalámbrico")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B09DBFG8W3 | Mimei Teclado silencioso inalámbrico, Teclado de conexión Estable y Recargable por USB Aplicable a los Cuatro Sistemas operativos Que admiten Bluetooth 28,5 12 2,2 CM Superb | marca: Mimei | color: Negro | precio: 42,90 …

**Agente:** Tengo el teclado inalámbrico Mimei por 42,90 €, el TedGem por 25,59 €, el Phoenix Technologies por 18,24 €, el TECKNET por 45,00 € y el Zienstar por 21,99 €. ¿Te interesa alguno?

**Enviado al TTS:** Tengo el teclado inalámbrico Mimei por cuarenta y dos euros con noventa céntimos, el TedGem por veinticinco euros con cincuenta y nueve céntimos, el Phoenix Technologies por dieciocho euros con veinticuatro céntimos, el TECKNET por cuarenta y cinco euros y el Zienstar por veintiún euros con noventa y nueve céntimos. ¿Te interesa alguno?

- ✔ `cart(empty=true)` — carrito: vacío

> `@primero` = `B09DBFG8W3` (candidate:1): Mimei Teclado silencioso inalámbrico, Teclado de conexión Estable y Recargable por USB Aplicable a los Cuatro Sistemas operativos Que admiten Bluetooth 28,5 12 2,2 CM Superb

> `@segundo` = `B07XD94VGX` (candidate:2): Teclado y Raton Inalambrico Español, TedGem 2.4G Teclado Inalambrico USB Teclado Raton Inalambrico PC Ergonómico Teclado Inalambrico PC con 105 Tecla para Windows 7/8/10/2000 / XP/Vista (Black)

> **Suceso externo:** la tienda deja `B09DBFG8W3` (@primero) con precio 15,00 € y existencias 20.

> **Suceso externo:** la tienda deja `B07XD94VGX` (@segundo) con precio 18,00 € y existencias 20.

## Turno 2 (9.7 s)

**Usuario (texto):** Añade uno del primero y uno del segundo.

- `agregar_al_carrito(product_id="B09DBFG8W3", cantidad=1)` → OK: hecho. Así queda el carrito. CARRITO: - id=B09DBFG8W3 | Mimei Teclado silencioso inalámbrico, Teclado de conexión Estable y… | 1 unidad × 15,00 € = 15,00 € | existencias: 20 Total del carrito: 15,00 €
- `agregar_al_carrito(product_id="B07XD94VGX", cantidad=1)` → OK: hecho. Así queda el carrito. CARRITO: - id=B09DBFG8W3 | Mimei Teclado silencioso inalámbrico, Teclado de conexión Estable y… | 1 unidad × 15,00 € = 15,00 € | existencias: 20 - id=B07XD94VGX | Teclado y Raton Inalambrico Español, TedGem 2.4G Teclado Inalambrico… | 1 unidad × 18,00 € = 18,00 € | exist…

**Agente:** Hecho, añadidos dos teclados al carrito. En el carrito hay 1 unidad de «Mimei Teclado silencioso inalámbrico, Teclado de conexión Estable y…» a 15,00 € cada una, 15,00 €; 1 unidad de «Teclado y Raton Inalambrico Español, TedGem 2.4G Teclado Inalambrico…» a 18,00 € cada una, 18,00 €. Total: 33,00 €.

**Enviado al TTS:** Hecho, añadidos dos teclados al carrito. En el carrito hay una unidad de Mimei Teclado silencioso inalámbrico a quince euros cada una, quince euros, una unidad de Teclado y Raton Inalambrico Español a dieciocho euros cada una, dieciocho euros. Total: treinta y tres euros.

- ✔ `cart(lines=[{"product": "@primero", "quantity": 1}, {"product": "@segundo", "quantity": 1}])` — carrito: 1 × B09DBFG8W3, 1 × B07XD94VGX

## Turno 3 (8.5 s)

**Usuario (texto):** Quita el primero.

- `quitar_del_carrito(product_id="B09DBFG8W3")` → OK: hecho. Así queda el carrito. CARRITO: - id=B07XD94VGX | Teclado y Raton Inalambrico Español, TedGem 2.4G Teclado Inalambrico… | 1 unidad × 18,00 € = 18,00 € | existencias: 20 Total del carrito: 18,00 €

**Agente:** Hecho, el carrito ahora contiene solo el teclado inalámbrico TedGem por 18,00 €. En el carrito hay 1 unidad de «Teclado y Raton Inalambrico Español, TedGem 2.4G Teclado Inalambrico…» a 18,00 € cada una, 18,00 €. Total: 18,00 €.

**Enviado al TTS:** Hecho, el carrito ahora contiene solo el teclado inalámbrico TedGem por dieciocho euros. En el carrito hay una unidad de Teclado y Raton Inalambrico Español a dieciocho euros cada una, dieciocho euros. Total: dieciocho euros.

- ✔ `cart(lines=[{"product": "@segundo", "quantity": 1}])` — carrito: 1 × B07XD94VGX

## Turno 4 (3.3 s)

**Usuario (texto):** Cierra el pedido.

- `cotizar()` → OK: cotización creada; falta la confirmación del usuario.

**Agente:** Te repito el pedido antes de registrarlo: 1 unidad de «Teclado y Raton Inalambrico Español, TedGem 2.4G Teclado Inalambrico…» a 18,00 € cada una, 18,00 €. Total: 18,00 €. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar. *(esperando confirmación)*

**Enviado al TTS:** Te repito el pedido antes de registrarlo: una unidad de Teclado y Raton Inalambrico Español a dieciocho euros cada una, dieciocho euros. Total: dieciocho euros. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar.

- ✔ `awaiting_confirmation(value=true)` — esperando confirmación: sí
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 5 (0.0 s)

**Usuario (texto):** Sí.

- `confirmar_pedido(quote_id="bfd83a8d1e234c7dacf20b69bbc90d8d")` → OK: pedido registrado

**Agente:** Pedido número 1 registrado: 1 unidad de «Teclado y Raton Inalambrico Español, TedGem 2.4G Teclado Inalambrico…» a 18,00 € cada una, 18,00 €. Total: 18,00 €. Gracias por tu compra.

**Enviado al TTS:** Pedido número uno registrado: una unidad de Teclado y Raton Inalambrico Español a dieciocho euros cada una, dieciocho euros. Total: dieciocho euros. Gracias por tu compra.

- ✔ `orders(count=1)` — pedidos registrados: 1

## Comprobaciones finales

- ✔ `orders(count=1)` — pedidos registrados: 1
- ✔ `order(lines=[{"product": "@segundo", "quantity": 1}], total_cents=1800)` — pedido 1: 1 × B07XD94VGX; total 1800 céntimos
- ✔ `stock(product="@primero", equals=20)` — existencias de B09DBFG8W3: 20
- ✔ `stock(product="@segundo", equals=19)` — existencias de B07XD94VGX: 19
- ✔ `cart(empty=true)` — carrito: vacío

## Violaciones de restricciones

- Ninguna.

## Estado final de la tienda

- Pedido 1: total 18,00 €
  - pedido 1: 1 × `B07XD94VGX` a 18,00 €
- Inventario `B07XD94VGX`: 12 → 19
- Inventario `B09DBFG8W3`: 21 → 20
- Líneas de carrito pendientes: 0

## Latencia por turno (segundos)

| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total | Audio de respuesta |
|---|---|---|---|---|---|---|---|
| 1 | 0.00 | 0.07 | 12.05 | 0.02 | 0.00 | 12.14 | 0.0 s |
| 2 | 0.00 | 0.00 | 9.62 | 0.07 | 0.00 | 9.69 | 0.0 s |
| 3 | 0.00 | 0.00 | 8.42 | 0.04 | 0.00 | 8.46 | 0.0 s |
| 4 | 0.00 | 0.00 | 3.24 | 0.03 | 0.00 | 3.27 | 0.0 s |
| 5 | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 | 0.03 | 0.0 s |
| **Media de los turnos con LLM (4)** | 0.00 | 0.02 | 8.33 | 0.04 | 0.00 | 8.39 | |
| **Media de los turnos sin LLM (1)** | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 | 0.03 | |

