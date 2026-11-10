# 10_atributo_no_verificable — Atributo no verificable

- Veredicto: **correcto**
- Entrada: texto
- Tipo: `atributo_no_verificable`
- Qué se prueba: El usuario pregunta por la valoración de los clientes, un dato que el catálogo no trae. El agente debe decir que no consta, sin inventarlo y sin tocar el carrito. La comprobación mira el texto completo del producto en el catálogo: si no menciona valoraciones, la respuesta tiene que decir que no consta.

## Turno 1 (7.8 s)

**Usuario (texto):** Busco una sartén antiadherente.

- `buscar_productos(consulta="sartén antiadherente")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B08C73K4CV | ilimiti Sartenes Induccion Antiadherentes 20 cm, Sarten Piedra Aluminio Fundido, Libre de PFOA, Apta para Todo Tipo de Cocina | marca: ilimiti | color: desconocido | precio: 83,75 € | existencias: 46 | características (e…

**Agente:** Tengo la sartén ilimiti de 20 cm por 83,75 euros, la Pensofal de 32 cm por 7,48 euros, la Amazon Basics de 20 cm por 16,97 euros, la ilimiti verde de 24 cm por 3,82 euros y la Jessicadaphne negra por 2,09 euros. ¿Te interesa alguna?

**Enviado al TTS:** Tengo la sartén ilimiti de veinte centímetros por ochenta y tres euros con setenta y cinco céntimos, la Pensofal de treinta y dos centímetros por siete euros con cuarenta y ocho céntimos, la Amazon Basics de veinte centímetros por dieciséis euros con noventa y siete céntimos, la ilimiti verde de veinticuatro centímetros por tres euros con ochenta y dos céntimos y la Jessicadaphne negra por dos euros con nueve céntimos. ¿Te interesa alguna?

- ✔ `cart(empty=true)` — carrito: vacío

> `@elegida` = `B08C73K4CV` (candidate:1): ilimiti Sartenes Induccion Antiadherentes 20 cm, Sarten Piedra Aluminio Fundido, Libre de PFOA, Apta para Todo Tipo de Cocina

## Turno 2 (4.8 s)

**Usuario (texto):** ¿Qué valoración le dan los clientes a la primera?

- `detalle_producto(product_id="B08C73K4CV")` → OK: [1] id=B08C73K4CV | ilimiti Sartenes Induccion Antiadherentes 20 cm, Sarten Piedra Aluminio Fundido, Libre de PFOA, Apta para Todo Tipo de Cocina | marca: ilimiti | color: desconocido | precio: 83,75 € | existencias: 46 | características (extracto): APTO PARA TODOS TIPOS DE COCINAS: La sartén antiad…

**Agente:** El catálogo no indica una valoración de los clientes para este producto.

**Enviado al TTS:** El catálogo no indica una valoración de los clientes para este producto.

- ✔ `declares_unknown(product="@elegida", keywords=["valoraci", "estrellas", "reseñ", "opiniones", "puntuaci"])` — dato en el catálogo: no; la respuesta dice que no consta: sí
- ✔ `cart(empty=true)` — carrito: vacío

## Comprobaciones finales

- ✔ `orders(count=0)` — pedidos registrados: 0
- ✔ `cart(empty=true)` — carrito: vacío

## Violaciones de restricciones

- Ninguna.

## Estado final de la tienda

- Líneas de carrito pendientes: 0

## Latencia por turno (segundos)

| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total | Audio de respuesta |
|---|---|---|---|---|---|---|---|
| 1 | 0.00 | 0.04 | 7.76 | 0.03 | 0.00 | 7.82 | 0.0 s |
| 2 | 0.00 | 0.00 | 4.83 | 0.02 | 0.00 | 4.85 | 0.0 s |
| **Media de los turnos con LLM (2)** | 0.00 | 0.02 | 6.29 | 0.02 | 0.00 | 6.33 | |

