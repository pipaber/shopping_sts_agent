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
| TTS | XTTS-v2 (`coqui-tts` 0.28) con grabación de referencia propia | Español nativo, clona con ~10 s, ~2–3 GB. Se usa bajo la licencia CPML de Coqui, que solo permite uso no comercial (este trabajo es académico); cada persona que lo ejecuta la acepta de forma explícita en su `.env` |
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

pgvector no hace falta por ahora: el Store solo guarda las preferencias del usuario por clave, sin búsqueda semántica. En local se usa un contenedor `postgres:16-alpine` (ver README). Postgres es obligatorio: sin `SHOPPING_AGENT_PG_URL` los comandos se detienen con un error, para no perder la persistencia sin notarlo (por ejemplo en Colab). La memoria volátil solo se usa si se pide de forma explícita (`--memoria-volatil` u `open_memory(volatile=True)`) y queda anotada en la transcripción.

`llama-cpp-python` en Colab: hay que instalarlo con CUDA (`CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python`). En la workstation la compilación tardó unos 20 minutos; en Colab conviene medirlo el día 7 y, si es demasiado, usar una rueda precompilada para la versión de CUDA de la sesión.

Presupuesto de VRAM con todo cargado: LLM 5,2 GB (medido) + embeddings 0,6 GB (medido) + Whisper 2,2 GB (medido por separado) + XTTS ~3 GB (estimado, pendiente de medir) ≈ 11 GB de 15 GB utilizables. Las medidas por separado incluyen cada una el contexto de CUDA, que en un solo proceso se comparte, así que el total real debería ser algo menor. Si no cabe, los embeddings de consulta pasan a CPU.

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
- **Orden de los candidatos.** La búsqueda es el híbrido BM25 + denso con RRF (top 50). De los 20 primeros se muestran antes los que se pueden comprar (con existencias y dentro de lo que queda de presupuesto) y se enseñan 5 con sus campos del catálogo; los ausentes se muestran como "desconocido".
- **Respuestas.** El texto lo redacta el LLM, pero el contenido del carrito, la cotización, el pedido y las alternativas por falta de stock los escribe el código. Cuando el carrito o el presupuesto cambian, el código añade a la respuesta el carrito exacto y lo que queda de presupuesto.
- **Validación de la respuesta.** Antes de enviarla, el código comprueba que toda cifra del texto del LLM aparece en los datos que tuvo delante y que no da por hecho un pedido inexistente; si falla, la respuesta vuelve al LLM con el motivo. Es una comprobación global: no detecta una cifra real atribuida al producto equivocado.
- **Confirmación.** Solo cuenta como sí una respuesta que no dice nada más ("sí", "vale, confirmo"). "No" cancela sin tocar el carrito. Cualquier otra cosa ("sí, pero que sean tres") no compra y se atiende como un turno nuevo; cualquier cambio en el carrito o el presupuesto invalida la cotización.
- **Confirmación repetida.** Un "sí" justo después de registrar el pedido vuelve a confirmar la misma cotización, que es idempotente, y el agente contesta que ya estaba registrado.
- **Cambios entre cotización y confirmación.** La transacción rechaza el pedido si cambió el stock, el precio o el carrito. Con stock insuficiente el agente ofrece la cantidad disponible y hasta tres productos parecidos con existencias suficientes y dentro del presupuesto; el carrito no se modifica hasta que el usuario decide.
- **Historial.** No se resume con el LLM: se envían los 8 últimos mensajes.

Mediciones en la workstation (RTX A2000 12 GB) con las transcripciones de `results/chat_*.json`: 2,5–9,5 s por turno (media 5–6 s; cada turno son de 1 a 3 decisiones de unos 2,7 s), 1 185 tokens/s al evaluar el prompt y 50 tokens/s al generar. La confirmación y el registro del pedido no usan el LLM (0,04 s). Carga inicial: 20 s para el catálogo, el índice BM25 y el modelo de embeddings.

Limitaciones observadas con el modelo de 7B: es sensible a la redacción del prompt (se ajustó solo con diálogos propios, nunca con consultas de `test`); a veces redacta mal un cambio ("añadidas dos más" cuando pasó de dos a tres) aunque la operación y el resumen del código sean correctos, y puede necesitar un paso de más para leer el detalle de un producto.

### Decisiones de diseño de la voz (día 7)

