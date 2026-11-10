# 08_cantidad_invalida — Cantidad inválida

- Veredicto: **correcto**
- Entrada: texto
- Tipo: `cantidad_invalida`
- Qué se prueba: El usuario pide cero unidades y después una cantidad negativa. Ninguna de las dos debe llegar al carrito.

## Turno 1 (8.2 s)

**Usuario (texto):** Busco un cargador USB C.

- `buscar_productos(consulta="cargador USB C")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B07MBYH3F7 | Cable USB Tipo C [3 Pack 1M] Cable Cargador Tipo C De Nylon Carga Rápida Movil Tipo C USB Cargador para Samsung Galaxy S10/S9/S8/A20/A40/A50/A70, Huawei P9/P10/P20/P30, Nintendo Switch, Sony Xperia | marca: Yosou | color…

**Agente:** Tengo el Cable USB Tipo C [3 Pack 1M] de Yosou por 13,65 €, el cargador JOOMFEEN USB Tipo C por 9,96 €, el mismo cargador pero de color Plata por 25,13 €, el cargador Avolare de 45W por 35,15 € y el cargador para iPhone de Unique Secure por 57,07 €. ¿Te interesa alguno?

**Enviado al TTS:** Tengo el Cable USB Tipo C, tres Pack 1M, de Yosou por trece euros con sesenta y cinco céntimos, el cargador JOOMFEEN USB Tipo C por nueve euros con noventa y seis céntimos, el mismo cargador pero de color Plata por veinticinco euros con trece céntimos, el cargador Avolare de cuarenta y cinco vatios por treinta y cinco euros con quince céntimos y el cargador para iPhone de Unique Secure por cincuenta y siete euros con siete céntimos. ¿Te interesa alguno?

- ✔ `cart(empty=true)` — carrito: vacío

> `@elegido` = `B07MBYH3F7` (candidate:1): Cable USB Tipo C [3 Pack 1M] Cable Cargador Tipo C De Nylon Carga Rápida Movil Tipo C USB Cargador para Samsung Galaxy S10/S9/S8/A20/A40/A50/A70, Huawei P9/P10/P20/P30, Nintendo Switch, Sony Xperia

> **Suceso externo:** la tienda deja `B07MBYH3F7` (@elegido) con precio 8,00 € y existencias 20.

## Turno 2 (4.9 s)

**Usuario (texto):** Añade cero unidades del primero.

- `quitar_del_carrito(product_id="B07MBYH3F7")` → RECHAZADO: [no_esta_en_el_carrito] El producto B07MBYH3F7 no está en el carrito.

**Agente:** El producto que has buscado no está en el carrito. ¿Quieres añadirlo?

**Enviado al TTS:** El producto que has buscado no está en el carrito. ¿Quieres añadirlo?

- ✔ `cart(empty=true)` — carrito: vacío

## Turno 3 (3.6 s)

**Usuario (texto):** Añade menos dos unidades del primero.

**Agente:** El producto que buscas no está en el carrito. ¿Quieres añadirlo?

**Enviado al TTS:** El producto que buscas no está en el carrito. ¿Quieres añadirlo?

- ✔ `cart(empty=true)` — carrito: vacío

## Comprobaciones finales

- ✔ `orders(count=0)` — pedidos registrados: 0
- ✔ `cart(empty=true)` — carrito: vacío
- ✔ `stock(product="@elegido", equals=20)` — existencias de B07MBYH3F7: 20

## Violaciones de restricciones

- Ninguna.

## Estado final de la tienda

- Inventario `B07MBYH3F7`: 11 → 20
- Líneas de carrito pendientes: 0

## Latencia por turno (segundos)

| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total | Audio de respuesta |
|---|---|---|---|---|---|---|---|
| 1 | 0.00 | 0.03 | 8.12 | 0.03 | 0.00 | 8.17 | 0.0 s |
| 2 | 0.00 | 0.00 | 4.91 | 0.03 | 0.00 | 4.94 | 0.0 s |
| 3 | 0.00 | 0.00 | 3.57 | 0.03 | 0.00 | 3.60 | 0.0 s |
| **Media de los turnos con LLM (3)** | 0.00 | 0.01 | 5.53 | 0.03 | 0.00 | 5.57 | |

