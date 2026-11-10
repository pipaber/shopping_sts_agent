# 10_atributo_no_verificable — Atributo no verificable

- Veredicto: **correcto**
- Entrada: texto
- Tipo: `atributo_no_verificable`
- Qué se prueba: El usuario pregunta por la valoración de los clientes, un dato que el catálogo no trae. El agente debe decir que no consta, sin inventarlo y sin tocar el carrito. La comprobación mira el texto completo del producto en el catálogo: si no menciona valoraciones, la respuesta tiene que decir que no consta.

## Turno 1 (8.3 s)

**Usuario (texto):** Busco una sartén antiadherente.

- `buscar_productos(consulta="sartén antiadherente")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B08C73K4CV | ilimiti Sartenes Induccion Antiadherentes 20 cm, Sarten Piedra Aluminio Fundido, Libre de PFOA, Apta para Todo Tipo de Cocina | marca: ilimiti | color: desconocido | precio: 83,75 € | existencias: 46 | características (e…

**Agente:** Tengo la sartén ilimiti de 20 cm por 83,75 euros, la ilimiti de 24 cm con tapa por 20,45 euros, la ilimiti de 24 cm sin tapa por 3,82 euros, la Pensofal de 32 cm por 7,48 euros y la Fesha de 24 cm por 10,40 euros. ¿Te interesa alguna?

**Enviado al TTS:** Tengo la sartén ilimiti de veinte centímetros por ochenta y tres euros con setenta y cinco céntimos, la ilimiti de veinticuatro centímetros con tapa por veinte euros con cuarenta y cinco céntimos, la ilimiti de veinticuatro centímetros sin tapa por tres euros con ochenta y dos céntimos, la Pensofal de treinta y dos centímetros por siete euros con cuarenta y ocho céntimos y la Fesha de veinticuatro centímetros por diez euros con cuarenta céntimos. ¿Te interesa alguna?

- ✔ `cart(empty=true)` — carrito: vacío

> `@elegida` = `B08C73K4CV` (candidate:1): ilimiti Sartenes Induccion Antiadherentes 20 cm, Sarten Piedra Aluminio Fundido, Libre de PFOA, Apta para Todo Tipo de Cocina

## Turno 2 (3.1 s)

**Usuario (texto):** ¿Qué valoración le dan los clientes a la primera?

**Agente:** El catálogo no indica valoraciones de clientes para este producto.

**Enviado al TTS:** El catálogo no indica valoraciones de clientes para este producto.

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
| 1 | 0.00 | 0.03 | 8.25 | 0.02 | 0.00 | 8.29 | 0.0 s |
| 2 | 0.00 | 0.00 | 3.04 | 0.03 | 0.00 | 3.07 | 0.0 s |
| **Media de los turnos con LLM (2)** | 0.00 | 0.01 | 5.65 | 0.02 | 0.00 | 5.68 | |