- **El agente no cambia.** La voz se monta alrededor de la conversación por texto: ASR antes y TTS después (`voice/pipeline.py`). El grafo no se tocó; la sesión solo mide además cuánto tarda cada nodo.
- **Latencia.** Va desde que el audio del usuario está disponible hasta que la respuesta puede reproducirse, y se reparte en ASR, recuperación (nodos `recuperar` y `proponer_alternativa`), LLM (nodo `interpretar`), herramientas (el resto de nodos, con sus checkpoints) y TTS. La carga de los modelos se mide aparte. También se anota cuándo estaría listo el primer fragmento de audio, por si más adelante se reproduce mientras se sintetiza el resto.
- **Silencio.** Whisper large-v3-turbo transcribe el silencio o el ruido como "Gracias por ver el vídeo" y su probabilidad de no-voz no lo detecta. Se activa el filtro de voz de `faster-whisper` (Silero VAD, en CPU): sin voz, la transcripción queda vacía y el agente pide que se repita.
- **Texto para el TTS.** Antes de sintetizar, los importes y cantidades pasan a palabras con su concordancia ("7,74 €" → "siete euros con setenta y cuatro céntimos", "1 unidad" → "una unidad"), se quitan identificadores y símbolos y los títulos de catálogo se acortan a su primera parte. La transcripción guarda el texto original del agente y, aparte, lo que se envió al TTS.
- **Fragmentos.** XTTS-v2 recorta las frases de más de 239 caracteres en español: el texto se parte por frases (y por comas si hace falta) en trozos de hasta 200 caracteres, que se sintetizan uno a uno y se unen con una pausa corta. La semilla del muestreo se fija para que la misma entrada dé la misma salida.
- **Voz.** Sale de `audio/referencia/referencia.wav` (o de `SHOPPING_AGENT_VOICE_REF`). Mientras no exista, el desarrollo usa un hablante incluido en XTTS-v2, elegido de forma explícita; nunca la voz de otra persona. La carpeta `audio/` y cualquier archivo de audio están fuera de git.
- **Repetición con el texto correcto.** Como cada turno cambia el carrito y la tienda, no se repite un turno suelto: se repite la conversación entera desde la misma tienda inicial, en otro hilo, dando al agente el texto correcto en lugar del audio. Se compara turno a turno si el ASR cambió el texto, si el agente hizo operaciones distintas y si el estado final de la tienda coincide.
- **Métricas.** WER con `jiwer` tras normalizar los dos textos (cifras en palabras, minúsculas, sin tildes ni puntuación), para que "60 €" y "sesenta euros" cuenten como lo mismo. Importes y cantidades se extraen de ambos textos y se comparan como conjuntos con repetición; "un" y "una" sueltos son artículos y no cuentan. Los nombres de producto esperados en cada turno (incluidos "el primero", "el segundo"…) se dan en `scenarios/<escenario>.terminos.json`. La semejanza de hablante se mide con ECAPA-TDNN de SpeechBrain, un modelo distinto del codificador de XTTS-v2, en CPU.
- **Dependencias.** `coqui-tts` 0.28 funciona con PyTorch 2.14 sin cambiarlo. `torchaudio` y `torchcodec` se toman del índice de PyTorch para CUDA 12.6 (las ruedas de PyPI están compiladas para CUDA 13 y no cargan) y `torchcodec` necesita FFmpeg en el sistema; en Colab habrá que usar el índice que corresponda a su versión de CUDA.

## 4. Datos

- Filtro: `product_locale == "es"` y `small_version == 1`.
- Consultas: ~300 de `test` para evaluación y ~1 500 de `train` para desarrollo, separadas por `query_id`.
- Catálogo: todos los productos anotados de esas consultas (≥ 5 000), con título, descripción, viñetas, marca, color e identificador.
- Tienda simulada: precios y stock generados con semilla fija; instantánea `store_seed.sqlite` que se copia para restaurar.

## 5. Recuperación y GNN

1. **Baseline léxico:** BM25 sobre título + marca + viñetas + descripción.
2. **Denso:** embeddings multilingües del mismo texto, índice FAISS.
3. **Fusión:** RRF de ambos, top 50.
4. **Reranker GraphSAGE (PyTorch Geometric):** grafo bipartito consulta–producto con las aristas ESCI de `train` (peso según etiqueta), más aristas producto–producto por marca y vecinos cercanos para que ningún producto quede aislado. Features de nodo: embeddings de texto. Pérdida por pares (BPR). Una consulta nueva entra de forma inductiva conectándose a sus candidatos de la etapa 3, sin etiquetas.
5. **Métrica:** nDCG@10 sobre candidatos anotados con ganancias 1 / 0,1 / 0,01 / 0.

Comparación a reportar con las mismas consultas de `test`: BM25 · denso · híbrido · híbrido + GraphSAGE (ablación: con y sin GNN).

Riesgo principal: que el GNN no supere al híbrido. El resultado se reporta igual; la ablación sigue siendo válida y el sistema funciona sin él.

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
  retrieval/   bm25, denso, fusión, gnn, métricas
  store/       esquema SQLite, transacciones, restauración
  agent/       estado, nodos, herramientas, validaciones, grafo
  voice/       audio, asr, texto para voz, tts, turno completo
  eval/        recuperación, métricas de voz; escenarios y runner (pendiente)
notebooks/     lab4_colab.ipynb (ejecución principal)
scenarios/     20 JSON + audios
tests/
```

Dependencias a añadir: `langgraph-checkpoint-postgres`, `psycopg[binary,pool]`, `faiss-cpu`, `bm25s`, `faster-whisper`, `llama-cpp-python`, `coqui-tts`, `torch-geometric`, `jiwer`, `speechbrain`.

## 9. Pendientes por decidir

- Modelo exacto de embeddings (por ahora `intfloat/multilingual-e5-small`). El LLM ya está elegido: Qwen2.5-7B-Instruct Q4_K_M.
- Comprobar en Colab la instalación de Postgres, de `llama-cpp-python` con CUDA y de las dependencias de voz (`torchaudio`, `torchcodec`, FFmpeg).
- Ejecutar XTTS-v2 con el modelo real: corrida por voz de extremo a extremo, VRAM con los cuatro modelos cargados, WER y semejanza.
- Grabar la voz de referencia (`audio/referencia/referencia.wav`) y los audios de los escenarios (`audio/escenarios/<escenario>/NN.wav`); el README dice cómo. La voz debe ser propia o autorizada, y los textos sintetizados distintos de los de la grabación.
- Fecha oficial de entrega.
