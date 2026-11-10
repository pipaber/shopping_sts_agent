# 07_presupuesto_excedido — Presupuesto excedido al añadir

- Veredicto: **correcto**
- Entrada: texto
- Tipo: `presupuesto_excedido`
- Qué se prueba: Con 30 € de presupuesto y el producto a 12,00 €, tres unidades (36,00 €) no caben: el carrito no debe cambiar. Dos unidades sí caben.

## Turno 1 (8.4 s)

**Usuario (texto):** Busco una mochila para portátil. Como mucho quiero gastar 30 euros.

- `fijar_presupuesto(importe_eur=30)` → OK: presupuesto fijado en 30,00 €.
- `buscar_productos(consulta="mochila para portátil")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B091TXCPQQ | SONAMBULO Mochila para Portátil, Mochila Unisex Impermeable de hasta 15.6 Pulgadas,Mochila de Portatil con Puerto USB,Mochila Ordenador Portatil Para los Viajes,Escolares o Negocio | marca: SONAMBULO | color: Negro | pre…

**Agente:** Tengo la mochila SONAMBULO por 6,13 euros, la Lubardy por 17,46, la KTMOUW por 24,01, la HOMIEE por 16,35 y la Under Armour por 11,65. ¿Te interesa alguna? He anotado un presupuesto de 30,00 €.

**Enviado al TTS:** Tengo la mochila SONAMBULO por seis euros con trece céntimos, la Lubardy por diecisiete coma cuarenta y seis, la KTMOUW por veinticuatro coma cero uno, la HOMIEE por dieciséis coma treinta y cinco y la Under Armour por once coma sesenta y cinco. ¿Te interesa alguna? He anotado un presupuesto de treinta euros.

- ✔ `budget(cents=3000)` — presupuesto en el estado: 3000
- ✔ `cart(empty=true)` — carrito: vacío

> `@elegida` = `B091TXCPQQ` (candidate:1): SONAMBULO Mochila para Portátil, Mochila Unisex Impermeable de hasta 15.6 Pulgadas,Mochila de Portatil con Puerto USB,Mochila Ordenador Portatil Para los Viajes,Escolares o Negocio

> **Suceso externo:** la tienda deja `B091TXCPQQ` (@elegida) con precio 12,00 € y existencias 20.

## Turno 2 (6.0 s)

**Usuario (texto):** Añade tres de la primera.

- `agregar_al_carrito(product_id="B091TXCPQQ", cantidad=3)` → RECHAZADO: [presupuesto_excedido] El total sería 36,00 € y supera el presupuesto de 30,00 € por 6,00 €. Dentro del presupuesto caben como máximo 2 unidades de este producto.

**Agente:** Lo siento, con tres unidades el total supera tu presupuesto. ¿Te interesa añadir dos en su lugar?

**Enviado al TTS:** Lo siento, con tres unidades el total supera tu presupuesto. ¿Te interesa añadir dos en su lugar?

- ✔ `cart(empty=true)` — carrito: vacío
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 3 (5.4 s)

**Usuario (texto):** Vale, pues ponme dos.

- `agregar_al_carrito(product_id="B091TXCPQQ", cantidad=2)` → OK: hecho. Así queda el carrito. CARRITO: - id=B091TXCPQQ | SONAMBULO Mochila para Portátil, Mochila Unisex Impermeable de hasta… | 2 unidades × 12,00 € = 24,00 € | existencias: 20 Total del carrito: 24,00 €

**Agente:** Hecho, añadidas dos unidades. El total es 24,00 €. En el carrito hay 2 unidades de «SONAMBULO Mochila para Portátil, Mochila Unisex Impermeable de hasta…» a 12,00 € cada una, 24,00 €. Total: 24,00 €. Tu presupuesto es de 30,00 € y te quedan 6,00 €.

**Enviado al TTS:** Hecho, añadidas dos unidades. El total es veinticuatro euros. En el carrito hay dos unidades de SONAMBULO Mochila para Portátil a doce euros cada una, veinticuatro euros. Total: veinticuatro euros. Tu presupuesto es de treinta euros y te quedan seis euros.

- ✔ `cart(lines=[{"product": "@elegida", "quantity": 2}])` — carrito: 2 × B091TXCPQQ

## Comprobaciones finales

- ✔ `orders(count=0)` — pedidos registrados: 0
- ✔ `cart(lines=[{"product": "@elegida", "quantity": 2}])` — carrito: 2 × B091TXCPQQ
- ✔ `budget(cents=3000)` — presupuesto en el estado: 3000
- ✔ `stock(product="@elegida", equals=20)` — existencias de B091TXCPQQ: 20

## Violaciones de restricciones

- Ninguna.

## Estado final de la tienda

- Inventario `B091TXCPQQ`: 42 → 20
- Líneas de carrito pendientes: 1

## Latencia por turno (segundos)

| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total | Audio de respuesta |
|---|---|---|---|---|---|---|---|
| 1 | 0.00 | 0.03 | 8.31 | 0.03 | 0.00 | 8.37 | 0.0 s |
| 2 | 0.00 | 0.00 | 5.98 | 0.03 | 0.00 | 6.01 | 0.0 s |
| 3 | 0.00 | 0.00 | 5.32 | 0.05 | 0.00 | 5.37 | 0.0 s |
| **Media de los turnos con LLM (3)** | 0.00 | 0.01 | 6.54 | 0.04 | 0.00 | 6.59 | |

