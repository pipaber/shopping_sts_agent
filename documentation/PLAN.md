# Plan de trabajo — Laboratorio 4: asistente de compras por voz

Plan para una persona, unas 2 semanas (inicio 9 de noviembre de 2026). Elaborado con asistencia de IA generativa; validar las decisiones técnicas con el docente o el grupo antes de darlas por cerradas.

## 1. Restricciones del enunciado que condicionan el diseño

| Restricción | Consecuencia |
|---|---|
| Todo el procesamiento en Google Colab, sin APIs externas de inferencia | LLM, ASR, TTS y embeddings locales. La guía de voz de LangGraph (AssemblyAI + Cartesia) solo sirve como patrón STT → agente → TTS |
| Interacción por turnos, sin tiempo real | No hace falta streaming ni WebSockets; se graba, se procesa y se reproduce en el notebook |
| "Sustentar las recomendaciones con información recuperada" | Cada afirmación sobre un producto debe salir del texto recuperado; lo que no aparece se declara "desconocido". No pide atención ni explicabilidad del modelo |
| Etiquetas ESCI no consultables por el agente | Solo se usan para entrenar con `train` y para medir con `test` |
| Validación de cantidades, presupuesto y stock por código | El LLM propone, el código decide. Confirmación atómica e idempotente |
| Control, memoria, herramientas y validaciones propias | Grafo explícito de LangGraph, sin agente preconstruido |
| No ajustar con consultas de evaluación | Hiperparámetros y prompts se fijan con `train`; `test` se corre una vez al final |

## 2. Decisiones tomadas

| Componente | Elección | Motivo |
|---|---|---|
| GPU | Colab T4 gratis (16 GB) | Caso base; el tamaño del LLM queda configurable |
| ASR | Whisper large-v3-turbo con `faster-whisper` 1.2 (float16 en GPU, int8 en CPU), español fijo y filtro de voz | Buen español y rápido; 2,2 GB de VRAM medidos. Sin el filtro de voz transcribe el silencio como frases inventadas |
| LLM | Qwen2.5-7B-Instruct en GGUF Q4_K_M (`Qwen/Qwen2.5-7B-Instruct-GGUF`, 4,68 GB) con `llama-cpp-python` | 5,2 GB de VRAM medidos con contexto de 8 192 tokens; el esquema JSON de la decisión se convierte en gramática y fuerza llamadas a herramientas válidas. Configurable con `SHOPPING_AGENT_LLM_*` |
| TTS | XTTS-v2 (`coqui-tts` 0.28) con grabación de referencia propia | Español nativo, clona con ~10 s; 2,0 GB de VRAM al cargar y 2,8 GB tras sintetizar (medidos). Se usa bajo la licencia CPML de Coqui, que solo permite uso no comercial (este trabajo es académico); cada persona que lo ejecuta la acepta de forma explícita en su `.env` |
| Recuperación | BM25 + embeddings densos multilingües (fusión RRF) → reranker GraphSAGE | El GNN es el componente de la ablación |
| Memoria del agente | Postgres: `PostgresSaver` (checkpoints) y `PostgresStore` (memoria entre conversaciones, con pgvector si hace falta búsqueda semántica) | Decisión del autor; un solo motor para la memoria de corto y largo plazo |
| Tienda simulada | SQLite (precios, stock, carritos, pedidos) | Restaurar el estado inicial es copiar un archivo |
| Vectores del catálogo | FAISS | Índice en memoria, suficiente a esta escala |
| Agente | Grafo explícito en LangGraph con `interrupt` para confirmar | Control propio y defendible |

Descartados: Memorilla (es memoria comprimida para LLM, no un GNN, y su inferencia pide una GPU de 80 GB); LightGCN puro (transductivo: las consultas de test no tienen embedding); DuckDB (con 5 000 productos la velocidad no importa y la tienda necesita transacciones tipo OLTP).

Postgres en Colab: se instala con `apt` y se arranca en una celda de preparación al inicio de cada sesión. Ese tiempo cuenta como carga inicial, no como latencia por turno. La receta se comprobó en un contenedor Ubuntu 22.04 como root (la misma base que Colab; instala PostgreSQL 14) y falta ejecutarla en Colab el día 7:

```bash
apt-get -qq update && apt-get -qq install -y postgresql
service postgresql start
sudo -u postgres psql -c "CREATE USER shopping_agent WITH PASSWORD 'colab'"
sudo -u postgres createdb -O shopping_agent shopping_agent
# SHOPPING_AGENT_PG_URL=postgresql://shopping_agent:colab@localhost:5432/shopping_agent
```

pgvector no hace falta por ahora: el Store solo guarda las preferencias del usuario por clave, sin búsqueda semántica. En local se usa un contenedor `postgres:16-alpine` (ver README). Postgres es obligatorio: sin `SHOPPING_AGENT_PG_URL` los comandos se detienen con un error, para no perder la persistencia sin notarlo (por ejemplo en Colab). La memoria volátil solo se usa si se pide de forma explícita (`--volatile-memory` u `open_memory(volatile=True)`) y queda anotada en la transcripción.

`llama-cpp-python` en Colab: hay que instalarlo con CUDA (`CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python`). En la workstation la compilación tardó unos 20 minutos; en Colab conviene medirlo el día 7 y, si es demasiado, usar una rueda precompilada para la versión de CUDA de la sesión.

VRAM con todo cargado en un solo proceso (medida en la workstation, sin el reranker, que añade 0,1 GB con el control y 0,23 GB con GraphSAGE): 9,6 GB con el LLM, los embeddings, Whisper y XTTS-v2 cargados, y 10,4 GB al terminar una conversación de ocho turnos; cabe en los 15 GB utilizables de la T4. Por separado: LLM 5,2 GB, embeddings 0,6 GB, Whisper 2,2 GB y XTTS-v2 2,0 GB (cada medida suelta incluye el contexto de CUDA, que en un proceso se comparte). Si en Colab no cupiera, los embeddings de consulta pasan a CPU.

## 3. Arquitectura

```
audio → ASR (Whisper) → texto
      → Grafo LangGraph (estado + PostgresSaver / PostgresStore)
           entender_turno → ¿falta info / ambigüedad? → aclarar
                          → recuperar (BM25 + denso → GraphSAGE)
                          → actuar (tools sobre SQLite)
                          → validar (código) → cotizar
                          → interrupt: confirmar → registrar_pedido (transacción)
      → texto de respuesta → TTS (XTTS-v2) → audio
```

El grafo implementado (`src/shopping_agent/agent/graph.py`) tiene estos nodos: `iniciar_turno`, `interpretar` (única llamada al LLM: una herramienta por paso), `recuperar`, `validar`, `ejecutar_herramienta`, `validar_respuesta`, `pedir_aclaracion`, `cotizar`, `confirmar` (`interrupt`), `registrar_pedido`, `proponer_alternativa` y `responder`.

**Estado de la conversación:** presupuesto, preferencias, carrito (producto, cantidad), candidatos recuperados con su evidencia, aclaración pendiente, última cotización (`quote_id`, total, instantánea de stock), pedido confirmado, historial resumido.

**Herramientas que puede proponer el LLM:** `buscar_productos`, `detalle_producto`, `comparar`, `consultar_precio_stock`, `agregar_al_carrito`, `cambiar_cantidad`, `quitar_del_carrito`, `fijar_presupuesto`, `guardar_preferencia`, `cotizar`, `pedir_aclaracion` y `responder`. `confirmar_pedido` no es una herramienta del LLM: solo la ejecuta el código cuando el usuario contesta que sí a la cotización.

