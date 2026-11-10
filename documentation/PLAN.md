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
| Inteligibilidad (WER de Whisper sobre la síntesis) | 3,6 % | 4,8 % |
| Semejanza con la referencia (coseno ECAPA), media / mínima | 0,861 / 0,847 | 0,755 / 0,693 |
| TTS por turno, media en turnos con LLM | 5,3 s | 7,9 s |
| Latencia total, media en turnos con LLM / sin LLM | 12,5 s / 3,4 s | 15,1 s / 4,8 s |
| Duración del audio de respuesta | 5–32 s | 7–47 s |

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

Comparación a reportar con las mismas consultas de `test`: BM25 · denso · híbrido · híbrido + GraphSAGE (ablación: con y sin GNN). Esa evaluación final está pendiente; lo que sigue se midió solo con consultas de `train`.

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
| GraphSAGE | `candidate` | 0,7586 ± 0,0006 | 0,5502 ± 0,0007 | +0,0004 [−0,0003; +0,0011] |
| GraphSAGE | `similar` | 0,7619 ± 0,0015 | 0,5488 ± 0,0024 | +0,0037 [+0,0007; +0,0068] |
| GraphSAGE | `brand` | 0,7612 ± 0,0017 | 0,5470 ± 0,0052 | +0,0030 [−0,0007; +0,0068] |
| GraphSAGE | `exact` | 0,7595 ± 0,0011 | 0,5423 ± 0,0022 | +0,0013 [−0,0004; +0,0031] |
| **GraphSAGE** (el de la ablación) | `candidate`, `similar`, `brand` | 0,7619 ± 0,0009 | 0,5474 ± 0,0027 | +0,0038 [+0,0004; +0,0073] |
| GraphSAGE con etiquetas | las cuatro | 0,7631 ± 0,0015 | 0,5470 ± 0,0035 | +0,0049 [+0,0022; +0,0078] |
| GATv2 | `candidate`, `similar`, `brand` | 0,7616 ± 0,0028 | 0,5491 ± 0,0026 | +0,0035 [+0,0012; +0,0058] |
| GATv2 con etiquetas | las cuatro | 0,7632 ± 0,0009 | 0,5461 ± 0,0015 | +0,0051 [+0,0014; +0,0088] |

Lo que dicen los números:

- **Reordenar ayuda; el grafo, muy poco.** Frente al híbrido, GraphSAGE gana +0,022 en anotados (IC [+0,013; +0,031]) y +0,024 en catálogo (IC [+0,008; +0,040]). Pero casi todo eso lo consigue ya el control sin grafo (+0,018 y +0,026). La aportación del paso de mensajes es de +0,004 en la métrica del enunciado, un 0,5 % relativo, y en la lista sobre el catálogo no hay diferencia con el control (−0,003, IC [−0,008; +0,003]).
- **Esa aportación es frágil.** El intervalo de +0,0038 apenas excluye el cero, se han comparado nueve variantes y los hiperparámetros se eligieron con estas mismas 300 consultas. Repitiendo control y GraphSAGE con otro número de épocas (`--epochs`), la diferencia es +0,0006 con 6 épocas, +0,0038 con 12, +0,0023 con 18 y 0,0000 con 24, y solo es distinta de cero con 12. El control no pasa de 0,7586 con ninguna duración; los modelos con grafo llegan a 0,762–0,763.
- **Aristas.** `similar` es la que aporta (+0,0037). `brand` da algo parecido pero con un intervalo que incluye el cero. `candidate` no aporta nada: promediar 50 candidatos no le dice a la consulta nada que no esté ya en su embedding. `exact` sola tampoco (+0,0013).
- **GATv2** queda igual que GraphSAGE (0,7616 frente a 0,7619) y tarda varias veces más en entrenar (unos 5 minutos las 5 semillas, frente a 1).
- **Frente al denso.** GraphSAGE mejora al coseno denso en +0,008 (IC [+0,002; +0,015]); el control, en +0,005 con un intervalo que incluye el cero. Con embeddings congelados las señales de la primera etapa dejan poco margen: sumar BM25 al coseno con el mejor peso posible no mejora nada en ajuste.

**Decisión sobre las aristas con etiquetas.** Usar `exact` mete etiquetas de `train` dentro del modelo en inferencia (los productos recuerdan para qué consultas de ajuste fueron exactos). Es defendible como parte del método ajustado, pero es una interpretación del enunciado, que prohíbe que las etiquetas sean información consultable por el agente. En validación añaden +0,001 sobre el GraphSAGE sin etiquetas (0,7631 frente a 0,7619), dentro del ruido entre semillas, y nada en la lista sobre el catálogo. **Ni el reranker por defecto del agente ni el GraphSAGE de la ablación las usan**: no hay ganancia que justifique la duda. Queda disponible como variante `sage_exact`. Tiene sentido que aporten poco: solo el 5 % de los pares de validación tienen un producto que sea exacto para otra consulta de ajuste, y esos productos no son más relevantes que el resto (ganancia media 0,42 frente a 0,44).

