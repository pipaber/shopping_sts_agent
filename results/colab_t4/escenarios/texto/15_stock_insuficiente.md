# 15_stock_insuficiente — Stock insuficiente al añadir

- Veredicto: **correcto**
- Entrada: texto
- Tipo: `stock_insuficiente`
- Qué se prueba: Del primer candidato quedan tres unidades y el usuario pide cinco: el carrito no debe cambiar. Después pide las tres que quedan.

## Turno 1 (12.6 s)

**Usuario (texto):** Busco una linterna LED.

- `buscar_productos(consulta="linterna LED")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B096M7FCYF | Linterna led recargable, 4 modos de luz, carga solar, IPX4 resistente al agua, apto para luces de emergencia domésticas, luces de camping al aire libre, luces de trabajo | marca: hctaw | color: desconocido | precio: 22,8…

**Agente:** Tengo la linterna LED recargable de HCTAW por 22,83 €, la linterna LED profesional de GS1 por 9,84 €, la linterna de mano de Lumpur por 34,33 €, la linterna mini portátil de Simpeak por 21,12 € y la linterna LED iTimo por 15,73 €. ¿Te interesa alguna?

**Enviado al TTS:** Tengo la linterna LED recargable de HCTAW por veintidós euros con ochenta y tres céntimos, la linterna LED profesional de GS1 por nueve euros con ochenta y cuatro céntimos, la linterna de mano de Lumpur por treinta y cuatro euros con treinta y tres céntimos, la linterna mini portátil de Simpeak por veintiún euros con doce céntimos y la linterna LED iTimo por quince euros con setenta y tres céntimos. ¿Te interesa alguna?

- ✔ `cart(empty=true)` — carrito: vacío

> `@elegida` = `B096M7FCYF` (candidate:1): Linterna led recargable, 4 modos de luz, carga solar, IPX4 resistente al agua, apto para luces de emergencia domésticas, luces de camping al aire libre, luces de trabajo

> **Suceso externo:** la tienda deja `B096M7FCYF` (@elegida) con precio 7,00 € y existencias 3.

## Turno 2 (8.3 s)

**Usuario (texto):** Añade cinco de la primera.

- `agregar_al_carrito(product_id="B096M7FCYF", cantidad=5)` → RECHAZADO: [stock_insuficiente] Solo quedan 3 unidades del producto B096M7FCYF y se pidieron 5.

**Agente:** Lo siento, solo quedan 3 unidades disponibles. ¿Te interesa 3 unidades en lugar de 5?

**Enviado al TTS:** Lo siento, solo quedan tres unidades disponibles. ¿Te interesa tres unidades en lugar de cinco?

- ✔ `cart(empty=true)` — carrito: vacío
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 3 (7.8 s)

**Usuario (texto):** Pues ponme las tres que quedan.

- `agregar_al_carrito(product_id="B096M7FCYF", cantidad=3)` → OK: hecho. Así queda el carrito. CARRITO: - id=B096M7FCYF | Linterna led recargable, 4 modos de luz, carga solar, IPX4 resistente… | 3 unidades × 7,00 € = 21,00 € | existencias: 3 Total del carrito: 21,00 €

**Agente:** Hecho, añadidas tres unidades. En el carrito hay 3 unidades de «Linterna led recargable, 4 modos de luz, carga solar, IPX4 resistente…» a 7,00 € cada una, 21,00 €. Total: 21,00 €.

**Enviado al TTS:** Hecho, añadidas tres unidades. En el carrito hay tres unidades de Linterna led recargable a siete euros cada una, veintiún euros. Total: veintiún euros.

- ✔ `cart(lines=[{"product": "@elegida", "quantity": 3}])` — carrito: 3 × B096M7FCYF

## Comprobaciones finales

- ✔ `orders(count=0)` — pedidos registrados: 0
- ✔ `cart(lines=[{"product": "@elegida", "quantity": 3}])` — carrito: 3 × B096M7FCYF
- ✔ `stock(product="@elegida", equals=3)` — existencias de B096M7FCYF: 3

## Violaciones de restricciones

- Ninguna.

## Estado final de la tienda

- Inventario `B096M7FCYF`: 24 → 3
- Líneas de carrito pendientes: 1

## Latencia por turno (segundos)

| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total | Audio de respuesta |
|---|---|---|---|---|---|---|---|
| 1 | 0.00 | 0.07 | 12.53 | 0.02 | 0.00 | 12.62 | 0.0 s |
| 2 | 0.00 | 0.00 | 8.22 | 0.03 | 0.00 | 8.25 | 0.0 s |
| 3 | 0.00 | 0.00 | 7.78 | 0.05 | 0.00 | 7.83 | 0.0 s |
| **Media de los turnos con LLM (3)** | 0.00 | 0.02 | 9.51 | 0.03 | 0.00 | 9.57 | |