**Confirmación:** una transacción `BEGIN IMMEDIATE` que vuelve a comprobar stock y presupuesto, inserta el pedido con `UNIQUE(quote_id)` y descuenta inventario. Si algo falla hay rollback completo y el agente propone una alternativa. Repetir la confirmación devuelve el pedido existente.

**Corrección de transcripción:** antes de cotizar, el agente repite cantidades, importes y productos entendidos; el usuario puede corregir antes de que se ejecute nada.

### Decisiones de diseño del agente (días 5–6)

Comportamientos que el plan no fijaba; en cada caso se eligió la opción más simple:

- **Una decisión por llamada al LLM.** La salida es un objeto JSON (`motivo`, `herramienta`, argumentos) restringido por gramática. Los `product_id` posibles se limitan a los candidatos y al carrito, así que el modelo no puede nombrar un producto inexistente. Máximo 6 decisiones por turno; si se agotan, el turno acaba con una respuesta de respaldo.
- **Carrito por conversación.** El `cart_id` es el `thread_id`. El carrito vive en SQLite y el estado del grafo se sincroniza con la tienda al empezar cada turno.
- **Presupuesto por compra, preferencias por usuario.** El presupuesto queda en el estado de la conversación; las preferencias se guardan además en el Store (`usuarios/<user_id>`) y se recuperan al abrir otra conversación.
- **Orden de los candidatos.** La búsqueda es el híbrido BM25 + denso con RRF (top 50), que desde los días 8–9 reordena un reranker entrenado: por defecto el control sin grafo, y GraphSAGE o ninguno según `SHOPPING_AGENT_RERANKER` (`sage`, `off`). De los 20 primeros se muestran antes los que se pueden comprar (con existencias y dentro de lo que queda de presupuesto) y se enseñan 5 con sus campos del catálogo; los ausentes se muestran como "desconocido".
- **Respuestas.** El texto lo redacta el LLM, pero el contenido del carrito, la cotización, el pedido y las alternativas por falta de stock los escribe el código. Cuando el carrito o el presupuesto cambian, el código añade a la respuesta el carrito exacto y lo que queda de presupuesto.
- **Validación de la respuesta.** Antes de enviarla, el código comprueba que toda cifra del texto del LLM aparece en los datos que tuvo delante y que no da por hecho un pedido inexistente; si falla, la respuesta vuelve al LLM con el motivo. Es una comprobación global: no detecta una cifra real atribuida al producto equivocado.
- **Confirmación.** Solo cuenta como sí una respuesta que no dice nada más ("sí", "vale, confirmo"). "No" cancela sin tocar el carrito. Cualquier otra cosa ("sí, pero que sean tres") no compra y se atiende como un turno nuevo; cualquier cambio en el carrito o el presupuesto invalida la cotización.
- **Confirmación repetida.** Un "sí" justo después de registrar el pedido vuelve a confirmar la misma cotización, que es idempotente, y el agente contesta que ya estaba registrado.
- **Cambios entre cotización y confirmación.** La transacción rechaza el pedido si cambió el stock, el precio o el carrito. Con stock insuficiente el agente ofrece la cantidad disponible y hasta tres productos parecidos con existencias suficientes y dentro del presupuesto; el carrito no se modifica hasta que el usuario decide.
- **Historial.** No se resume con el LLM: se envían los 8 últimos mensajes.

Mediciones en la workstation (RTX A2000 12 GB) con las transcripciones de `results/chat_*.json`: 2,5–9,5 s por turno (media 5–6 s; cada turno son de 1 a 3 decisiones de unos 2,7 s), 1 185 tokens/s al evaluar el prompt y 50 tokens/s al generar. La confirmación y el registro del pedido no usan el LLM (0,04 s). Carga inicial: 20 s para el catálogo, el índice BM25 y el modelo de embeddings.

Limitaciones observadas con el modelo de 7B: es sensible a la redacción del prompt (se ajustó solo con diálogos propios, nunca con consultas de `test`); a veces redacta mal un cambio ("añadidas dos más" cuando pasó de dos a tres) aunque la operación y el resumen del código sean correctos, y puede necesitar un paso de más para leer el detalle de un producto.

### Decisiones de diseño de la voz (día 7)

- **El agente no cambia.** La voz se monta alrededor de la conversación por texto: ASR antes y TTS después (`voice/pipeline.py`; el comando es `voice/chat.py`). El grafo no se tocó; la sesión solo mide además cuánto tarda cada nodo.
- **Latencia.** Va desde que el audio del usuario está disponible hasta que la respuesta puede reproducirse, y se reparte en ASR, recuperación (nodos `recuperar` y `proponer_alternativa`), LLM (nodo `interpretar`), herramientas (el resto de nodos, con sus checkpoints) y TTS. La carga de los modelos se mide aparte. También se anota cuándo estaría listo el primer fragmento de audio, por si más adelante se reproduce mientras se sintetiza el resto.
- **Silencio.** Whisper large-v3-turbo transcribe el silencio o el ruido como "Gracias por ver el vídeo" y su probabilidad de no-voz no lo detecta. Se activa el filtro de voz de `faster-whisper` (Silero VAD, en CPU): sin voz, la transcripción queda vacía y el agente pide que se repita.
- **Texto para el TTS.** Antes de sintetizar, los importes y cantidades pasan a palabras con su concordancia ("7,74 €" → "siete euros con setenta y cuatro céntimos", "1 unidad" → "una unidad"), se quitan identificadores y símbolos y los títulos de catálogo se acortan a su primera parte. La transcripción guarda el texto original del agente y, aparte, lo que se envió al TTS.
- **Fragmentos.** XTTS-v2 recorta las frases de más de 239 caracteres en español: el texto se parte por frases (y por comas si hace falta) en trozos de hasta 200 caracteres, que se sintetizan uno a uno y se unen con una pausa corta. La semilla del muestreo se fija para que la misma entrada dé la misma salida.
- **Audio que sobra.** Con textos muy cortos XTTS-v2 a veces sigue "hablando" (un "Sí." salió con cinco segundos de balbuceo). Si un fragmento dura más de 2 s + 0,15 s por carácter, se vuelve a sintetizar con otra semilla, hasta tres veces, y se usa el intento más corto. El umbral es holgado a propósito: una voz pausada llega a 0,10 s por carácter, y un primer umbral ajustado al hablante de prueba (0,09) hacía reintentar sin motivo con la voz real.
- **Memoria de GPU compartida.** Tras cada síntesis se libera la memoria que PyTorch deja en reserva (cerca de 1 GB después de una respuesta larga). El LLM y Whisper reservan la suya fuera de PyTorch, y en la GPU de 12 GB de la workstation esa reserva bastó para que Whisper se quedara sin memoria en el turno siguiente.
- **Voz.** Sale de `audio/referencia/referencia.wav` (o de `SHOPPING_AGENT_VOICE_REF`). Mientras no exista, el desarrollo usa un hablante incluido en XTTS-v2, elegido de forma explícita; nunca la voz de otra persona. La carpeta `audio/` y cualquier archivo de audio están fuera de git.
- **Repetición con el texto correcto.** Como cada turno cambia el carrito y la tienda, no se repite un turno suelto: se repite la conversación entera desde la misma tienda inicial, en otro hilo, dando al agente el texto correcto en lugar del audio. Se compara turno a turno si el ASR cambió el texto, si el agente hizo operaciones distintas y si el estado final de la tienda coincide.
- **Métricas.** WER con `jiwer` tras normalizar los dos textos (cifras en palabras, minúsculas, sin tildes ni puntuación), para que "60 €" y "sesenta euros" cuenten como lo mismo. Importes y cantidades se extraen de ambos textos y se comparan como conjuntos con repetición; "un" y "una" sueltos son artículos y no cuentan. Los nombres de producto esperados en cada turno (incluidos "el primero", "el segundo"…) se dan en `scenarios/<escenario>.terminos.json`. La semejanza de hablante se mide con ECAPA-TDNN de SpeechBrain, un modelo distinto del codificador de XTTS-v2, en CPU.
- **Dependencias.** `coqui-tts` 0.28 funciona con PyTorch 2.14 sin cambiarlo. `torchaudio` y `torchcodec` se toman del índice de PyTorch para CUDA 12.6 (las ruedas de PyPI están compiladas para CUDA 13 y no cargan) y `torchcodec` necesita FFmpeg en el sistema; en Colab habrá que usar el índice que corresponda a su versión de CUDA.

