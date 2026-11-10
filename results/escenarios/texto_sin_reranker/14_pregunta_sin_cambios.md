# 14_pregunta_sin_cambios — Una pregunta no cambia el carrito

- Veredicto: **correcto**
- Entrada: texto
- Tipo: `pregunta_sin_cambios`
- Qué se prueba: El usuario pregunta por disponibilidad y por precio sin pedir nada. El carrito debe seguir vacío y la respuesta sobre el precio debe dar el de la tienda.

## Turno 1 (6.0 s)

**Usuario (texto):** Busco una funda para móvil.

- `buscar_productos(consulta="funda móvil")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B091HXTM73 | KEELYY Funda Impermeable Móvil IPX8 Universal 4 Unidades, Bolsa para Móvil Estanca a Prueba de Agua para iPhone 12 11 XR X 8 7 Galaxy Note 20 S20 Xiaomi Huawei Mate40 Pro hasta 6.7'' | marca: KEELYY | color: 4Colors | pr…

**Agente:** Tengo la funda KEELYY por 18,23 euros, la Cocoda por 21,73, la MOBESV por 17,62 y la kwmobile por 81,81. ¿Te interesa alguna?

**Enviado al TTS:** Tengo la funda KEELYY por dieciocho euros con veintitrés céntimos, la Cocoda por veintiuno coma setenta y tres, la MOBESV por diecisiete coma sesenta y dos y la kwmobile por ochenta y uno coma ochenta y uno. ¿Te interesa alguna?

- ✔ `cart(empty=true)` — carrito: vacío

> `@primera` = `B091HXTM73` (candidate:1): KEELYY Funda Impermeable Móvil IPX8 Universal 4 Unidades, Bolsa para Móvil Estanca a Prueba de Agua para iPhone 12 11 XR X 8 7 Galaxy Note 20 S20 Xiaomi Huawei Mate40 Pro hasta 6.7''

## Turno 2 (4.6 s)

**Usuario (texto):** ¿La segunda está disponible?

- `consultar_precio_stock(product_id="B098NQLJKX")` → OK: precio 21,73 €; quedan 10 unidades. Esta herramienta no da características: para color, batería, medidas u otros datos del producto usa detalle_producto.

**Agente:** Sí, la funda Cocoda está disponible. Quedan 10 unidades.

**Enviado al TTS:** Sí, la funda Cocoda está disponible. Quedan diez unidades.

- ✔ `cart(empty=true)` — carrito: vacío

## Turno 3 (3.2 s)

**Usuario (texto):** ¿Cuánto cuesta la primera?

**Agente:** La funda KEELYY cuesta 18,23 euros.

**Enviado al TTS:** La funda KEELYY cuesta dieciocho euros con veintitrés céntimos.

- ✔ `cart(empty=true)` — carrito: vacío
- ✔ `mentions_price(product="@primera")` — precio en la tienda: 18.23 €

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
| 1 | 0.00 | 0.03 | 5.94 | 0.03 | 0.00 | 6.00 | 0.0 s |
| 2 | 0.00 | 0.00 | 4.61 | 0.03 | 0.00 | 4.64 | 0.0 s |
| 3 | 0.00 | 0.00 | 3.21 | 0.03 | 0.00 | 3.24 | 0.0 s |
| **Media de los turnos con LLM (3)** | 0.00 | 0.01 | 4.59 | 0.03 | 0.00 | 4.63 | |

