# 24_dato_que_no_consta — Dato que el catálogo no trae

- Veredicto: **correcto**
- Entrada: texto
- Tipo: `dato_que_no_consta`
- Qué se prueba: Escenario de reserva, escrito antes de corregir el agente y sin ejecutarlo. El usuario pregunta por la garantía del segundo candidato y por el plazo de entrega del primero. La comprobación mira el texto completo de cada producto en el catálogo: si no menciona el dato, la respuesta tiene que decir que no consta; si lo menciona, no puede decir que no consta. El carrito no debe cambiar.

## Turno 1 (7.1 s)

**Usuario (texto):** Busco una silla de oficina.

- `buscar_productos(consulta="silla de oficina")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B07SFFT627 | Silla de Oficina, Silla Ergonómica con reposacabezas y reposapiés Respaldo ergonomico,una Mejor protección de la Columna para Personas sedentarias, Carga máx. 130kg,Gray | marca: CC Chair | color: Gray | precio: 17,37 € …

**Agente:** Tengo la silla de oficina Gray de CC Chair por 17,37 euros, la de Cashoffice por 13,30 euros, la de mfavour en Negro por 10,95 euros, la de mfavour en Blanca por 13,19 euros y la de Deuba por 68,19 euros. ¿Te interesa alguna?

**Enviado al TTS:** Tengo la silla de oficina Gray de CC Chair por diecisiete euros con treinta y siete céntimos, la de Cashoffice por trece euros con treinta céntimos, la de mfavour en Negro por diez euros con noventa y cinco céntimos, la de mfavour en Blanca por trece euros con diecinueve céntimos y la de Deuba por sesenta y ocho euros con diecinueve céntimos. ¿Te interesa alguna?

- ✔ `cart(empty=true)` — carrito: vacío

> `@primera` = `B07SFFT627` (candidate:1): Silla de Oficina, Silla Ergonómica con reposacabezas y reposapiés Respaldo ergonomico,una Mejor protección de la Columna para Personas sedentarias, Carga máx. 130kg,Gray

> `@segunda` = `B0777SG7GP` (candidate:2): CashOffice - Silla de Escritorio Ergonómica, Silla de Oficina Giratoria con Respaldo Transpirable (Negro)

## Turno 2 (5.2 s)

**Usuario (texto):** ¿Cuántos años de garantía tiene la segunda?

- `detalle_producto(product_id="B0777SG7GP")` → OK: [1] id=B0777SG7GP | CashOffice - Silla de Escritorio Ergonómica, Silla de Oficina Giratoria con Respaldo Transpirable (Negro) | marca: Cashoffice | color: Black | precio: 13,30 € | existencias: 27 | características (extracto): Silla ergonómica con asiento firme y respaldo fabricado en malla transpir…

**Agente:** El catálogo no indica cuántos años de garantía tiene esta silla.

**Enviado al TTS:** El catálogo no indica cuántos años de garantía tiene esta silla.

- ✔ `declares_unknown(product="@segunda", keywords=["garant"])` — dato en el catálogo: no; la respuesta dice que no consta: sí
- ✔ `cart(empty=true)` — carrito: vacío

## Turno 3 (5.1 s)

**Usuario (texto):** ¿Y en cuántos días llega la primera?

- `consultar_precio_stock(product_id="B07SFFT627")` → OK: precio 17,37 €; quedan 25 unidades. Esta herramienta no da características: para color, batería, medidas u otros datos del producto usa detalle_producto.

**Agente:** El catálogo no indica cuántos días tarda en llegar, pero sí que quedan 25 unidades.

**Enviado al TTS:** El catálogo no indica cuántos días tarda en llegar, pero sí que quedan veinticinco unidades.

- ✔ `declares_unknown(product="@primera", keywords=["entrega", "envío", "envio", "llega en", "días laborables", "24 horas", "48 horas"])` — dato en el catálogo: no; la respuesta dice que no consta: sí
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
| 1 | 0.00 | 0.04 | 7.06 | 0.03 | 0.00 | 7.13 | 0.0 s |
| 2 | 0.00 | 0.00 | 5.13 | 0.03 | 0.00 | 5.16 | 0.0 s |
| 3 | 0.00 | 0.00 | 5.04 | 0.03 | 0.00 | 5.07 | 0.0 s |
| **Media de los turnos con LLM (3)** | 0.00 | 0.01 | 5.74 | 0.03 | 0.00 | 5.78 | |

