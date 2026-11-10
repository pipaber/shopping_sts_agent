# 23_candidato_fuera_de_lista — Referencia a un candidato que no está en la lista

- Veredicto: **correcto**
- Entrada: texto
- Tipo: `candidato_fuera_de_lista`
- Qué se prueba: Escenario de reserva, escrito antes de corregir el agente y sin ejecutarlo. La lista tiene cinco candidatos, todos con 20 unidades. El usuario pide el sexto y pregunta por el octavo: el agente no debe añadir nada. Después pide el quinto, que sí existe, y debe añadirse ese y no otro.

## Turno 1 (6.8 s)

**Usuario (texto):** Busco un reloj de pared.

- `buscar_productos(consulta="reloj de pared")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B07PWQFGQR | Amazon Basics - Reloj de pared con números, 30,5 cm, negro | marca: Amazon Basics | color: Negro | precio: 16,59 € | existencias: 19 | características (extracto): Reloj de pared de 30,5 cm con manecillas de operación ana…

**Agente:** Tengo el reloj de pared Amazon Basics por 16,59 euros, el DIYZON por 22,39 euros, el Planetareloj por 29,60 euros, el SOLEDI por 8,14 euros y el DIYZON por 11,64 euros. ¿Te interesa alguno?

**Enviado al TTS:** Tengo el reloj de pared Amazon Basics por dieciséis euros con cincuenta y nueve céntimos, el DIYZON por veintidós euros con treinta y nueve céntimos, el Planetareloj por veintinueve euros con sesenta céntimos, el SOLEDI por ocho euros con catorce céntimos y el DIYZON por once euros con sesenta y cuatro céntimos. ¿Te interesa alguno?

- ✔ `cart(empty=true)` — carrito: vacío

> `@candidato1` = `B07PWQFGQR` (candidate:1): Amazon Basics - Reloj de pared con números, 30,5 cm, negro

> `@candidato2` = `B099D9NWR7` (candidate:2): DIYZON Reloj de Pared Moderno, Reloj de 30 cm Silencioso Entry Lux de Moda, Movimiento de Cuarzo sin Tictac con Batería, Lectura Fácil, Adecuado para Dormitorio, Cocina, Escuela, Oficina

> `@candidato3` = `B00J3TR8UO` (candidate:3): Planetareloj - Reloj de Pared Vintage con Temporizador

> `@candidato4` = `B00ODSSLVK` (candidate:4): SOLEDI Reloj de Pared 3D DIY Reloj de Etiqueta de Pared Decoración Ideal para la Casa Oficina Hotel Restaurante Plata

> `@candidato5` = `B099DBHWHL` (candidate:5): DIYZON Reloj de Pared Minimalista, Reloj silencioso Moderno de 30 cm, Movimiento de Cuarzo sin Tictac con Batería, Fácil de Leer, Adecuado para Dormitorio, Cocina, Escuela, Oficina

> **Suceso externo:** la tienda deja `B07PWQFGQR` (@candidato1) con existencias 20.

> **Suceso externo:** la tienda deja `B099D9NWR7` (@candidato2) con existencias 20.

> **Suceso externo:** la tienda deja `B00J3TR8UO` (@candidato3) con existencias 20.

> **Suceso externo:** la tienda deja `B00ODSSLVK` (@candidato4) con existencias 20.

> **Suceso externo:** la tienda deja `B099DBHWHL` (@candidato5) con existencias 20.

## Turno 2 (3.5 s)

**Usuario (texto):** Ponme el sexto.

- `pedir_aclaracion(pregunta="¿Podrías indicarme cuál es el sexto reloj de pared de la lista que te interesa?")` → OK: pregunta enviada al usuario

**Agente:** ¿Podrías indicarme cuál es el sexto reloj de pared de la lista que te interesa?

**Enviado al TTS:** ¿Podrías indicarme cuál es el sexto reloj de pared de la lista que te interesa?

- ✔ `cart(empty=true)` — carrito: vacío

## Turno 3 (5.2 s)

**Usuario (texto):** ¿Y cuánto cuesta el octavo?

- `detalle_producto(product_id="B00ODSSLVK")` → RECHAZADO: [posicion_inexistente] El usuario se refiere al octavo de la lista y CANDIDATOS solo tiene 5. No elijas otro producto por él: usa pedir_aclaracion para decirle cuántos hay y preguntarle cuál quiere.
- `pedir_aclaracion(pregunta="¿Podrías indicarme cuál reloj de pared de la lista te interesa?")` → OK: pregunta enviada al usuario

**Agente:** ¿Podrías indicarme cuál reloj de pared de la lista te interesa?

**Enviado al TTS:** ¿Podrías indicarme cuál reloj de pared de la lista te interesa?

- ✔ `cart(empty=true)` — carrito: vacío

## Turno 4 (5.1 s)

**Usuario (texto):** Entonces ponme uno del quinto.

- `agregar_al_carrito(product_id="B099DBHWHL", cantidad=1)` → OK: hecho. Así queda el carrito. CARRITO: - id=B099DBHWHL | DIYZON Reloj de Pared Minimalista, Reloj silencioso Moderno de 30 cm… | 1 unidad × 11,64 € = 11,64 € | existencias: 20 Total del carrito: 11,64 €

**Agente:** Hecho, añadido uno del quinto reloj de pared al carrito. En el carrito hay 1 unidad de «DIYZON Reloj de Pared Minimalista, Reloj silencioso Moderno de 30 cm…» a 11,64 € cada una, 11,64 €. Total: 11,64 €.

**Enviado al TTS:** Hecho, añadido uno del quinto reloj de pared al carrito. En el carrito hay una unidad de DIYZON Reloj de Pared Minimalista a once euros con sesenta y cuatro céntimos cada una, once euros con sesenta y cuatro céntimos. Total: once euros con sesenta y cuatro céntimos.

- ✔ `cart(lines=[{"product": "@candidato5", "quantity": 1}])` — carrito: 1 × B099DBHWHL

## Comprobaciones finales

- ✔ `orders(count=0)` — pedidos registrados: 0
- ✔ `cart(lines=[{"product": "@candidato5", "quantity": 1}])` — carrito: 1 × B099DBHWHL

## Violaciones de restricciones

- Ninguna.

## Estado final de la tienda

- Inventario `B00J3TR8UO`: 10 → 20
- Inventario `B00ODSSLVK`: 47 → 20
- Inventario `B07PWQFGQR`: 19 → 20
- Inventario `B099D9NWR7`: 42 → 20
- Inventario `B099DBHWHL`: 19 → 20
- Líneas de carrito pendientes: 1

## Latencia por turno (segundos)

| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total | Audio de respuesta |
|---|---|---|---|---|---|---|---|
| 1 | 0.00 | 0.03 | 6.75 | 0.03 | 0.00 | 6.80 | 0.0 s |
| 2 | 0.00 | 0.00 | 3.47 | 0.03 | 0.00 | 3.50 | 0.0 s |
| 3 | 0.00 | 0.00 | 5.14 | 0.03 | 0.00 | 5.17 | 0.0 s |
| 4 | 0.00 | 0.00 | 5.06 | 0.05 | 0.00 | 5.12 | 0.0 s |
| **Media de los turnos con LLM (4)** | 0.00 | 0.01 | 5.11 | 0.03 | 0.00 | 5.15 | |

