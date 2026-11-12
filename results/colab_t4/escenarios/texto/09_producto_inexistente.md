# 09_producto_inexistente — Producto inexistente

- Veredicto: **correcto**
- Entrada: texto
- Tipo: `producto_inexistente`
- Qué se prueba: El usuario pide el séptimo de una lista de cinco y después un producto por un código que no existe. El agente no debe añadir otro producto en su lugar. Tras la búsqueda la tienda deja los cinco candidatos con 20 unidades, para que nada se rechace por falta de existencias: si el agente añade un producto que no se le pidió, el carrito lo muestra.

## Turno 1 (11.8 s)

**Usuario (texto):** Busco un altavoz bluetooth.

- `buscar_productos(consulta="altavoz bluetooth")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B07QG82RGM | Tracer Rave Blue Altavoz Bluetooth Portátil/Speaker Inalámbrico, 20 W, hasta 8 Horas, Micro SD, Jack 3.5mm, Bluetooth 4.2 | marca: Tracer | color: desconocido | precio: 44,10 € | existencias: 1 | características (extract…

**Agente:** Tengo el Tracer Rave Blue por 44,10 euros, el Genérico negro por 22,53 euros, el HP plateado por 24,21 euros, el Motorola Negro por 70,16 euros y el JXFS colorido por 11,83 euros. ¿Te interesa alguno?

**Enviado al TTS:** Tengo el Tracer Rave Blue por cuarenta y cuatro euros con diez céntimos, el Genérico negro por veintidós euros con cincuenta y tres céntimos, el HP plateado por veinticuatro euros con veintiún céntimos, el Motorola Negro por setenta euros con dieciséis céntimos y el JXFS colorido por once euros con ochenta y tres céntimos. ¿Te interesa alguno?

- ✔ `cart(empty=true)` — carrito: vacío

> `@candidato1` = `B07QG82RGM` (candidate:1): Tracer Rave Blue Altavoz Bluetooth Portátil/Speaker Inalámbrico, 20 W, hasta 8 Horas, Micro SD, Jack 3.5mm, Bluetooth 4.2

> `@candidato2` = `B099MQKFGG` (candidate:2): Altavoz Bluetooth Portátil, Altavoz Bluetooth Inalámbrico Estéreo Sonido de Bajo Bluetooth 5.0 Manos Libres/Modo AUX/Tarjeta TF/USB para Samsung Huawei XiaoMi Sony etc

> `@candidato3` = `B08MV67XX7` (candidate:3): HP - PC Altavoz Bluetooth 350, Altavoz portátil con micrófono, conexión Bluetooth y AUX 3,5 mm, Carga USB-C, Resistente al Agua y al Polvo, Compatible con PC, Tablet y Smartphone, Color Plateado

> `@candidato4` = `B07GYCF7N9` (candidate:4): Motorola Sonic Boost 210 - Altavoz inalámbrico Bluetooth, Color Negro

> `@candidato5` = `B07TY4VMZ3` (candidate:5): JXFS Altavoz Bluetooth con lámpara LED Colorido Bola mágica Altavoz inalámbrico Bluetooth con Control Remoto Navidad Altavoces para Bajos al Aire Libre-Blue

> **Suceso externo:** la tienda deja `B07QG82RGM` (@candidato1) con existencias 20.

> **Suceso externo:** la tienda deja `B099MQKFGG` (@candidato2) con existencias 20.

> **Suceso externo:** la tienda deja `B08MV67XX7` (@candidato3) con existencias 20.

> **Suceso externo:** la tienda deja `B07GYCF7N9` (@candidato4) con existencias 20.

> **Suceso externo:** la tienda deja `B07TY4VMZ3` (@candidato5) con existencias 20.

## Turno 2 (5.3 s)

**Usuario (texto):** Añade dos del séptimo.

- `pedir_aclaracion(pregunta="Parece que quieres añadir dos unidades de un producto que no está en la lista. ¿Podrías indicarme cuál es?")` → OK: pregunta enviada al usuario

**Agente:** Parece que quieres añadir dos unidades de un producto que no está en la lista. ¿Podrías indicarme cuál es?

**Enviado al TTS:** Parece que quieres añadir dos unidades de un producto que no está en la lista. ¿Podrías indicarme cuál es?

- ✔ `cart(empty=true)` — carrito: vacío

## Turno 3 (5.3 s)

**Usuario (texto):** Añade dos unidades del producto con código ZX-999.

- `pedir_aclaracion(pregunta="¿Podrías indicarme cuál es el altavoz que buscas?")` → OK: pregunta enviada al usuario

**Agente:** ¿Podrías indicarme cuál es el altavoz que buscas?

**Enviado al TTS:** ¿Podrías indicarme cuál es el altavoz que buscas?

- ✔ `cart(empty=true)` — carrito: vacío

## Comprobaciones finales

- ✔ `orders(count=0)` — pedidos registrados: 0
- ✔ `cart(empty=true)` — carrito: vacío

## Violaciones de restricciones

- Ninguna.

## Estado final de la tienda

- Inventario `B07GYCF7N9`: 5 → 20
- Inventario `B07QG82RGM`: 1 → 20
- Inventario `B07TY4VMZ3`: 36 → 20
- Inventario `B08MV67XX7`: 19 → 20
- Inventario `B099MQKFGG`: 16 → 20
- Líneas de carrito pendientes: 0

## Latencia por turno (segundos)

| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total | Audio de respuesta |
|---|---|---|---|---|---|---|---|
| 1 | 0.00 | 0.07 | 11.74 | 0.02 | 0.00 | 11.83 | 0.0 s |
| 2 | 0.00 | 0.00 | 5.28 | 0.03 | 0.00 | 5.31 | 0.0 s |
| 3 | 0.00 | 0.00 | 5.27 | 0.03 | 0.00 | 5.30 | 0.0 s |
| **Media de los turnos con LLM (3)** | 0.00 | 0.02 | 7.43 | 0.02 | 0.00 | 7.48 | |