Mediciones de voz en la workstation (RTX A2000 12 GB) con el guion `demo_compra` (8 turnos). En las dos corridas los audios de entrada son sintéticos (un hablante incluido en XTTS-v2), porque aún no hay grabaciones de los turnos: sirven como **prueba de flujo, no como evaluación del ASR**. Cambia la voz que clona el agente:

| | Hablante de prueba | Voz del usuario |
|---|---|---|
| Referencia | 21 s sintetizados con un hablante incluido en XTTS-v2 | grabación propia de 30 s (`audio/referencia/referencia.wav`, sin versionar) |
| Corrida | [results/voz_demo_compra](../results/voz_demo_compra/transcripcion.md) | [results/voz_demo_compra_voz_usuario](../results/voz_demo_compra_voz_usuario/transcripcion.md) |
| Inteligibilidad (WER de Whisper sobre la síntesis) | 3,6 % | 5,7 % |
| Semejanza con la referencia (coseno ECAPA), media / mínima | 0,866 / 0,852 | 0,762 / 0,744 |
| TTS por turno, media en turnos con LLM | 5,7 s | 8,2 s |
| Latencia total, media en turnos con LLM / sin LLM | 13,1 s / 3,3 s | 15,7 s / 4,8 s |
| Duración del audio de respuesta | 8–28 s | 12–47 s |

Las dos corridas se repitieron el 10 de noviembre con el reranker por defecto (`control`) y la tabla trae esas cifras. Las observaciones de detalle que siguen (palabras concretas mal entendidas, turnos con sílabas de más) se hicieron sobre las corridas originales, sin reranker, que quedan en el historial de git; las cifras por etapa cambian poco.

- Carga inicial: de 30 a 42 s en total con los archivos ya en la caché del disco (catálogo y recuperadores 20 s, LLM 1 s, Whisper 1 s, XTTS-v2 8–10 s). En frío, leer el catálogo y los embeddings desde el disco de datos llegó a tardar 153 s.
- VRAM del proceso: 9,5 GB con los cuatro modelos cargados y 9,7 GB al terminar la conversación, igual con las dos voces.
- Latencia por etapa en los turnos con LLM (media): ASR 0,4 s, recuperación 0,01 s, LLM 6,7 s, herramientas 0,04 s y TTS 5–8 s. El TTS sintetiza a unas cuatro veces el tiempo real; el primer fragmento está listo en 1–6 s, así que reproducir mientras se sintetiza el resto ahorraría varios segundos por turno.
- La voz del usuario habla más despacio que el hablante de prueba (0,08–0,10 s por carácter frente a 0,06–0,07), y por eso sus audios y su tiempo de TTS son más largos.
- Inteligibilidad: con las dos voces los importes y las cantidades se entienden todos. Los errores son marcas que no son palabras ("LYCHL" → "Lichel", "Andfive" → "Ant5"), "inalambricos" (el catálogo lo trae sin tilde) y alguna palabra suelta que XTTS-v2 añade al final de un fragmento: dos interjecciones con el hablante de prueba ("No.", "¡Ole!") y unas sílabas de más tras "¿Lo confirmo?" con la voz del usuario, justo en la frase que pide la confirmación (turno 6, WER del 11,8 %).
- Semejanza: el coseno mide parecido de timbre con un modelo de verificación de hablante; 0,70–0,79 con la voz real queda por debajo del hablante de prueba, que parte de una referencia generada por el propio XTTS-v2. Falta el juicio de oído.
- ASR sobre los audios sintéticos: WER 0 %, sin errores en importes, cantidades ni nombres de producto. No dice nada del ASR con una voz real.
- El ASR escribió "Bluetooth" con mayúscula donde el guion dice "bluetooth", y el LLM buscó "auriculares Bluetooth deporte". En la primera corrida eso bastó para que los candidatos salieran en otro orden y "el segundo" fuera otro producto en los turnos 2 y 3, porque el modelo denso distingue mayúsculas (BM25 no). Desde entonces la búsqueda del agente pasa la consulta a minúsculas, como vienen todas las consultas de ESCI con las que se midió el recuperador (en `train` ninguna lleva mayúsculas, así que el nDCG@10 no cambia: 0,7236). En las corridas guardadas, hechas ya con ese cambio, el agente ejecuta las mismas operaciones con el audio que con el texto correcto a partir del turno 2; en el turno 1 solo difiere la forma en que el LLM escribe la consulta.

## 4. Datos

- Filtro: `product_locale == "es"` y `small_version == 1`.
- Consultas: ~300 de `test` para evaluación y ~1 500 de `train` para desarrollo, separadas por `query_id`.
- Catálogo: todos los productos anotados de esas consultas (≥ 5 000), con título, descripción, viñetas, marca, color e identificador.
- Tienda simulada: precios y stock generados con semilla fija; instantánea `store_seed.sqlite` que se copia para restaurar.

## 5. Recuperación y GNN

1. **Baseline léxico:** BM25 sobre título + marca + viñetas + descripción.
2. **Denso:** embeddings multilingües del mismo texto, índice FAISS.
3. **Fusión:** RRF de ambos, top 50.
4. **Reranker GraphSAGE (PyTorch Geometric):** reordena los 50 primeros del híbrido sobre un grafo consulta–producto. El diseño y los resultados están más abajo.
5. **Métrica:** nDCG@10 sobre candidatos anotados con ganancias 1 / 0,1 / 0,01 / 0.

Comparación con las mismas consultas de `test`: BM25 · denso · híbrido · híbrido + control sin grafo · híbrido + GraphSAGE. Se hizo una sola vez, al cerrar la evaluación; el diseño del reranker, más abajo, se decidió antes y solo con consultas de `train`.

### Evaluación final en test (día 11)

[results/retrieval_test.md](../results/retrieval_test.md): 300 consultas de test, el 10 de noviembre de 2026, en el commit `7c385b8`. Las consultas de test no se habían leído en ningún paso anterior. Los rerankers se entrenaron como en la validación (1 200 consultas de ajuste, mismos hiperparámetros, semillas 0 a 4) y puntúan cada consulta de test como lo hace el agente con una consulta nueva: conectada solo a sus 50 candidatos, sin etiquetas. Los intervalos son del 95 %, por bootstrap de consultas; las diferencias, consulta a consulta. Nada se ajustó después de ver estos números.

