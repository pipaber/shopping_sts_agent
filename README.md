# Asistente de compras por voz (Laboratorio 4)

Asistente que recibe consultas habladas en español, recupera productos de un catálogo (ESCI), opera sobre una tienda simulada y responde con voz clonada. Todo el procesamiento de modelos es local.

El diseño y el cronograma están en [documentation/PLAN.md](documentation/PLAN.md).

## Entorno

Requiere [uv](https://docs.astral.sh/uv/) y Python 3.11. PyTorch se instala con CUDA 12.6 en Windows y Linux.

```bash
uv sync
```

### Configuración local

Lo que depende de la máquina (rutas, credenciales) va en un archivo `.env` en la raíz del repo, que no se versiona. El paquete lo lee al importarse y no pisa las variables ya definidas en el entorno. [.env.example](.env.example) lista las variables disponibles:

```bash
cp .env.example .env
```

Los modelos (embeddings, LLM, Whisper y XTTS-v2) se descargan en la caché de Hugging Face. Si el disco del sistema tiene poco espacio, `HF_HOME` en el `.env` la lleva a otro disco; ocupa unos 9 GB.

## Datos

Descarga ESCI (~1,2 GB), arma el catálogo y las consultas, y genera la tienda simulada. Todo es determinista (semilla 42).

```bash
uv run python -m shopping_agent.data.download
uv run python -m shopping_agent.data.prepare
uv run python -m shopping_agent.store.db
```

Salidas en `datasets/processed/`: `catalog.parquet`, `queries_{train,test}.parquet`, `qrels_{train,test}.parquet`, `store_seed.sqlite` y `store.sqlite`. Para devolver la tienda a su estado inicial se repite el último comando.

## Recuperación

Compara BM25, denso e híbrido con nDCG@10 sobre los candidatos anotados. `test` se reserva para la evaluación final.

```bash
uv run python -m shopping_agent.eval.retrieval --split train
```

## Reranker (GraphSAGE)

Segunda etapa opcional de la búsqueda: una GNN (GraphSAGE, con PyTorch Geometric) reordena los 50 primeros del híbrido sobre un grafo de consultas y productos. Es el componente de la ablación: el agente se puede correr con y sin él. El diseño, las decisiones y las limitaciones están en [documentation/PLAN.md](documentation/PLAN.md) ("Diseño y resultados del reranker").

Las 1 500 consultas de `train` se reparten con semilla fija en 1 200 de ajuste y 300 de validación; las de `test` no se leen en ningún paso.

```bash
uv run python -m shopping_agent.retrieval.train --variant sage --seed 0
```

Entrena con las consultas de ajuste y guarda los pesos y el grafo en `datasets/processed/reranker.pt` (13 MB, fuera de git; se regenera con este comando en unos 3 minutos). Imprime el nDCG@10 de validación del modelo guardado. La misma semilla lo reproduce con una diferencia de hasta ±0,0005, por operaciones de GPU que no son deterministas. `--variant` admite las variantes de la comparación: `sage` (la del agente), `control` (el mismo modelo sin grafo), `sage_exact` (con aristas de etiquetas de ajuste), `gatv2`…

```bash
uv run python -m shopping_agent.eval.reranker --seeds 5
```

Compara en validación los modelos base, el control sin grafo y cada variante con 5 semillas (unos 15 minutos en GPU), y escribe [results/reranker_validation.md](results/reranker_validation.md) y su `.json`. Resumen (nDCG@10 sobre candidatos anotados, media ± desviación entre semillas):

| Sistema | nDCG@10 en validación |
|---|---|
| BM25 (base léxica) | 0,6750 |
| Denso | 0,7535 |
| Híbrido RRF | 0,7403 |
| Control sin grafo (mismo modelo, sin paso de mensajes) | 0,7582 ± 0,0005 |
| GraphSAGE | 0,7619 ± 0,0009 |
| GraphSAGE con aristas de etiquetas | 0,7631 ± 0,0015 |

Reordenar mejora al híbrido en +0,022, pero casi toda la mejora la da ya el control sin grafo: el paso de mensajes añade +0,004 (IC 95 % [+0,0004; +0,0073]), una diferencia pequeña y sensible al número de épocas. Las aristas con etiquetas no aportan nada medible y el modelo del agente no las usa.

```bash
uv run python -m shopping_agent.eval.reranker_cost
```

Mide el coste en la búsqueda ([results/reranker_cost.json](results/reranker_cost.json)): +10 ms por consulta en GPU (+124 ms en CPU) y 230 MiB más de VRAM.

**Interruptor.** El agente usa el reranker por defecto. `SHOPPING_AGENT_RERANKER=off` (en el entorno o en el `.env`) deja la búsqueda en el híbrido; las transcripciones anotan cuál se usó. Con el reranker activado hacen falta los pesos: si no están, el agente se detiene con un mensaje que dice cómo generarlos.

```bash
SHOPPING_AGENT_RERANKER=off uv run python -m shopping_agent.agent.chat --script scenarios/demo_compra.txt --restore --out results/chat_compra_sin_gnn
```

Las transcripciones que ya estaban en `results/` (`chat_*` y `voz_*`) se hicieron antes de que existiera el reranker, con la búsqueda híbrida sola.

## Memoria del agente (Postgres)

Los checkpoints de la conversación (`PostgresSaver`) y la memoria entre conversaciones (`PostgresStore`) se guardan en Postgres. La conexión se lee de `SHOPPING_AGENT_PG_URL` y las tablas se crean solas la primera vez. Postgres es obligatorio: sin esa variable los comandos se detienen con un error que lo explica, para no quedarse sin persistencia sin notarlo. Para trabajar a propósito sin Postgres hay que pedirlo con la opción `--volatile-memory` (en código, `open_memory(volatile=True)`); la transcripción deja anotado qué memoria se usó.

Lo más sencillo es un contenedor, que no necesita permisos de administrador ni toca otros Postgres de la máquina:

```bash
docker run -d --name shopping-agent-pg --restart unless-stopped -e POSTGRES_USER=shopping_agent -e POSTGRES_PASSWORD=CAMBIA_ESTA_CLAVE -e POSTGRES_DB=shopping_agent -p 127.0.0.1:5544:5432 -v shopping_agent_pg:/var/lib/postgresql/data postgres:16-alpine
```

y en el `.env`:

```
SHOPPING_AGENT_PG_URL=postgresql://shopping_agent:CAMBIA_ESTA_CLAVE@127.0.0.1:5544/shopping_agent
```

Con un Postgres ya instalado basta crear un usuario y una base (`CREATE USER shopping_agent WITH PASSWORD '…'` y `createdb -O shopping_agent shopping_agent`) y apuntar la variable a ellos.

## LLM local

El agente usa un Qwen instruct en GGUF servido con `llama-cpp-python`, que `uv sync` compila desde el código fuente. Para que use la GPU hay que compilarlo con CUDA (hacen falta el toolkit de CUDA y un compilador de C++):

```bash
CMAKE_ARGS="-DGGML_CUDA=on" uv sync
```

Si `nvcc` no está en el `PATH`, se añade `CUDACXX=/usr/local/cuda/bin/nvcc` delante. Si ya se instaló sin CUDA, se recompila con `CMAKE_ARGS="-DGGML_CUDA=on" uv sync --reinstall-package llama-cpp-python`. La compilación tarda unos 20 minutos.

El modelo (unos 4,7 GB) se descarga solo la primera vez en la caché de Hugging Face. Para usar otro, ver las variables `SHOPPING_AGENT_LLM_*` en [.env.example](.env.example).

## Agente por texto

Conversación por turnos con el agente (grafo de LangGraph, tienda en SQLite, LLM local). Antes de registrar un pedido repite productos, cantidades e importes y espera un sí.

```bash
uv run python -m shopping_agent.agent.chat
```

Con un guion (un mensaje de usuario por línea) se reproduce una conversación y se guarda la transcripción, con las operaciones ejecutadas y el estado final de la tienda:

```bash
uv run python -m shopping_agent.agent.chat --script scenarios/demo_compra.txt --restore --out results/chat_compra
```

`--restore` devuelve antes la tienda a su estado inicial y `--thread` reanuda una conversación guardada. En `results/` están las transcripciones de dos corridas: [chat_compra.md](results/chat_compra.md) y [chat_incidencias.md](results/chat_incidencias.md).

## Voz

Alrededor del agente por texto hay un reconocedor de voz antes y un sintetizador después; todo corre en local.

| Etapa | Modelo | Paquete | Licencia |
|---|---|---|---|
| ASR | Whisper large-v3-turbo, español fijo | `faster-whisper` | MIT |
| TTS con clonación | XTTS-v2 | `coqui-tts` | **CPML de Coqui: solo uso no comercial** |
| Semejanza de hablante (solo evaluación) | ECAPA-TDNN (`speechbrain/spkrec-ecapa-voxceleb`) | `speechbrain` | Apache 2.0 |

`torchaudio` y `torchcodec` se instalan desde el mismo índice de PyTorch que `torch` (CUDA 12.6); `torchcodec` necesita además las bibliotecas de FFmpeg del sistema (`apt install ffmpeg`).

### Licencia de XTTS-v2

XTTS-v2 se usa bajo la [CPML de Coqui](https://tts-hub.github.io/cpml), que solo permite uso no comercial; este proyecto es académico. El modelo no se descarga hasta que quien lo ejecuta acepta esa licencia: o bien añade `COQUI_TOS_AGREED=1` a su `.env`, o bien lanza el comando en una terminal y responde a la pregunta de Coqui. El repositorio no la acepta por nadie: la variable está en [.env.example](.env.example) comentada.

### Grabaciones

La voz es un dato personal: la carpeta `audio/` y cualquier archivo de audio están en `.gitignore` y no se suben.

```
audio/
  referencia/referencia.wav        voz que clona el agente
  escenarios/<escenario>/01.wav    lo que dice el usuario en el turno 1 de ese escenario
  escenarios/<escenario>/02.wav    turno 2, etc.
```

**Voz de referencia** (`audio/referencia/referencia.wav`; otra ruta con `SHOPPING_AGENT_VOICE_REF`). Debe ser propia o de alguien que la haya autorizado.

- Entre 15 y 30 segundos de habla continua en español, con tu voz normal. XTTS-v2 usa como mucho los primeros 30 segundos.
- Un texto cualquiera que no sea ninguna respuesta del agente (por ejemplo, un párrafo de un libro): lo que se sintetiza después tiene que ser distinto de lo grabado.
- Sitio silencioso, sin música ni eco, a un palmo del micrófono y sin saturar.
- WAV, mono o estéreo, a cualquier frecuencia de muestreo (mejor 44,1 o 48 kHz y 16 bits); el código lo convierte a lo que necesita cada modelo.

**Audios de un escenario** (`audio/escenarios/<escenario>/`). Un archivo por turno del usuario, numerado con dos cifras en el orden de la conversación. El texto de cada turno es la línea correspondiente de `scenarios/<escenario>.txt`: la línea 1 se graba en `01.wav`, la 2 en `02.wav`, y así. Hay que decir el texto tal cual, porque ese archivo es la transcripción correcta con la que se compara el ASR.

- Un turno por archivo, de 1 a 15 segundos, sin silencios largos al principio ni al final.
- WAV (también se leen FLAC, MP3, OGG y M4A), mono o estéreo, a 16 kHz o más.

Por ahora hay dos guiones para grabar: [scenarios/demo_compra.txt](scenarios/demo_compra.txt) (8 turnos) y [scenarios/demo_incidencias.txt](scenarios/demo_incidencias.txt) (10 turnos). Los seis escenarios de la evaluación final seguirán la misma convención. Por ejemplo, para `demo_compra`:

| Archivo | Texto que hay que decir |
|---|---|
| `audio/escenarios/demo_compra/01.wav` | Hola, busco unos auriculares bluetooth para hacer deporte. Tengo un presupuesto de 60 euros. |
| `…/02.wav` | ¿De qué color es el segundo y cuánto le dura la batería? |
| `…/03.wav` | Compárame el primero con el tercero. |
| `…/04.wav` | Añade dos del primero al carrito. |
| `…/05.wav` | Mejor que sean tres. |
| `…/06.wav` | Vale, pues quiero cerrar el pedido. |
| `…/07.wav` | Sí, confirmo. |
| `…/08.wav` | Sí. |

### Conversación por voz

```bash
uv run python -m shopping_agent.voice.chat --scenario demo_compra --mode both --restore
```

Cada turno hace audio → ASR → agente → TTS → audio. En `results/voz_demo_compra/` quedan `turnos.json` y `transcripcion.md` con la transcripción del ASR, las operaciones, el texto de la respuesta, el texto enviado al TTS y los tiempos por etapa (ASR, recuperación, LLM, herramientas, TTS), con la carga inicial de los modelos aparte; los audios de entrada y de respuesta se guardan en la misma carpeta, fuera de git. Con `--mode both` la conversación se repite después con el texto correcto en lugar del audio, para separar los errores del ASR de los del agente; `--mode text` hace solo esa parte.

Antes de sintetizar, la respuesta se pasa a una forma apta para voz (importes y cantidades en palabras, sin identificadores ni símbolos, títulos de catálogo acortados). La transcripción conserva el texto original.

Mientras no haya grabación de referencia se puede probar con un hablante incluido en XTTS-v2 (`--speaker`, lista con `uv run python -m shopping_agent.voice.tts --list-speakers`), y generar audios de entrada sintéticos a partir de un guion:

```bash
uv run python -m shopping_agent.voice.tts --speaker "NOMBRE" --script scenarios/demo_compra.txt --out-dir audio/sinteticos/demo_compra
```

Los audios sintéticos sirven para comprobar que el flujo funciona, no para evaluar el ASR. En `results/` hay dos corridas hechas con esos audios de entrada: [voz_demo_compra](results/voz_demo_compra/transcripcion.md), en la que el agente clona un hablante de prueba ([métricas](results/voz_demo_compra/metricas.md)), y [voz_demo_compra_voz_usuario](results/voz_demo_compra_voz_usuario/transcripcion.md), en la que clona la grabación de referencia del autor ([métricas](results/voz_demo_compra_voz_usuario/metricas.md)). Los audios de entrada y de respuesta no se suben.

### Métricas de voz

```bash
uv run python -m shopping_agent.eval.voice results/voz_demo_compra
```

Calcula, sobre una corrida guardada: la inteligibilidad (WER de Whisper sobre el audio sintetizado frente al texto enviado al TTS), la semejanza con la referencia (coseno entre embeddings de hablante) y los errores del ASR en importes, cantidades y nombres de producto frente al texto correcto. Los nombres de producto esperados en cada turno se indican en `scenarios/<escenario>.terminos.json`.

## Organización del código

```
src/shopping_agent/
  data/        preparación de ESCI y de la tienda simulada
  retrieval/   BM25, denso, fusión RRF y métricas
    dev_data.py, first_stage.py   consultas de ajuste y validación; señales de la primera etapa
    graph.py, gnn.py              grafo consulta–producto; modelo GraphSAGE y su pérdida
    train.py, reranker.py         entrenamiento; reranker ya entrenado, para el agente
  store/       esquema SQLite, operaciones con validación y restauración
  agent/
    state.py     estado de la conversación, con un valor por defecto en cada campo
    tools.py     registro de herramientas: descripción, esquema, validación y función de cada una
    prompt.py    lo que ve el LLM (reglas, estado, resultados)
    texts.py     lo que el código le dice al usuario
    guards.py    comprobaciones sobre texto libre: confirmación y respuesta del LLM
    deps.py      lo que los nodos necesitan de fuera (LLM, búsqueda, tienda, Store)
    nodes/       los nodos del grafo: turn (conversación), actions (acciones), checkout (cierre)
    graph.py     el cableado del grafo: a dónde puede ir cada nodo
    session.py   un mensaje entra, una respuesta sale
    chat.py, report.py   comando de chat por texto y transcripción
    memory.py, llm.py, search.py   Postgres, LLM local y búsqueda híbrida con reranker opcional
  voice/       audio, asr, speech_text, tts, pipeline (un turno por voz), chat (comando), report
  eval/        evaluación de la recuperación, del reranker (comparación y coste) y métricas de voz
```

Criterio de idioma: los identificadores del código (módulos, funciones, clases, variables, campos, claves de los JSON de resultados y opciones de los comandos) van en inglés. Va en español todo lo que es lenguaje: los textos para el usuario y para el LLM, los comentarios y la documentación, y los nombres que el LLM o las transcripciones muestran (nodos del grafo, herramientas y sus argumentos, códigos de rechazo). La función que implementa un nodo se llama como el nodo. Los archivos de resultados y de escenarios, que son contenido, también van en español.

## Pruebas

Las pruebas no necesitan GPU, modelos ni grabaciones: el grafo del agente se prueba con un LLM guionizado, el canal de voz con un ASR y un TTS simulados, y el reranker con un grafo sintético de doce productos. Las que no tratan de Postgres usan memoria volátil pedida de forma explícita; las de Postgres se omiten si `SHOPPING_AGENT_PG_URL` no está definida o el servidor no responde.

```bash
uv run pytest
```

## Uso de IA

Parte del código y la documentación se elaboró con asistencia de IA generativa (Claude Code) y fue revisado por el autor.
