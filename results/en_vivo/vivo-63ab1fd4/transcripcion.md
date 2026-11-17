# Transcripción de una compra por voz

- Fecha: 2026-11-17T15:16:29
- Nota: conversación en vivo
- LLM: `qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf`; ASR: `large-v3-turbo`; TTS: `F5-Spanish`; embeddings: `intfloat/multilingual-e5-small`
- Voz del agente: clonada de los turnos grabados `audio/escenarios/01_compra_confirmada/01.wav`, `audio/escenarios/03_cambio_cantidad/01.wav`, velocidad del habla 0,90
- Carga inicial: catálogo y recuperadores 20.0 s, LLM 0.7 s, ASR 0.8 s, TTS 5.8 s; total 27.7 s
- VRAM del proceso: 8522 MiB con todo cargado, 8798 MiB al terminar la conversación
- Memoria del agente: postgres; hilo `vivo-63ab1fd4`

## Latencia por turno (segundos)

| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total | Audio de respuesta |
|---|---|---|---|---|---|---|---|
| 1 | 0.47 | 0.03 | 9.49 | 0.04 | 10.54 | 20.57 | 25.7 s |
| 2 | 0.33 | 0.00 | 4.88 | 0.05 | 17.93 | 23.20 | 35.9 s |
| 3 | 0.00 | 0.00 | 3.00 | 0.03 | 2.96 | 5.98 | 5.1 s |
| **Media de los turnos con LLM (3)** | 0.27 | 0.01 | 5.79 | 0.04 | 10.48 | 16.59 | |

## Turno 1 (20.6 s)

**Usuario (transcripción del ASR):** Busco una botella de agua de acero inoxidable. Mi presupuesto es de 45 euros.

- `fijar_presupuesto(importe_eur=45)` → OK: presupuesto fijado en 45,00 €.
- `buscar_productos(consulta="botella de agua acero inoxidable")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B07VQNY8PK | Newdora Botella de Agua Acero Inoxidable 500ml, Aislamiento de Vacío de Doble Pared, Botellas de Frío/Caliente, con 1 un Cepillo de Limpieza, para Niños, Deporte, Oficina, Gimnasio, Ciclismo, Negro | marca: Newdora | col…

**Agente:** Tengo la botella de agua de Newdora por 6,72 euros, la de KOSAD por 12,37, la de KOUAJ por 18,29 y las de ion8 por 4,97 y 10,79 euros. ¿Te interesa alguna? He anotado un presupuesto de 45,00 €.

**Enviado al TTS:** Tengo la botella de agua de Newdora por seis euros con setenta y dos céntimos, la de KOSAD por doce coma treinta y siete, la de KOUAJ por dieciocho coma veintinueve y las de ion8 por cuatro coma noventa y siete y diez euros con setenta y nueve céntimos. ¿Te interesa alguna? He anotado un presupuesto de cuarenta y cinco euros.

## Turno 2 (23.2 s)

**Usuario (transcripción del ASR):** Añade dos de la primera.

- `agregar_al_carrito(product_id="B07VQNY8PK", cantidad=2)` → OK: hecho. Así queda el carrito. CARRITO: - id=B07VQNY8PK | Newdora Botella de Agua Acero Inoxidable 500ml, Aislamiento de Vacío… | 2 unidades × 6,72 € = 13,44 € | existencias: 46 Total del carrito: 13,44 €

**Agente:** Hecho, añadidas dos unidades. El total es 13,44 €. En el carrito hay 2 unidades de «Newdora Botella de Agua Acero Inoxidable 500ml, Aislamiento de Vacío…» a 6,72 € cada una, 13,44 €. Total: 13,44 €. Tu presupuesto es de 45,00 € y te quedan 31,56 €.

**Enviado al TTS:** Hecho, añadidas dos unidades. El total es trece euros con cuarenta y cuatro céntimos. En el carrito hay dos unidades de Newdora Botella de Agua Acero Inoxidable quinientos mililitros a seis euros con setenta y dos céntimos cada una, trece euros con cuarenta y cuatro céntimos. Total: trece euros con cuarenta y cuatro céntimos. Tu presupuesto es de cuarenta y cinco euros y te quedan treinta y un euros con cincuenta y seis céntimos.

## Turno 3 (6.0 s)

**Usuario (texto):** ¿Cuánto llevo gastado?

**Agente:** Hasta ahora has gastado 13,44 €.

**Enviado al TTS:** Hasta ahora has gastado trece euros con cuarenta y cuatro céntimos.

## Estado final de la tienda

- Líneas de carrito pendientes: 1