| Sistema | nDCG@10 en test | recall@50 | Dif. con el híbrido | Dif. con el control | nDCG@10 en validación |
|---|---|---|---|---|---|
| BM25 (base léxica) | 0,6797 [0,6515; 0,7066] | 0,6455 | −0,0316 [−0,0441; −0,0191] | | 0,6750 |
| Denso | 0,7278 [0,7016; 0,7524] | 0,6501 | +0,0165 [+0,0042; +0,0291] | | 0,7535 |
| Híbrido RRF | 0,7113 [0,6844; 0,7368] | 0,7194 | | | 0,7403 |
| Híbrido + control sin grafo (la configuración del agente) | 0,7292 [0,7031; 0,7536] (± 0,0006 entre semillas) | 0,7194 | +0,0179 [+0,0086; +0,0275] | | 0,7582 |
| Híbrido + GraphSAGE (la variante del GNN) | 0,7363 [0,7104; 0,7605] (± 0,0025 entre semillas) | 0,7194 | +0,0249 [+0,0152; +0,0351] | +0,0071 [+0,0028; +0,0117] | 0,7617 |

- **Reordenar ayuda también en test.** El control mejora al híbrido en +0,018 y GraphSAGE en +0,025, con intervalos que excluyen el cero. Es lo mismo que se vio en validación (+0,018 y +0,021).
- **El grafo aporta más que en validación.** GraphSAGE supera al control en +0,0071, con un intervalo que excluye el cero; en validación eran +0,0035, con un intervalo que lo incluye por muy poco. Sigue siendo una diferencia pequeña (un 1 % relativo) frente a intervalos de ±0,025 en el valor de cada sistema, pero en test no queda dentro del ruido. El agente usa por defecto el control, decisión tomada con la validación y antes de esta medida; **no se ha cambiado a raíz de test**. Si se cambia, es una decisión del autor y debe decirse que se tomó después de ver test.
- **Test es más difícil que validación para todos los sistemas menos BM25.** El denso, el híbrido y los rerankers bajan entre 0,026 y 0,029; BM25 sube 0,005. Como también bajan los modelos sin entrenar, la mayor parte de la caída es de la muestra de consultas, no de haber elegido hiperparámetros con la validación.
- **El híbrido ordena peor los candidatos anotados que el denso** (0,7113 frente a 0,7278), igual que en validación, pero recupera más productos exactos entre los 50 primeros (0,719 frente a 0,650 del denso y 0,646 de BM25). Por eso es la primera etapa: lo que el reranker reordena son esos 50. Los rerankers comparten el recall@50 del híbrido.
- **Qué mide y qué no.** El nDCG@10 es sobre los candidatos anotados de cada consulta, la métrica del enunciado; no mide la lista sobre todo el catálogo. Las cinco semillas son de entrenamiento: la de la semilla 0 es la configuración con la que se generan los pesos del agente. Entre la validación y esta medida el reranker se reescribió sobre `HeteroData` y `HeteroConv` sin cambiar el modelo (mismos parámetros iniciales y puntuaciones iguales hasta 1e-7); la medida en test se hizo ya con esa versión.
- **Orden de los hechos.** La evaluación se lanzó a las 15:04, al terminar las corridas de escenarios y de voz y con la GPU libre. El aviso de esperar a que el modelo estuviera cerrado, y la confirmación posterior, llegaron a esa sesión cuando ya había terminado. Lo que se midió coincide con lo que quedó cerrado: embeddings `multilingual-e5-small`, las variantes `control` y `sage` sin ninguna más, y el código sobre `HeteroData` (commits `c5f422b` y `e58dc43` incluidos). No se ha repetido. La columna de validación de la tabla sale de `results/reranker_validation.json`; si esa tabla se regenera, `--render` la actualiza sin volver a leer test.

### Diseño y resultados del reranker (días 8–9)

**Datos de desarrollo.** Las 1 500 consultas de `train` se reparten por `query_id`, con semilla 42, en 1 200 de ajuste y 300 de validación. Todo se entrena con las de ajuste y se elige con las de validación. El código de entrenamiento solo lee el catálogo y la partición de `train` (hay una prueba que lo comprueba); las consultas de `test` y sus qrels no se han cargado en ningún momento.

**Grafo.** Es un grafo heterogéneo, un `HeteroData` de PyTorch Geometric, con dos tipos de nodo: `product` (los 43 674 productos) y `query` (las consultas), cada uno con su embedding de texto (`multilingual-e5-small`) como características. Tiene cuatro tipos de arista, que PyG nombra como (origen, relación, destino); el mensaje va del origen al destino:

| Tipo de arista | Qué une | Aristas | ¿Usa etiquetas? |
|---|---|---|---|
| `(product, candidate, query)` | los 50 primeros del híbrido para esa consulta | 75 000 | no |
| `(product, similar, product)` | los 10 vecinos más cercanos por coseno | 436 740 | no |
| `(product, brand, product)` | hasta 5 productos de la misma marca, los más parecidos | 118 605 | no |
| `(query, exact, product)` | la consulta de ajuste tiene ese producto anotado como exacto | 13 301 | sí, de ajuste |

- **Inductivo.** Una consulta nueva entra al grafo conectada solo a sus 50 candidatos, sin etiquetas, igual que las de validación. Los productos no reciben nada de ella, así que añadirla no cambia la puntuación de ninguna otra.
- **Sin fuga de etiquetas.** Ninguna consulta recibe mensajes por `exact` (la relación solo va hacia el producto). Y al entrenar con un lote de consultas se quitan del grafo sus propias aristas `exact`: sus productos exactos no la tienen como vecina, como le pasará a una consulta nueva. Sus etiquetas solo son la supervisión. Una prueba cambia las etiquetas de una consulta de ajuste y comprueba que sus puntuaciones no se mueven (y que sin la máscara sí lo harían).

**Modelo.** Dos capas. Cada una es un `HeteroConv` de PyG con una convolución por tipo de arista (`SAGEConv`, media de los vecinos; `GATv2Conv` en la variante con atención), cuyas salidas se suman en el nodo de destino; a eso se añade una transformación lineal propia de cada tipo de nodo. La capa se elige en la configuración (`conv`), de modo que otra capa heterogénea de PyG sería una variante más. La puntuación de un par es una combinación lineal de las tres señales de la primera etapa (coseno denso, BM25 relativo al máximo de la consulta y RRF) más una corrección que sale de los estados de la consulta y del producto. La corrección empieza en cero y la parte lineal en el coseno: sin entrenar, el modelo ordena igual que el recuperador denso. El **control sin grafo** es ese mismo modelo sin ninguna relación: mismas características, misma cabeza, misma pérdida y ningún paso de mensajes.

**Pérdida.** Por pares dentro de cada consulta, logística (como RankNet) y ponderada por la diferencia de ganancia entre los dos candidatos: confundir un exacto con un irrelevante cuesta diez veces más que confundir un sustituto con un irrelevante, como en el nDCG. Cada consulta pesa lo mismo.

