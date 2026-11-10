# 23_candidato_fuera_de_lista — Referencia a un candidato que no está en la lista

- Veredicto: **correcto**
- Entrada: texto
- Tipo: `candidato_fuera_de_lista`
- Qué se prueba: Escenario de reserva, escrito antes de corregir el agente y sin ejecutarlo. La lista tiene cinco candidatos, todos con 20 unidades. El usuario pide el sexto y pregunta por el octavo: el agente no debe añadir nada. Después pide el quinto, que sí existe, y debe añadirse ese y no otro.

## Turno 1 (7.3 s)

**Usuario (texto):** Busco un reloj de pared.

- `buscar_productos(consulta="reloj de pared")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B099D9NWR7 | DIYZON Reloj de Pared Moderno, Reloj de 30 cm Silencioso Entry Lux de Moda, Movimiento de Cuarzo sin Tictac con Batería, Lectura Fácil, Adecuado para Dormitorio, Cocina, Escuela, Oficina | marca: DIYZON | color: Blanco |…

**Agente:** Tengo estos relojes de pared: uno de DIYZON por 22,39 €, uno de Youery por 57,13 €, uno de SOLEDI por 18,35 €, otro de DIYZON por 11,64 € y uno de FreeLeben por 27,42 €. ¿Te interesa alguno?

**Enviado al TTS:** Tengo estos relojes de pared: uno de DIYZON por veintidós euros con treinta y nueve céntimos, uno de Youery por cincuenta y siete euros con trece céntimos, uno de SOLEDI por dieciocho euros con treinta y cinco céntimos, otro de DIYZON por once euros con sesenta y cuatro céntimos y uno de FreeLeben por veintisiete euros con cuarenta y dos céntimos. ¿Te interesa alguno?

- ✔ `cart(empty=true)` — carrito: vacío

> `@candidato1` = `B099D9NWR7` (candidate:1): DIYZON Reloj de Pared Moderno, Reloj de 30 cm Silencioso Entry Lux de Moda, Movimiento de Cuarzo sin Tictac con Batería, Lectura Fácil, Adecuado para Dormitorio, Cocina, Escuela, Oficina

> `@candidato2` = `B08MT7PX3C` (candidate:2): Youery Reloj de Pared 3D,Relojes Modernos DIY,Reloj de Pared Adhesivo Reloj de Etiqueta de Pared Decoración,llenado Pared Vacía 3D Reloj,Ideal para Oficina Hotel Restaurante(Negro)

> `@candidato3` = `B01AXRGQNE` (candidate:3): Reloj de pared vintage multicolor francés, reloj moderno hecho de madera estilo toscano para decoración del hogar

> `@candidato4` = `B099DBHWHL` (candidate:4): DIYZON Reloj de Pared Minimalista, Reloj silencioso Moderno de 30 cm, Movimiento de Cuarzo sin Tictac con Batería, Fácil de Leer, Adecuado para Dormitorio, Cocina, Escuela, Oficina

> `@candidato5` = `B089NMG3TR` (candidate:5): FreeLeben Reloj De Pared De Doble Cara Reloj De Pie Retro Reloj De Pared De La Estación De Paddington Soporte Vintage De Aspecto Antiguo Reloj De Decoración Colgante, 12.12 * 7.5cm

> **Suceso externo:** la tienda deja `B099D9NWR7` (@candidato1) con existencias 20.

> **Suceso externo:** la tienda deja `B08MT7PX3C` (@candidato2) con existencias 20.

> **Suceso externo:** la tienda deja `B01AXRGQNE` (@candidato3) con existencias 20.

> **Suceso externo:** la tienda deja `B099DBHWHL` (@candidato4) con existencias 20.

> **Suceso externo:** la tienda deja `B089NMG3TR` (@candidato5) con existencias 20.

## Turno 2 (3.9 s)

**Usuario (texto):** Ponme el sexto.

**Agente:** Lo siento, no hay un sexto producto en la lista. ¿Podrías indicarme uno de los cinco que veo?

**Enviado al TTS:** Lo siento, no hay un sexto producto en la lista. ¿Podrías indicarme uno de los cinco que veo?

- ✔ `cart(empty=true)` — carrito: vacío

## Turno 3 (3.2 s)

**Usuario (texto):** ¿Y cuánto cuesta el octavo?

- `pedir_aclaracion(pregunta="¿Podrías indicarme el número del producto que te interesa?")` → OK: pregunta enviada al usuario

**Agente:** ¿Podrías indicarme el número del producto que te interesa?

**Enviado al TTS:** ¿Podrías indicarme el número del producto que te interesa?

- ✔ `cart(empty=true)` — carrito: vacío

## Turno 4 (5.7 s)

**Usuario (texto):** Entonces ponme uno del quinto.

- `agregar_al_carrito(product_id="B089NMG3TR", cantidad=1)` → OK: hecho. Así queda el carrito. CARRITO: - id=B089NMG3TR | FreeLeben Reloj De Pared De Doble Cara Reloj De Pie Retro Reloj De… | 1 unidad × 27,42 € = 27,42 € | existencias: 20 Total del carrito: 27,42 €

**Agente:** Hecho, añadido uno del quinto candidato. El total del carrito es 27,42 €. En el carrito hay 1 unidad de «FreeLeben Reloj De Pared De Doble Cara Reloj De Pie Retro Reloj De…» a 27,42 € cada una, 27,42 €. Total: 27,42 €.

**Enviado al TTS:** Hecho, añadido uno del quinto candidato. El total del carrito es veintisiete euros con cuarenta y dos céntimos. En el carrito hay una unidad de FreeLeben Reloj De Pared De Doble Cara a veintisiete euros con cuarenta y dos céntimos cada una, veintisiete euros con cuarenta y dos céntimos. Total: veintisiete euros con cuarenta y dos céntimos.

- ✔ `cart(lines=[{"product": "@candidato5", "quantity": 1}])` — carrito: 1 × B089NMG3TR

## Comprobaciones finales

- ✔ `orders(count=0)` — pedidos registrados: 0
- ✔ `cart(lines=[{"product": "@candidato5", "quantity": 1}])` — carrito: 1 × B089NMG3TR

## Violaciones de restricciones

- Ninguna.

## Estado final de la tienda

- Inventario `B01AXRGQNE`: 45 → 20
- Inventario `B089NMG3TR`: 10 → 20
- Inventario `B08MT7PX3C`: 46 → 20
- Inventario `B099D9NWR7`: 42 → 20
- Inventario `B099DBHWHL`: 19 → 20
- Líneas de carrito pendientes: 1

## Latencia por turno (segundos)

| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total | Audio de respuesta |
|---|---|---|---|---|---|---|---|
| 1 | 0.00 | 0.03 | 7.25 | 0.03 | 0.00 | 7.30 | 0.0 s |
| 2 | 0.00 | 0.00 | 3.85 | 0.03 | 0.00 | 3.88 | 0.0 s |
| 3 | 0.00 | 0.00 | 3.19 | 0.01 | 0.00 | 3.21 | 0.0 s |
| 4 | 0.00 | 0.00 | 5.61 | 0.06 | 0.00 | 5.67 | 0.0 s |
| **Media de los turnos con LLM (4)** | 0.00 | 0.01 | 4.97 | 0.03 | 0.00 | 5.01 | |

