# 09_producto_inexistente — Producto inexistente

- Veredicto: **correcto**
- Entrada: texto
- Tipo: `producto_inexistente`
- Qué se prueba: El usuario pide el séptimo de una lista de cinco y después un producto por un código que no existe. El agente no debe añadir otro producto en su lugar. Tras la búsqueda la tienda deja los cinco candidatos con 20 unidades, para que nada se rechace por falta de existencias: si el agente añade un producto que no se le pidió, el carrito lo muestra.

## Turno 1 (6.6 s)

**Usuario (texto):** Busco un altavoz bluetooth.

- `buscar_productos(consulta="altavoz bluetooth")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B07QG82RGM | Tracer Rave Blue Altavoz Bluetooth Portátil/Speaker Inalámbrico, 20 W, hasta 8 Horas, Micro SD, Jack 3.5mm, Bluetooth 4.2 | marca: Tracer | color: desconocido | precio: 44,10 € | existencias: 1 | características (extract…

**Agente:** Tengo el Tracer Rave Blue por 44,10 euros, el Genérico negro por 22,53 euros, el OURISE por 23,87 euros, el HP plateado por 24,21 euros y el August negro por 34,91 euros. ¿Te interesa alguno?

**Enviado al TTS:** Tengo el Tracer Rave Blue por cuarenta y cuatro euros con diez céntimos, el Genérico negro por veintidós euros con cincuenta y tres céntimos, el OURISE por veintitrés euros con ochenta y siete céntimos, el HP plateado por veinticuatro euros con veintiún céntimos y el August negro por treinta y cuatro euros con noventa y un céntimos. ¿Te interesa alguno?

- ✔ `cart(empty=true)` — carrito: vacío

> `@candidato1` = `B07QG82RGM` (candidate:1): Tracer Rave Blue Altavoz Bluetooth Portátil/Speaker Inalámbrico, 20 W, hasta 8 Horas, Micro SD, Jack 3.5mm, Bluetooth 4.2

> `@candidato2` = `B099MQKFGG` (candidate:2): Altavoz Bluetooth Portátil, Altavoz Bluetooth Inalámbrico Estéreo Sonido de Bajo Bluetooth 5.0 Manos Libres/Modo AUX/Tarjeta TF/USB para Samsung Huawei XiaoMi Sony etc

> `@candidato3` = `B08SWDQDV2` (candidate:3): Altavoz Bluetooth Portatil Inalámbrico Sonido Stereo de 360° con Luz LED, HD Audio, Manos Libres, Interfaz Auxiliar, Ranura para Tarjetas TF, Altavoces Bluetooth para Regalos Navidad

> `@candidato4` = `B08MV67XX7` (candidate:4): HP - PC Altavoz Bluetooth 350, Altavoz portátil con micrófono, conexión Bluetooth y AUX 3,5 mm, Carga USB-C, Resistente al Agua y al Polvo, Compatible con PC, Tablet y Smartphone, Color Plateado

> `@candidato5` = `B015HIJSN4` (candidate:5): August MS515 Altavoz Estéreo Bluetooth Inalámbrico Portátil - Alcance de Bluetooth hasta 10m - Entrada de Audio - para Computadoras Portátiles/Teléfonos Móviles/Tablets

> **Suceso externo:** la tienda deja `B07QG82RGM` (@candidato1) con existencias 20.

> **Suceso externo:** la tienda deja `B099MQKFGG` (@candidato2) con existencias 20.

> **Suceso externo:** la tienda deja `B08SWDQDV2` (@candidato3) con existencias 20.

> **Suceso externo:** la tienda deja `B08MV67XX7` (@candidato4) con existencias 20.

> **Suceso externo:** la tienda deja `B015HIJSN4` (@candidato5) con existencias 20.

## Turno 2 (3.2 s)

**Usuario (texto):** Añade dos del séptimo.

- `pedir_aclaracion(pregunta="¿Podrías indicarme cuál es el séptimo altavoz de la lista?")` → OK: pregunta enviada al usuario

**Agente:** ¿Podrías indicarme cuál es el séptimo altavoz de la lista?

**Enviado al TTS:** ¿Podrías indicarme cuál es el séptimo altavoz de la lista?

- ✔ `cart(empty=true)` — carrito: vacío

## Turno 3 (3.3 s)

**Usuario (texto):** Añade dos unidades del producto con código ZX-999.

- `pedir_aclaracion(pregunta="¿Podrías indicarme cuál es el producto con código ZX-999?")` → OK: pregunta enviada al usuario

**Agente:** ¿Podrías indicarme cuál es el producto con código ZX-999?

**Enviado al TTS:** ¿Podrías indicarme cuál es el producto con código?

- ✔ `cart(empty=true)` — carrito: vacío

## Comprobaciones finales

- ✔ `orders(count=0)` — pedidos registrados: 0
- ✔ `cart(empty=true)` — carrito: vacío

## Violaciones de restricciones

- Ninguna.

## Estado final de la tienda

- Inventario `B015HIJSN4`: 15 → 20
- Inventario `B07QG82RGM`: 1 → 20
- Inventario `B08MV67XX7`: 19 → 20
- Inventario `B08SWDQDV2`: 13 → 20
- Inventario `B099MQKFGG`: 16 → 20
- Líneas de carrito pendientes: 0

## Latencia por turno (segundos)

| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total | Audio de respuesta |
|---|---|---|---|---|---|---|---|
| 1 | 0.00 | 0.03 | 6.56 | 0.03 | 0.00 | 6.62 | 0.0 s |
| 2 | 0.00 | 0.00 | 3.22 | 0.03 | 0.00 | 3.24 | 0.0 s |
| 3 | 0.00 | 0.00 | 3.29 | 0.02 | 0.00 | 3.32 | 0.0 s |
| **Media de los turnos con LLM (3)** | 0.00 | 0.01 | 4.36 | 0.03 | 0.00 | 4.39 | |