**Reranker del agente: el control sin grafo, por defecto.** `SHOPPING_AGENT_RERANKER` elige qué reordena los 50 primeros del híbrido: `control` (por defecto), `sage` (GraphSAGE), cualquier otra variante entrenada u `off` (el híbrido solo). Reordenar se deja activado porque en validación mejora al híbrido en las dos métricas con intervalos que excluyen el cero. Entre los dos rerankers, el autor eligió el control (10 de noviembre de 2026): en la lista sobre el catálogo, que es lo que ve el usuario, rinde igual que GraphSAGE (0,5500 frente a 0,5474), la ventaja del grafo en la métrica del enunciado es de +0,004 y frágil, y el control es más simple y más barato. La ablación del GNN en el agente queda así limpia: `control` frente a `sage` cambia solo el paso de mensajes.

**Coste** ([control](../results/reranker_cost_control.json), [GraphSAGE](../results/reranker_cost_sage.json); RTX A2000, 200 consultas). La búsqueda híbrida tarda 15–16 ms por consulta. Con el control pasa a 18 ms en GPU (+2 ms; +89 ms si el reranker va en CPU) y el proceso ocupa 102 MiB más de VRAM (604 → 706 MiB con el recuperador denso). Con GraphSAGE, 27 ms (+12 ms; +127 ms en CPU) y 230 MiB más. Junto a los 9,5 GB del resto, cualquiera de los dos cabe de sobra en la T4. El comando de entrenamiento tardó 3 minutos, casi todo en leer el catálogo y cargar los modelos; el entrenamiento en sí son unos segundos en GPU. Los pesos de cada variante ocupan 13 MB.

**Paridad tras pasar a `HeteroData` y `HeteroConv`.** La tabla de arriba se generó con la primera versión del código, que guardaba el grafo en una clase propia y sumaba las relaciones a mano. Al pasar a las clases heterogéneas de PyG se comprobó que el modelo es el mismo:

- Con la misma semilla, los parámetros iniciales son idénticos bit a bit, y en CPU los estados de los nodos y las puntuaciones coinciden hasta 1e-7 (cambia el orden en que se suman los mensajes y, con él, el redondeo).
- Reentrenando con las mismas 5 semillas, el control da exactamente los mismos nDCG@10 de validación (0,7578 / 0,7589 / 0,7583 / 0,7577 / 0,7583).
- GraphSAGE da medias de 0,7625, 0,7622 y 0,7613 en tres repeticiones, frente al 0,7619 de la tabla. El código anterior, repetido dos veces, da 0,7619 y 0,7621: la diferencia es el ruido entre corridas en GPU, no el cambio.

La tabla no se ha regenerado: hacerlo ocupa la GPU 15 minutos y 6,4 GB, y en ese momento la usaba la evaluación de escenarios. Los pesos sí son nuevos, porque el cambio renombra los parámetros de las capas: los archivos pasan a llamarse `reranker_<variante>.v2.pt` (control, semilla 0: 0,7578 en validación; GraphSAGE, semilla 0: 0,7634). El coste por consulta tampoco se ha vuelto a medir.

**Limitaciones.**

- 300 consultas de validación solo distinguen diferencias de más de ±0,004–0,008 en nDCG@10. Las diferencias entre variantes con grafo están por debajo.
- La métrica de catálogo es pesimista: cerca del 40 % de los 10 primeros son productos sin anotar para esa consulta, y algunos son claramente relevantes (para "regleta sin cable usb" el GNN sube regletas sin cable que nadie anotó). Sirve para detectar fallos graves, no para afinar.
- Los hiperparámetros y el número de épocas se eligieron en la misma validación con la que se comparan las variantes, así que las cifras de los rerankers son algo optimistas frente a las de los modelos base. La evaluación en `test` lo corregirá.
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
  eval/        recuperación, reranker (comparación y coste), métricas de voz; escenarios y runner (pendiente)
notebooks/     lab4_colab.ipynb (ejecución principal, pendiente)
scenarios/     guiones de los escenarios (los audios van en audio/, sin versionar)
tests/
```

El detalle de los módulos del agente y el criterio de idioma de los nombres están en el README ("Organización del código").

Dependencias a añadir: `langgraph-checkpoint-postgres`, `psycopg[binary,pool]`, `faiss-cpu`, `bm25s`, `faster-whisper`, `llama-cpp-python`, `coqui-tts`, `torch-geometric`, `jiwer`, `speechbrain`.

## 9. Pendientes por decidir

- Modelo exacto de embeddings (por ahora `intfloat/multilingual-e5-small`). El LLM ya está elegido: Qwen2.5-7B-Instruct Q4_K_M.
- Comprobar en Colab la instalación de Postgres, de `llama-cpp-python` con CUDA y de las dependencias de voz (`torchaudio`, `torchcodec`, FFmpeg).
- Repetir la corrida por voz con los turnos del usuario grabados (`audio/escenarios/`); la voz de referencia ya es real, pero los audios de entrada medidos hasta ahora son sintéticos.
- Las respuestas con el carrito completo dan audios de 25 a 47 s; valorar una versión hablada más breve.
- Grabar los audios de los escenarios (`audio/escenarios/<escenario>/NN.wav`); el README dice cómo. La voz de referencia (`audio/referencia/referencia.wav`) ya está grabada. La voz debe ser propia o autorizada, y los textos sintetizados distintos de los de la grabación.
- Evaluación final en `test` (una sola vez): BM25 · denso · híbrido · híbrido + GraphSAGE, con el control sin grafo al lado.
- Correr los escenarios con y sin GNN (`SHOPPING_AGENT_RERANKER=control|sage`) y, como referencia, sin reranker (`off`).
- Fecha oficial de entrega.
