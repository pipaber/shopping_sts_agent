# 23_candidato_fuera_de_lista — Referencia a un candidato que no está en la lista

- Veredicto: **correcto**
- Entrada: texto
- Tipo: `candidato_fuera_de_lista`
- Qué se prueba: Escenario de reserva, escrito antes de corregir el agente y sin ejecutarlo. La lista tiene cinco candidatos, todos con 20 unidades. El usuario pide el sexto y pregunta por el octavo: el agente no debe añadir nada. Después pide el quinto, que sí existe, y debe añadirse ese y no otro.

## Turno 1 (6.3 s)

**Usuario (texto):** Busco un reloj de pared.

- `buscar_productos(consulta="reloj de pared")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B07PWQFGQR | Amazon Basics - Reloj de pared con números, 30,5 cm, negro | marca: Amazon Basics | color: Negro | precio: 16,59 € | existencias: 19 | características (extracto): Reloj de pared de 30,5 cm con manecillas de operación ana…

**Agente:** Tengo el Amazon Basics por 16,59 euros, el Planetareloj por 29,60, el DIYZON por 22,39, el Rolex Daytona por 31,59 y el FreeLeben por 27,42. ¿Te interesa alguno?

**Enviado al TTS:** Tengo el Amazon Basics por dieciséis euros con cincuenta y nueve céntimos, el Planetareloj por veintinueve coma sesenta, el DIYZON por veintidós coma treinta y nueve, el Rolex Daytona por treinta y uno coma cincuenta y nueve y el FreeLeben por veintisiete coma cuarenta y dos. ¿Te interesa alguno?

- ✔ `cart(empty=true)` — carrito: vacío

> `@candidato1` = `B07PWQFGQR` (candidate:1): Amazon Basics - Reloj de pared con números, 30,5 cm, negro

> `@candidato2` = `B00J3TR8UO` (candidate:2): Planetareloj - Reloj de Pared Vintage con Temporizador

> `@candidato3` = `B099D9NWR7` (candidate:3): DIYZON Reloj de Pared Moderno, Reloj de 30 cm Silencioso Entry Lux de Moda, Movimiento de Cuarzo sin Tictac con Batería, Lectura Fácil, Adecuado para Dormitorio, Cocina, Escuela, Oficina

> `@candidato4` = `B01065J29I` (candidate:4): Reloj de pared Rolex Daytona

> `@candidato5` = `B089NMG3TR` (candidate:5): FreeLeben Reloj De Pared De Doble Cara Reloj De Pie Retro Reloj De Pared De La Estación De Paddington Soporte Vintage De Aspecto Antiguo Reloj De Decoración Colgante, 12.12 * 7.5cm

> **Suceso externo:** la tienda deja `B07PWQFGQR` (@candidato1) con existencias 20.

> **Suceso externo:** la tienda deja `B00J3TR8UO` (@candidato2) con existencias 20.

> **Suceso externo:** la tienda deja `B099D9NWR7` (@candidato3) con existencias 20.

> **Suceso externo:** la tienda deja `B01065J29I` (@candidato4) con existencias 20.

> **Suceso externo:** la tienda deja `B089NMG3TR` (@candidato5) con existencias 20.

## Turno 2 (3.2 s)

**Usuario (texto):** Ponme el sexto.

- `pedir_aclaracion(pregunta="¿Podrías indicarme cuál es el sexto reloj de la lista que te interesa?")` → OK: pregunta enviada al usuario

**Agente:** ¿Podrías indicarme cuál es el sexto reloj de la lista que te interesa?

**Enviado al TTS:** ¿Podrías indicarme cuál es el sexto reloj de la lista que te interesa?

- ✔ `cart(empty=true)` — carrito: vacío

## Turno 3 (4.8 s)

**Usuario (texto):** ¿Y cuánto cuesta el octavo?

- `detalle_producto(product_id="B089NMG3TR")` → RECHAZADO: [posicion_inexistente] El usuario se refiere al octavo de la lista y CANDIDATOS solo tiene 5. No elijas otro producto por él: usa pedir_aclaracion para decirle cuántos hay y preguntarle cuál quiere.
- `pedir_aclaracion(pregunta="¿Podrías indicarme cuál de estos relojes de pared te interesa?")` → OK: pregunta enviada al usuario

**Agente:** ¿Podrías indicarme cuál de estos relojes de pared te interesa?

**Enviado al TTS:** ¿Podrías indicarme cuál de estos relojes de pared te interesa?

- ✔ `cart(empty=true)` — carrito: vacío

## Turno 4 (5.0 s)

**Usuario (texto):** Entonces ponme uno del quinto.

- `agregar_al_carrito(product_id="B089NMG3TR", cantidad=1)` → OK: hecho. Así queda el carrito. CARRITO: - id=B089NMG3TR | FreeLeben Reloj De Pared De Doble Cara Reloj De Pie Retro Reloj De… | 1 unidad × 27,42 € = 27,42 € | existencias: 20 Total del carrito: 27,42 €

**Agente:** Hecho, añadido uno del FreeLeben al carrito. En el carrito hay 1 unidad de «FreeLeben Reloj De Pared De Doble Cara Reloj De Pie Retro Reloj De…» a 27,42 € cada una, 27,42 €. Total: 27,42 €.

**Enviado al TTS:** Hecho, añadido uno del FreeLeben al carrito. En el carrito hay una unidad de FreeLeben Reloj De Pared De Doble Cara a veintisiete euros con cuarenta y dos céntimos cada una, veintisiete euros con cuarenta y dos céntimos. Total: veintisiete euros con cuarenta y dos céntimos.

- ✔ `cart(lines=[{"product": "@candidato5", "quantity": 1}])` — carrito: 1 × B089NMG3TR

## Comprobaciones finales

- ✔ `orders(count=0)` — pedidos registrados: 0
- ✔ `cart(lines=[{"product": "@candidato5", "quantity": 1}])` — carrito: 1 × B089NMG3TR

## Violaciones de restricciones

- Ninguna.

## Estado final de la tienda

- Inventario `B00J3TR8UO`: 10 → 20
- Inventario `B01065J29I`: 1 → 20
- Inventario `B07PWQFGQR`: 19 → 20
- Inventario `B089NMG3TR`: 10 → 20
- Inventario `B099D9NWR7`: 42 → 20
- Líneas de carrito pendientes: 1

## Latencia por turno (segundos)

| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total | Audio de respuesta |
|---|---|---|---|---|---|---|---|
| 1 | 0.00 | 0.04 | 6.24 | 0.03 | 0.00 | 6.30 | 0.0 s |
| 2 | 0.00 | 0.00 | 3.23 | 0.01 | 0.00 | 3.25 | 0.0 s |
| 3 | 0.00 | 0.00 | 4.81 | 0.03 | 0.00 | 4.83 | 0.0 s |
| 4 | 0.00 | 0.00 | 4.90 | 0.05 | 0.00 | 4.95 | 0.0 s |
| **Media de los turnos con LLM (4)** | 0.00 | 0.01 | 4.79 | 0.03 | 0.00 | 4.83 | |

