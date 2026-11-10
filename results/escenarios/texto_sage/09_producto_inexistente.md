# 09_producto_inexistente — Producto inexistente

- Veredicto: **correcto**
- Entrada: texto
- Tipo: `producto_inexistente`
- Qué se prueba: El usuario pide el séptimo de una lista de cinco y después un producto por un código que no existe. El agente no debe añadir otro producto en su lugar. Tras la búsqueda la tienda deja los cinco candidatos con 20 unidades, para que nada se rechace por falta de existencias: si el agente añade un producto que no se le pidió, el carrito lo muestra.

## Turno 1 (6.5 s)

**Usuario (texto):** Busco un altavoz bluetooth.

- `buscar_productos(consulta="altavoz bluetooth")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B07QG82RGM | Tracer Rave Blue Altavoz Bluetooth Portátil/Speaker Inalámbrico, 20 W, hasta 8 Horas, Micro SD, Jack 3.5mm, Bluetooth 4.2 | marca: Tracer | color: desconocido | precio: 44,10 € | existencias: 1 | características (extract…

**Agente:** Tengo el Tracer Rave Blue por 44,10 €, el HP plateado por 24,21 €, el HP Negro por 163,87 €, el Motorola Negro por 70,16 € y el Sony Amarillo Lima por 50,15 €. ¿Te interesa alguno?

**Enviado al TTS:** Tengo el Tracer Rave Blue por cuarenta y cuatro euros con diez céntimos, el HP plateado por veinticuatro euros con veintiún céntimos, el HP Negro por ciento sesenta y tres euros con ochenta y siete céntimos, el Motorola Negro por setenta euros con dieciséis céntimos y el Sony Amarillo Lima por cincuenta euros con quince céntimos. ¿Te interesa alguno?

- ✔ `cart(empty=true)` — carrito: vacío

> `@candidato1` = `B07QG82RGM` (candidate:1): Tracer Rave Blue Altavoz Bluetooth Portátil/Speaker Inalámbrico, 20 W, hasta 8 Horas, Micro SD, Jack 3.5mm, Bluetooth 4.2

> `@candidato2` = `B08MV67XX7` (candidate:2): HP - PC Altavoz Bluetooth 350, Altavoz portátil con micrófono, conexión Bluetooth y AUX 3,5 mm, Carga USB-C, Resistente al Agua y al Polvo, Compatible con PC, Tablet y Smartphone, Color Plateado

> `@candidato3` = `B08MV7VYY8` (candidate:3): HP - PC Altavoz Bluetooth 350, Altavoz portátil con micrófono, conexión Bluetooth y AUX 3,5 mm, Carga USB-C, Resistente al Agua y al Polvo, Compatible con PC, Tablet y Smartphone, Color Negro

> `@candidato4` = `B07GYCF7N9` (candidate:4): Motorola Sonic Boost 210 - Altavoz inalámbrico Bluetooth, Color Negro

> `@candidato5` = `B08YDXKTTQ` (candidate:5): Sony SRS-XB13 - Altavoz Bluetooth Compacto, Duradero y Potente con EXTRA BASS (Resistente al agua, Inalámbrico, 16h Autonomía), Amarillo Lima

> **Suceso externo:** la tienda deja `B07QG82RGM` (@candidato1) con existencias 20.

> **Suceso externo:** la tienda deja `B08MV67XX7` (@candidato2) con existencias 20.

> **Suceso externo:** la tienda deja `B08MV7VYY8` (@candidato3) con existencias 20.

> **Suceso externo:** la tienda deja `B07GYCF7N9` (@candidato4) con existencias 20.

> **Suceso externo:** la tienda deja `B08YDXKTTQ` (@candidato5) con existencias 20.

## Turno 2 (3.7 s)

**Usuario (texto):** Añade dos del séptimo.

- `pedir_aclaracion(pregunta="Parece que quieres añadir dos del séptimo, pero solo hay cinco productos. ¿Podrías indicarme cuál es el que te interesa?")` → OK: pregunta enviada al usuario

**Agente:** Parece que quieres añadir dos del séptimo, pero solo hay cinco productos. ¿Podrías indicarme cuál es el que te interesa?

**Enviado al TTS:** Parece que quieres añadir dos del séptimo, pero solo hay cinco productos. ¿Podrías indicarme cuál es el que te interesa?

- ✔ `cart(empty=true)` — carrito: vacío

## Turno 3 (3.1 s)

**Usuario (texto):** Añade dos unidades del producto con código ZX-999.

- `pedir_aclaracion(pregunta="¿Podrías indicarme cuál es el altavoz bluetooth que te interesa?")` → OK: pregunta enviada al usuario

**Agente:** ¿Podrías indicarme cuál es el altavoz bluetooth que te interesa?

**Enviado al TTS:** ¿Podrías indicarme cuál es el altavoz bluetooth que te interesa?

- ✔ `cart(empty=true)` — carrito: vacío

## Comprobaciones finales

- ✔ `orders(count=0)` — pedidos registrados: 0
- ✔ `cart(empty=true)` — carrito: vacío

## Violaciones de restricciones

- Ninguna.

## Estado final de la tienda

- Inventario `B07GYCF7N9`: 5 → 20
- Inventario `B07QG82RGM`: 1 → 20
- Inventario `B08MV67XX7`: 19 → 20
- Inventario `B08MV7VYY8`: 7 → 20
- Inventario `B08YDXKTTQ`: 45 → 20
- Líneas de carrito pendientes: 0

## Latencia por turno (segundos)

| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total | Audio de respuesta |
|---|---|---|---|---|---|---|---|
| 1 | 0.00 | 0.04 | 6.42 | 0.02 | 0.00 | 6.47 | 0.0 s |
| 2 | 0.00 | 0.00 | 3.64 | 0.02 | 0.00 | 3.67 | 0.0 s |
| 3 | 0.00 | 0.00 | 3.11 | 0.01 | 0.00 | 3.12 | 0.0 s |
| **Media de los turnos con LLM (3)** | 0.00 | 0.01 | 4.39 | 0.02 | 0.00 | 4.42 | |

