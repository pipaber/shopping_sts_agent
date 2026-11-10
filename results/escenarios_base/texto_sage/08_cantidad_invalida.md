# 08_cantidad_invalida — Cantidad inválida

- Veredicto: **correcto**
- Entrada: texto
- Tipo: `cantidad_invalida`
- Qué se prueba: El usuario pide cero unidades y después una cantidad negativa. Ninguna de las dos debe llegar al carrito.

## Turno 1 (6.6 s)

**Usuario (texto):** Busco un cargador USB C.

- `buscar_productos(consulta="cargador USB C")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B01M3XQ2KL | Samsung EP-LN920CBEGWW, Cargador de coche Dual con Carga rápida y cable USB-C incluído, color negro | marca: SAMSUNG | color: negro | precio: 12,72 € | existencias: 6 | características (extracto): Diseño elegante y creat…

**Agente:** Tengo el cargador USB C de Samsung por 12,72 euros, el de Yosou por 13,65 euros, el de JOOMFEEN en negro por 9,96 euros y otro de JOOMFEEN en plata por 25,13 euros. ¿Te interesa alguno?

**Enviado al TTS:** Tengo el cargador USB C de Samsung por doce euros con setenta y dos céntimos, el de Yosou por trece euros con sesenta y cinco céntimos, el de JOOMFEEN en negro por nueve euros con noventa y seis céntimos y otro de JOOMFEEN en plata por veinticinco euros con trece céntimos. ¿Te interesa alguno?

- ✔ `cart(empty=true)` — carrito: vacío

> `@elegido` = `B01M3XQ2KL` (candidate:1): Samsung EP-LN920CBEGWW, Cargador de coche Dual con Carga rápida y cable USB-C incluído, color negro

> **Suceso externo:** la tienda deja `B01M3XQ2KL` (@elegido) con precio 8,00 € y existencias 20.

## Turno 2 (2.9 s)

**Usuario (texto):** Añade cero unidades del primero.

**Agente:** Entendido, no se añadirán unidades del primero.

**Enviado al TTS:** Entendido, no se añadirán unidades del primero.

- ✔ `cart(empty=true)` — carrito: vacío

## Turno 3 (5.3 s)

**Usuario (texto):** Añade menos dos unidades del primero.

- `cambiar_cantidad(product_id="B01M3XQ2KL", cantidad=1)` → RECHAZADO: [no_esta_en_el_carrito] El producto B01M3XQ2KL no está en el carrito.

**Agente:** Lo siento, el producto que buscas no está en el carrito. ¿Quieres añadirlo directamente?

**Enviado al TTS:** Lo siento, el producto que buscas no está en el carrito. ¿Quieres añadirlo directamente?

- ✔ `cart(empty=true)` — carrito: vacío

## Comprobaciones finales

- ✔ `orders(count=0)` — pedidos registrados: 0
- ✔ `cart(empty=true)` — carrito: vacío
- ✔ `stock(product="@elegido", equals=20)` — existencias de B01M3XQ2KL: 20

## Violaciones de restricciones

- Ninguna.

## Estado final de la tienda

- Inventario `B01M3XQ2KL`: 6 → 20
- Líneas de carrito pendientes: 0

## Latencia por turno (segundos)

| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total | Audio de respuesta |
|---|---|---|---|---|---|---|---|
| 1 | 0.00 | 0.05 | 6.54 | 0.01 | 0.00 | 6.61 | 0.0 s |
| 2 | 0.00 | 0.00 | 2.82 | 0.03 | 0.00 | 2.85 | 0.0 s |
| 3 | 0.00 | 0.00 | 5.30 | 0.03 | 0.00 | 5.33 | 0.0 s |
| **Media de los turnos con LLM (3)** | 0.00 | 0.02 | 4.89 | 0.02 | 0.00 | 4.93 | |