**Irrelevantes al azar.** A cada consulta de ajuste se le añaden 20 productos del catálogo al azar con ganancia 0. Los candidatos anotados de una consulta tienen todos algo que ver con ella, pero el agente reordena los 50 primeros del híbrido, donde también hay productos fuera de tema; sin estos ejemplos el reranker a veces los subía a los primeros puestos (para "2 barras visillos sin tornillos color negro" llegó a poner libros con "sin" en el título). No afectan a la evaluación, que sigue siendo solo sobre candidatos anotados.

**Hiperparámetros.** Los mismos para todas las variantes: 64 unidades, 2 capas, dropout 0,5, AdamW con tasa 1e-3 y decaimiento 1e-2, lotes de 64 consultas y 12 épocas. Salen de un barrido pequeño en validación (16 combinaciones de tamaño, dropout, tasa y decaimiento, con el control y GraphSAGE): se eligió la combinación cuya curva de validación era más estable. No se usa parada temprana.

**Resultados en validación** (300 consultas, 5 semillas; [results/reranker_validation.md](../results/reranker_validation.md)). "Anotados" es la métrica del enunciado. "Catálogo" es el nDCG@10 de la lista sobre todo el catálogo contando lo no anotado como irrelevante; los rerankers reordenan los 50 primeros del híbrido, como en el agente. Las diferencias son por consulta, con intervalo del 95 % por bootstrap.

| Sistema | Aristas | nDCG@10 anotados | nDCG@10 catálogo | Anotados: dif. con el control |
|---|---|---|---|---|
| BM25 (base léxica) | | 0,6750 | 0,4399 | |
| Denso | | 0,7535 | 0,5114 | |
| Híbrido RRF | | 0,7403 | 0,5236 | |
| **Control sin grafo** (el del agente por defecto) | ninguna | 0,7582 ± 0,0005 | 0,5500 ± 0,0012 | |
| GraphSAGE | `candidate` | 0,7585 ± 0,0003 | 0,5505 ± 0,0006 | +0,0003 [−0,0004; +0,0010] |
| GraphSAGE | `similar` | 0,7615 ± 0,0017 | 0,5494 ± 0,0019 | +0,0034 [+0,0003; +0,0064] |
| GraphSAGE | `brand` | 0,7609 ± 0,0013 | 0,5477 ± 0,0054 | +0,0028 [−0,0008; +0,0065] |
| GraphSAGE | `exact` | 0,7596 ± 0,0010 | 0,5420 ± 0,0018 | +0,0014 [−0,0003; +0,0031] |
| **GraphSAGE** (el de la ablación) | `candidate`, `similar`, `brand` | 0,7617 ± 0,0006 | 0,5463 ± 0,0031 | +0,0035 [−0,0001; +0,0073] |
| GraphSAGE con etiquetas | las cuatro | 0,7628 ± 0,0017 | 0,5470 ± 0,0036 | +0,0046 [+0,0020; +0,0074] |
| GATv2 | `candidate`, `similar`, `brand` | 0,7616 ± 0,0022 | 0,5505 ± 0,0015 | +0,0034 [+0,0013; +0,0058] |
| GATv2 con etiquetas | las cuatro | 0,7630 ± 0,0006 | 0,5462 ± 0,0016 | +0,0048 [+0,0012; +0,0085] |

Lo que dicen los números:

- **Reordenar ayuda; el grafo, muy poco.** Frente al híbrido, GraphSAGE gana +0,021 en anotados (IC [+0,012; +0,031]) y +0,023 en catálogo (IC [+0,007; +0,039]). Pero casi todo eso lo consigue ya el control sin grafo (+0,018 y +0,026). La aportación del paso de mensajes es de +0,0035 en la métrica del enunciado, un 0,5 % relativo, y en la lista sobre el catálogo no hay diferencia con el control (−0,004, IC [−0,009; +0,002]).
- **Esa aportación es frágil.** El intervalo de +0,0035 es [−0,0001; +0,0073] e incluye el cero por muy poco. En la primera generación de esta tabla, con el código anterior a la refactorización, salió +0,0038 [+0,0004; +0,0073] y lo excluía por igual de poco: es el mismo modelo, y el ruido entre corridas en GPU basta para cruzar esa línea. Además se han comparado nueve variantes y los hiperparámetros se eligieron con estas mismas 300 consultas. Repitiendo control y GraphSAGE con otro número de épocas (`--epochs`, medido con aquella primera versión), la diferencia es +0,0006 con 6 épocas, +0,0038 con 12, +0,0023 con 18 y 0,0000 con 24, y solo es distinta de cero con 12. El control no pasa de 0,7586 con ninguna duración; los modelos con grafo llegan a 0,762–0,763.
- **Aristas.** `similar` es la que aporta (+0,0034, la única relación sola con un intervalo que excluye el cero). `brand` da algo parecido pero con un intervalo que incluye el cero. `candidate` no aporta nada: promediar 50 candidatos no le dice a la consulta nada que no esté ya en su embedding. `exact` sola tampoco (+0,0014).
- **GATv2** queda igual que GraphSAGE (0,7616 frente a 0,7617) y tarda varias veces más en entrenar (unos 5 minutos las 5 semillas, frente a 1).
- **Frente al denso.** GraphSAGE mejora al coseno denso en +0,008 (IC [+0,001; +0,015]); el control, en +0,005 con un intervalo que incluye el cero. Con embeddings congelados las señales de la primera etapa dejan poco margen: sumar BM25 al coseno con el mejor peso posible no mejora nada en ajuste.

**Decisión sobre las aristas con etiquetas.** Usar `exact` mete etiquetas de `train` dentro del modelo en inferencia (los productos recuerdan para qué consultas de ajuste fueron exactos). Es defendible como parte del método ajustado, pero es una interpretación del enunciado, que prohíbe que las etiquetas sean información consultable por el agente. En validación añaden +0,001 sobre el GraphSAGE sin etiquetas (0,7628 frente a 0,7617), dentro del ruido entre semillas, y nada en la lista sobre el catálogo. **Ni el reranker por defecto del agente ni el GraphSAGE de la ablación las usan**: no hay ganancia que justifique la duda. Queda disponible como variante `sage_exact`. Tiene sentido que aporten poco: solo el 5 % de los pares de validación tienen un producto que sea exacto para otra consulta de ajuste, y esos productos no son más relevantes que el resto (ganancia media 0,42 frente a 0,44).

**Reranker del agente: el control sin grafo, por defecto.** `SHOPPING_AGENT_RERANKER` elige qué reordena los 50 primeros del híbrido: `control` (por defecto), `sage` (GraphSAGE), cualquier otra variante entrenada u `off` (el híbrido solo). Reordenar se deja activado porque en validación mejora al híbrido en las dos métricas con intervalos que excluyen el cero. Entre los dos rerankers, el autor eligió el control (10 de noviembre de 2026): en la lista sobre el catálogo, que es lo que ve el usuario, rinde igual que GraphSAGE (0,5500 frente a 0,5463), la ventaja del grafo en la métrica del enunciado es de +0,004 y frágil, y el control es más simple y más barato. La ablación del GNN en el agente queda así limpia: `control` frente a `sage` cambia solo el paso de mensajes.

**Coste** ([control](../results/reranker_cost_control.json), [GraphSAGE](../results/reranker_cost_sage.json); RTX A2000, 200 consultas). La búsqueda híbrida tarda 15–16 ms por consulta. Con el control pasa a 18 ms en GPU (+2 ms; +89 ms si el reranker va en CPU) y el proceso ocupa 102 MiB más de VRAM (604 → 706 MiB con el recuperador denso). Con GraphSAGE, 27 ms (+12 ms; +127 ms en CPU) y 230 MiB más. Junto a los 9,5 GB del resto, cualquiera de los dos cabe de sobra en la T4. El comando de entrenamiento tardó 3 minutos, casi todo en leer el catálogo y cargar los modelos; el entrenamiento en sí son unos segundos en GPU. Los pesos de cada variante ocupan 13 MB.

