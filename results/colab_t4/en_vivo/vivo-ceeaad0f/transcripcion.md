# Transcripción de una compra por voz

- Fecha: 2026-11-12T19:53:48
- Nota: conversación en vivo
- LLM: `qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf`; ASR: `large-v3-turbo`; TTS: `XTTS-v2`; embeddings: `intfloat/multilingual-e5-small`
- Voz del agente: clonada de la grabación de referencia `audio/referencia/referencia.wav`, velocidad del habla 1,10
- Carga inicial: catálogo y recuperadores 41.3 s, LLM 19.8 s, ASR 4.0 s, TTS 28.2 s; total 94.5 s
- VRAM del proceso: 9152 MiB con todo cargado, 9430 MiB al terminar la conversación
- Memoria del agente: postgres; hilo `vivo-ceeaad0f`

## Latencia por turno (segundos)

| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total | Audio de respuesta |
|---|---|---|---|---|---|---|---|
| 1 | 1.13 | 0.10 | 15.46 | 0.07 | 13.13 | 29.89 | 23.1 s |
| 2 | 0.39 | 0.00 | 8.64 | 0.06 | 19.09 | 28.17 | 34.3 s |
| **Media de los turnos con LLM (2)** | 0.76 | 0.05 | 12.05 | 0.06 | 16.11 | 29.03 | |

## Turno 1 (29.9 s)

**Usuario (transcripción del ASR):** Busco una botella de agua de acero inoxidable. Mi presupuesto es de 45 euros.

- `fijar_presupuesto(importe_eur=45)` → OK: presupuesto fijado en 45,00 €.
- `buscar_productos(consulta="botella de agua acero inoxidable")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B07VQNY8PK | Newdora Botella de Agua Acero Inoxidable 500ml, Aislamiento de Vacío de Doble Pared, Botellas de Frío/Caliente, con 1 un Cepillo de Limpieza, para Niños, Deporte, Oficina, Gimnasio, Ciclismo, Negro | marca: Newdora | col…

**Agente:** Tengo la botella de agua de Newdora por 6,72 euros, la de KOSAD por 12,37, la de KOUAJ por 18,29 y las de ion8 por 4,97 y 10,79 euros. ¿Te interesa alguna? He anotado un presupuesto de 45,00 €.

**Enviado al TTS:** Tengo la botella de agua de Newdora por seis euros con setenta y dos céntimos, la de KOSAD por doce coma treinta y siete, la de KOUAJ por dieciocho coma veintinueve y las de ion8 por cuatro coma noventa y siete y diez euros con setenta y nueve céntimos. ¿Te interesa alguna? He anotado un presupuesto de cuarenta y cinco euros.

## Turno 2 (28.2 s)

**Usuario (transcripción del ASR):** Añade dos de la primera.

- `agregar_al_carrito(product_id="B07VQNY8PK", cantidad=2)` → OK: hecho. Así queda el carrito. CARRITO: - id=B07VQNY8PK | Newdora Botella de Agua Acero Inoxidable 500ml, Aislamiento de Vacío… | 2 unidades × 6,72 € = 13,44 € | existencias: 46 Total del carrito: 13,44 €

**Agente:** Hecho, añadidas dos unidades. El total del carrito es 13,44 €. En el carrito hay 2 unidades de «Newdora Botella de Agua Acero Inoxidable 500ml, Aislamiento de Vacío…» a 6,72 € cada una, 13,44 €. Total: 13,44 €. Tu presupuesto es de 45,00 € y te quedan 31,56 €.

**Enviado al TTS:** Hecho, añadidas dos unidades. El total del carrito es trece euros con cuarenta y cuatro céntimos. En el carrito hay dos unidades de Newdora Botella de Agua Acero Inoxidable quinientos mililitros a seis euros con setenta y dos céntimos cada una, trece euros con cuarenta y cuatro céntimos. Total: trece euros con cuarenta y cuatro céntimos. Tu presupuesto es de cuarenta y cinco euros y te quedan treinta y un euros con cincuenta y seis céntimos.

## Estado final de la tienda

- Líneas de carrito pendientes: 1