**Paridad tras pasar a `HeteroData` y `HeteroConv`.** La primera versión del código guardaba el grafo en una clase propia y sumaba las relaciones a mano. Al pasar a las clases heterogéneas de PyG se comprobó, antes de regenerar la tabla, que el modelo es el mismo:

- Con la misma semilla, los parámetros iniciales son idénticos bit a bit, y en CPU los estados de los nodos y las puntuaciones coinciden hasta 1e-7 (cambia el orden en que se suman los mensajes y, con él, el redondeo).
- Reentrenando con las mismas 5 semillas, el control da exactamente los mismos nDCG@10 de validación (0,7578 / 0,7589 / 0,7583 / 0,7577 / 0,7583).
- GraphSAGE da medias de 0,7625, 0,7622 y 0,7613 en tres repeticiones, frente al 0,7619 de la tabla de entonces. El código anterior, repetido dos veces, da 0,7619 y 0,7621: la diferencia es el ruido entre corridas en GPU, no el cambio.

La tabla de arriba es ya la del código nuevo: se regeneró el 10 de noviembre de 2026 con las mismas semillas. El control sale idéntico (0,7582 ± 0,0005) y GraphSAGE queda en 0,7617 ± 0,0006, frente al 0,7619 ± 0,0009 de la primera generación. Los pesos también son nuevos, porque el cambio renombra los parámetros de las capas: los archivos pasan a llamarse `reranker_<variante>.v2.pt` (control, semilla 0: 0,7578 en validación; GraphSAGE, semilla 0: 0,7634). La evaluación en test se hizo con este código. El coste por consulta no se ha vuelto a medir.

**Limitaciones.**

- 300 consultas de validación solo distinguen diferencias de más de ±0,004–0,008 en nDCG@10. Las diferencias entre variantes con grafo están por debajo.
- La métrica de catálogo es pesimista: cerca del 40 % de los 10 primeros son productos sin anotar para esa consulta, y algunos son claramente relevantes (para "regleta sin cable usb" el GNN sube regletas sin cable que nadie anotó). Sirve para detectar fallos graves, no para afinar.
- Los hiperparámetros y el número de épocas se eligieron en la misma validación con la que se comparan las variantes, así que las cifras de los rerankers son algo optimistas frente a las de los modelos base. La evaluación en `test` (más arriba) lo confirma solo en parte: allí bajan todos los sistemas menos BM25, también los que no se entrenan.
- El control se reproduce exactamente con la misma semilla. GraphSAGE no: algunas operaciones del paso de mensajes en GPU no son deterministas y el entrenamiento amplifica esas diferencias de redondeo. En 25 corridas, la misma semilla se desvió hasta ±0,002 de nDCG@10 y la media de 5 semillas quedó entre 0,7613 y 0,7625. Es un ruido del mismo orden que la desviación entre semillas.
- Los pesos se entrenan solo con las 1 200 consultas de ajuste. Reentrenar con las 1 500 antes de la evaluación final es posible, pero ese modelo ya no tendría validación propia.
- Con solo 1 200 consultas de ajuste y el codificador de texto congelado, la corrección aprendida sobreajusta pronto (por eso 12 épocas y dropout alto). Más consultas de `train` (ESCI tiene más en español) probablemente ayudarían más que cambiar el grafo; no se ha hecho porque cambiaría la selección de consultas.

Riesgo que el plan anticipaba: que el GNN no superase al híbrido. Lo supera, pero por haber entrenado un reranker y no por el grafo; la ablación con el control sin grafo es la que lo muestra.

## 6. Evaluación

- **20 escenarios** con estado inicial reproducible (JSON: semilla, stock inicial, turnos, estado final esperado). Seis por audio, uno por cada situación obligatoria; al menos tres con varios turnos.
- Cada caso de voz se repite con su transcripción correcta para aislar errores del ASR.
- Se guardan audios, transcripciones, llamadas a herramientas y estado final de la tienda.
- **Métricas:** % de escenarios correctos, incumplimientos de restricciones, errores de transcripción en cantidades, importes y productos.
- **Voz:** inteligibilidad (WER de Whisper sobre el audio sintetizado) y semejanza (coseno entre embeddings de hablante de la referencia y la síntesis).
- **Latencia:** por etapa (ASR, recuperación, LLM, herramientas, TTS), separando carga inicial de consultas posteriores.
- Análisis de al menos cinco aciertos y cinco fallos con sus causas.

### Diseño y resultados de la evaluación (días 10–11)

**Escenarios como datos.** Veinte escenarios en `scenarios/evaluacion/`, uno por JSON y cada uno de un tipo distinto. Los seis primeros son los de voz que pide el enunciado: compra confirmada, pedido ambiguo, cambio de cantidad, producto sin existencias, corrección de una transcripción, y cambio de stock entre cotización y confirmación con confirmación repetida. Los otros catorce cubren el resto de las reglas del agente: presupuesto excedido, cantidad inválida, producto inexistente, atributo no verificable, rechazo en la confirmación, memoria de preferencias entre conversaciones, un sí con cambios, preguntas que no deben tocar el carrito, stock insuficiente al añadir, quitar del carrito, bajar el presupuesto con el carrito lleno, cerrar sin carrito, presupuesto compartido entre dos productos y producto agotado al confirmar. En total, 87 turnos (31 en los de voz).

- **Productos por regla.** Un escenario no nombra productos por su identificador: `candidate:N` y `cart:N` son el candidato o la línea de carrito N en ese momento de la conversación, y `remember` les pone nombre. El precio y las existencias de los que depende el resultado los fija un suceso de la tienda (`set_offer`) después de la búsqueda. Así lo que se espera se puede escribir de antemano (por ejemplo, "dos unidades a 14,50 €, total 29,00 €, quedan 18") sin mirar qué devuelve la búsqueda.
- **Estado inicial.** Cada escenario parte de una copia de `store_seed.sqlite`, con hilo y usuario nuevos; la memoria de Postgres no arrastra nada de otros escenarios. El escenario de memoria abre dos conversaciones del mismo usuario.
- **Veredicto.** Correcto si se cumplen todas las comprobaciones del escenario (de cada turno y finales), no hay violaciones y no hubo errores. Todo es código sobre la tienda y el estado del agente. Cuatro comprobaciones miran el texto de la respuesta (si cita otro producto con existencias, si dice que un dato no consta, si da el precio de la tienda, si contiene una palabra): son deterministas, pero una respuesta correcta dicha de otra forma puede no pasarlas, y por eso la ficha conserva el texto.
- **Violaciones.** Se calculan aparte, comparando la tienda antes y después de cada turno: `cantidad` (línea con menos de una unidad, o pedido distinto de lo cotizado), `presupuesto` (pedido o carrito recién modificado por encima del presupuesto), `existencias` (existencias negativas o pedido con más unidades de las que había), `pedido_duplicado` (más de un pedido en un turno, o un pedido sin cotización esperando) y `cambio_parcial` (confirmación rechazada que cambió algo, o pedido que no descontó lo comprado o no vació el carrito).
- **Voz.** Los turnos por voz pasan por el mismo `VoicePipeline` que una conversación normal. La corrida por voz se repite entera con la transcripción correcta, desde la misma tienda, y se comparan veredicto, operaciones y tienda final.

**Resultados** ([results/escenarios/resumen.md](../results/escenarios/resumen.md); cada corrida tiene una ficha por escenario). Workstation, RTX A2000 de 12 GB, 10 de noviembre de 2026.

| Corrida | Entrada | Reranker | Correctos | Fallan |
|---|---|---|---|---|
| `texto` | texto | control (por defecto) | 14 de 20 (70 %) | 03, 04, 06, 09, 10, 20 |
| `texto_sage` | texto | GraphSAGE | 16 de 20 (80 %) | 03, 04, 06, 09 |
| `texto_sin_reranker` | texto | ninguno | 16 de 20 (80 %) | 03, 04, 09, 10 |
| `voz` | audio sintético de prueba | control | 3 de 6 (50 %) | 03, 04, 06 |
| `voz_texto_correcto` | transcripción correcta | control | 3 de 6 (50 %) | 03, 04, 06 |

- **Violaciones de restricciones: ninguna** en las cinco corridas (323 turnos): ni cantidades inválidas, ni pedidos o carritos por encima del presupuesto, ni existencias negativas o pedidos sin stock, ni pedidos duplicados, ni cambios parciales. Las validaciones por código y la transacción de confirmación hicieron su trabajo en todos los casos, incluidos el stock que cambia entre la cotización y la confirmación y el sí repetido.
- **Todos los fallos son decisiones del LLM en el diálogo.** La tienda nunca queda en un estado inválido, pero el agente hace algo distinto de lo que se le pidió:

| Escenario | Dónde falla | Qué pasa |
|---|---|---|
| 03 cambio de cantidad | las cinco corridas | El cambio de dos a cuatro unidades se hace bien. Ante «Ciérralo.» el LLM no cotiza: contesta repitiendo el carrito, y el «Sí» siguiente no tiene nada que confirmar. No se compra nada. Con «Cierra el pedido» o «Quiero cerrar el pedido» sí cotiza. |
| 04 sin existencias | las cinco corridas | La tienda rechaza el producto agotado y el LLM, sin que nadie se lo pida, añade el segundo candidato. Cuando el usuario pide después «una de la segunda», el carrito pasa a dos y se compran dos. |
| 06 cambio de stock | `texto`, `texto_sage`, `voz`, `voz_texto_correcto` | La confirmación se rechaza bien y el agente ofrece dejarlo en una unidad. Ante «Vale, déjalo en una», en lugar de cambiar la cantidad quita el producto: con el control añade una de las alternativas (se compra otro producto) y con GraphSAGE deja el carrito vacío. Sin reranker cambia la cantidad y acierta. Donde llegó a haber pedido, el sí repetido no lo duplicó. |
| 09 producto inexistente | las tres de texto | Ante «Añade dos del séptimo» (la lista tiene cinco) añade dos unidades de otro candidato en vez de preguntar. |
| 10 atributo no verificable | `texto`, `texto_sin_reranker` | A la pregunta por la valoración de los clientes, con el control repite la búsqueda y la lista sin contestar. Sin reranker dice «los clientes no han valorado esta sartén», que la comprobación cuenta como fallo porque afirma algo que el catálogo no dice (caso dudoso). Con GraphSAGE contesta que el catálogo no lo indica. |
| 20 agotado al confirmar | `texto` | El rechazo y las alternativas, que escribe el código, son correctos. Ante «la primera alternativa» el LLM añade la segunda. |

- **Aciertos para el análisis:** 05 (corrige de dos a doce antes de confirmar y no compra nada con dos), 13 («sí, pero que sean tres» no registra el pedido de una), 17 (bajar el presupuesto hace que la cotización se rechace sin que el agente toque el carrito), 19 (dos productos compartiendo presupuesto), 16 (dos altas en un turno y una baja), 11 (un no deja el carrito como estaba) y 12 (la preferencia llega a otra conversación). Dos aciertos con matices: en 08 el carrito queda vacío, pero el agente intenta quitar o cambiar un producto que no está y explica eso en lugar de decir que la cantidad no vale; en 12 vuelve a guardar la preferencia al preguntarle por ella.
- **Ablación de extremo a extremo.** Con el control aciertan 14 escenarios, con GraphSAGE 16 y sin reranker 16. No es una diferencia de calidad de la búsqueda: los tres aciertan y fallan casi en los mismos escenarios, y donde difieren (06, 10, 20) es porque salen otros candidatos y el LLM toma otro camino con el mismo mensaje. Con 20 escenarios y una corrida por configuración, dos escenarios de diferencia no permiten ordenar las configuraciones.
- **Determinismo.** La corrida `texto` se hizo dos veces (la primera coincidió con procesos de otra sesión en la GPU): las operaciones y las respuestas fueron idénticas turno a turno. Una sola corrida por configuración no deja ver, por tanto, cuánto cambiarían los aciertos con otra redacción de los turnos.

**Voz** (corrida `voz`, 31 turnos). Los audios de entrada son **sintéticos**: un hablante incluido en XTTS-v2 («Luis Moray») lee el guion, porque el usuario aún no ha grabado sus turnos. La respuesta sí se sintetiza con la voz clonada de su grabación de referencia.

| Medida | Resultado |
|---|---|
| WER del ASR | 2,1 % (28 de 31 turnos idénticos tras normalizar) |
| Errores del ASR en importes | 0 de 3 |
| Errores del ASR en cantidades | 0 de 8 |
| Errores del ASR en nombres de producto | 0 de 13 |
| Inteligibilidad de la voz generada (WER de Whisper sobre 31 respuestas) | 3,8 % |
| Semejanza con la voz de referencia (coseno ECAPA), media / mínima | 0,742 / 0,589 |

- Los tres turnos con diferencias tienen una sílaba de más al final («… al carrito E.», «… de la segunda. De.», «… LED. Lo.»): la añade el audio sintético de entrada, no es un error típico de reconocimiento. **Estas cifras no dicen nada del ASR con una voz real.**
- Con audio y con la transcripción correcta el veredicto es el mismo en los seis escenarios, y la tienda final coincide en cinco. En 06 la sílaba de más cambió la consulta que escribe el LLM y, con ella, la alternativa que acabó comprando; el fallo es el mismo. Los errores de los escenarios de voz son, por tanto, del agente y no del ASR.
- Los errores de inteligibilidad son del mismo tipo que en las corridas anteriores: marcas que no son palabras («Gastroback» → «GastroVac», «SLATOR» → «Les Lator», «Newdora» → «Neudora»). Falta el juicio de oído sobre la semejanza.

**Latencia**, desde que el audio del usuario está disponible hasta que la respuesta puede reproducirse (corrida `voz`, segundos por turno, media y máximo):

| Turnos | ASR | Recuperación | LLM | Herramientas | TTS | Total |
|---|---|---|---|---|---|---|
| Con LLM (25) | 0,35 (0,54) | 0,01 (0,03) | 5,14 (9,76) | 0,04 (0,09) | 6,42 (17,33) | 11,96 (25,57) |
| Sin LLM (6): confirmar el pedido | 0,33 (0,36) | 0,00 (0,03) | 0,00 | 0,03 (0,04) | 5,22 (10,69) | 5,59 (11,05) |

- Por texto (corrida `texto`, 74 turnos con LLM): recuperación 0,01 s, LLM 5,38 s (máximo 10,21), herramientas 0,04 s; 5,43 s en total. Los 13 turnos sin LLM tardan 0,03 s.
- Carga inicial, aparte: 27,4 s con todo en la caché del disco (catálogo y recuperadores 16,2 s, LLM 0,8 s, Whisper 1,0 s, XTTS-v2 8,8 s). Con el disco de datos en frío, el catálogo y los recuperadores tardan unos 150 s (pasó en `texto_sin_reranker`).
- El LLM y el TTS se reparten casi toda la latencia. El TTS depende de lo larga que sea la respuesta: las que repiten el carrito o la cotización son las de 10 a 17 s.
- VRAM: 9,5 GB con los cuatro modelos y el reranker cargados. En la GPU de 12 GB, con el escritorio ocupando 1,4 GB, el asignador de PyTorch avisó 27 veces de falta de memoria durante la corrida por voz; liberó caché y siguió, y ningún turno falló. En la T4 de 16 GB debería haber margen, pero no se ha comprobado.

**Qué se corrigió por el camino.**

- El escenario 09 no fijaba las existencias de los candidatos. En la primera corrida salió correcto por azar: el agente intentó añadir dos unidades del primer candidato y la tienda lo rechazó solo porque quedaba una. Se guardó esa corrida, se añadió al escenario el suceso que deja los cinco candidatos con 20 unidades (lo que se espera no cambia) y se repitieron todas las corridas. Desde entonces falla en las tres configuraciones.
- En el agente no se cambió nada: ni el prompt, ni las herramientas, ni el grafo. Los fallos se reportan tal cual.
- Las transcripciones de demostración de `results/` (`chat_*` y `voz_demo_*`) se regeneraron con el reranker por defecto.

**Qué no se midió.**

- **El ASR con la voz del usuario.** Faltan las grabaciones de los 31 turnos ([guion](../scenarios/evaluacion/GUION_GRABACION.md)). Con ellas en `audio/escenarios/`, el mismo comando las usa en lugar de los audios sintéticos.
- **Nada en Colab.** Todo se corrió en la workstation; las latencias y la memoria en la T4 están por medir.
- **El juicio de oído** sobre la voz clonada. La semejanza es un coseno entre embeddings de hablante.
- **La variabilidad.** Hay una corrida por configuración y el agente es determinista: los porcentajes describen estos 20 guiones con esta redacción, no una tasa de aciertos general. Los escenarios se escribieron conociendo las reglas del agente, aunque sin mirar antes cómo respondía a ellos.
- **La calidad de las explicaciones.** Las comprobaciones miran lo que el agente hace con la tienda; salvo las cuatro que buscan algo concreto en el texto, no juzgan si la respuesta explica bien un rechazo (el acierto con matices de 08 es un ejemplo).
- Las corridas de escenarios se hicieron en el commit `8711c79`, antes de que el reranker se reescribiera sobre `HeteroData` (mismo modelo); llevan la marca `+cambios` porque el README se estaba editando, sin cambios de código.

## 7. Cronograma

| Días | Trabajo | Entregable |
|---|---|---|
| 1–2 | Filtrar ESCI, armar catálogo y consultas, generar tienda con semilla y restauración | `data/` + `store_seed.sqlite` + pruebas |
| 3–4 | BM25, denso, fusión y nDCG@10 en `train` | Tabla baseline |
| 5–6 | Herramientas, validaciones y transacción de confirmación; Postgres para checkpoints y Store; grafo LangGraph en texto con LLM local | Compra completa por texto + pytest de idempotencia |
| 7 | ASR y TTS con clonación; ciclo completo por voz en Colab | Primer turno hablado de extremo a extremo |
| 8–9 | GraphSAGE: grafo, entrenamiento, reranking, ablación | Tabla comparativa |
| 10–11 | 20 escenarios, 6 audios, repetición con transcripción correcta, latencias, métricas de voz | Resultados y registros |
| 12 | Notebook final de Colab, README con versiones y configuración, análisis de aciertos y fallos | Entrega de código |
| 13–14 | Video (máx. 20 min) y margen | Video |

Orden pensado para tener un sistema completo sin GNN al final del día 7; el GNN se añade encima.

## 8. Estructura propuesta del repo

```
src/shopping_agent/
  data/        preparación de ESCI y tienda simulada
  retrieval/   bm25, denso, fusión, métricas; reranker: datos de desarrollo, primera etapa, grafo, modelo, entrenamiento e inferencia
  store/       esquema SQLite, transacciones, restauración
  agent/       estado, herramientas (registro), textos, nodos (nodes/), cableado del grafo, sesión, chat
  voice/       audio, asr, texto para voz, tts, turno completo, chat por voz
  eval/        recuperación, reranker (comparación y coste), métricas de voz; escenarios (formato, comprobaciones, violaciones, ejecutor e informe) y evaluación final en test
notebooks/     lab4_colab.ipynb (ejecución principal, pendiente)
scenarios/     guiones de demostración; evaluacion/ con los 20 escenarios y el guion de grabación (los audios van en audio/, sin versionar)
tests/
```

El detalle de los módulos del agente y el criterio de idioma de los nombres están en el README ("Organización del código").

Dependencias a añadir: `langgraph-checkpoint-postgres`, `psycopg[binary,pool]`, `faiss-cpu`, `bm25s`, `faster-whisper`, `llama-cpp-python`, `coqui-tts`, `torch-geometric`, `jiwer`, `speechbrain`.

## 9. Pendientes por decidir

- Modelo exacto de embeddings (por ahora `intfloat/multilingual-e5-small`). El LLM ya está elegido: Qwen2.5-7B-Instruct Q4_K_M.
- Comprobar en Colab la instalación de Postgres, de `llama-cpp-python` con CUDA y de las dependencias de voz (`torchaudio`, `torchcodec`, FFmpeg).
- Repetir la corrida por voz de los escenarios con los turnos del usuario grabados (`uv run python -m shopping_agent.eval.scenarios --mode voice`); la voz de referencia ya es real, pero los audios de entrada medidos hasta ahora son sintéticos.
- Las respuestas con el carrito completo dan audios de 25 a 47 s; valorar una versión hablada más breve.
- Grabar los 31 turnos de los seis escenarios de voz (`audio/escenarios/<escenario>/NN.wav`); el texto exacto está en `scenarios/evaluacion/GUION_GRABACION.md` y el README dice cómo. La voz de referencia (`audio/referencia/referencia.wav`) ya está grabada. La voz debe ser propia o autorizada, y los textos sintetizados distintos de los de la grabación.
- Decidir, a la vista de test, si el reranker por defecto sigue siendo el control: allí GraphSAGE lo supera en +0,0071 de nDCG@10 (IC [+0,0028; +0,0117]). Es una decisión posterior a ver test y hay que decirlo si se toma.
- La evaluación en test y las corridas de escenarios están hechas con `multilingual-e5-small`. Cambiar el modelo de embeddings obligaría a repetirlas, y la de test dejaría de ser una evaluación única.
- Repetir en Colab las corridas de escenarios (latencia y memoria en la T4).
- Análisis escrito de al menos cinco aciertos y cinco fallos; el material está en las fichas de `results/escenarios/` y en la tabla de fallos de la sección 6.
- Fecha oficial de entrega.
