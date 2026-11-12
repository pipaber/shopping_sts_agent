# Asistente de compras por voz (Laboratorio 4)

Asistente que recibe consultas habladas en español, recupera productos de un catálogo (ESCI), opera sobre una tienda simulada y responde con voz clonada. Todo el procesamiento de modelos es local.

El diseño y el cronograma están en [documentation/PLAN.md](documentation/PLAN.md).

## Cómo funciona

El recorrido de los datos, de la voz del usuario al pedido registrado y a la respuesta hablada, está en una página animada: [documentation/flujo.html](documentation/flujo.html). GitHub muestra su código, no la página: para verla hay que abrir el archivo en un navegador (con el repositorio clonado, `documentation/flujo.html`). Recorre paso a paso tres turnos reales (buscar, añadir al carrito y confirmar), por voz o por texto.

[![Flujo de un turno: usuario, ASR, agente, búsqueda, tienda, memoria y TTS](documentation/flujo.png)](documentation/flujo.html)

El mismo flujo, resumido:

```mermaid
flowchart LR
    U(["Usuario"]) -- "audio" --> ASR["ASR<br/>Whisper large-v3-turbo"]
    ASR -- "texto" --> LLM
    U -. "por texto" .-> LLM
    subgraph AG["Agente (LangGraph)"]
        LLM["El LLM propone un paso<br/>Qwen2.5-7B"] --> COD["El código valida y ejecuta"]
        COD -- "resultado" --> LLM
        LLM --> R["Respuesta<br/>texto con cifras comprobadas"]
    end
    COD <--> B[("Búsqueda<br/>BM25 + denso, RRF, reranker<br/>catálogo ESCI")]
    COD <--> T[("Tienda simulada<br/>SQLite")]
    COD -.-> M[("Memoria<br/>Postgres")]
    R -- "texto" --> TTS["TTS<br/>XTTS-v2, voz clonada"]
    TTS -- "audio" --> S(["Respuesta"])
    R -. "por texto" .-> S
```

- **Caso de uso.** Comprar hablando en español: buscar un producto con un presupuesto, añadirlo al carrito, corregir la cantidad y cerrar el pedido. El agente repite el pedido antes de registrarlo y solo compra con un sí.
- **Voz o texto.** Las dos. El agente es el mismo; por voz lleva un reconocedor delante (ASR) y un sintetizador detrás (TTS), y por texto se saltan esas dos etapas.
- **Función del agente.** El LLM propone una herramienta por paso y redacta la respuesta; el código valida cada llamada, comprueba existencias y presupuesto en la tienda, verifica las cifras de la respuesta y es el único que registra pedidos.
- **Qué se toma de ESCI.** La versión reducida, solo en español: 43 674 productos (título, descripción, características, marca y color) forman el catálogo en el que busca el agente. Las consultas y sus etiquetas (1 500 de `train` y 300 de `test`) solo sirven para entrenar el reranker y para medir: el agente no las lee. Precios y existencias no vienen en ESCI: son ficticios, generados con semilla.
- **Modelos, todos locales.** Whisper large-v3-turbo, Qwen2.5-7B-Instruct (GGUF Q4_K_M), XTTS-v2 y `multilingual-e5-small`, más un reranker entrenado aquí.
- **Hardware.** Medido en una estación de trabajo con una NVIDIA RTX A2000 de 12 GB (9 532 MiB de memoria de GPU con todo cargado). El objetivo del enunciado es Google Colab con una T4: [notebooks/colab.ipynb](notebooks/colab.ipynb).

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

Compara BM25, denso e híbrido con nDCG@10 sobre los candidatos anotados, con las consultas de `train`. La evaluación final con `test` es otro comando y se hizo una sola vez (ver "Recuperación en test").

```bash
uv run python -m shopping_agent.eval.retrieval --split train
```

## Reranker (control sin grafo y GraphSAGE)

Segunda etapa de la búsqueda: un modelo entrenado reordena los 50 primeros del híbrido. Hay dos versiones que solo se diferencian en el paso de mensajes: GraphSAGE (una GNN sobre un grafo heterogéneo de consultas y productos, hecho con `HeteroData` y `HeteroConv` de PyTorch Geometric) y su control sin grafo. El GNN es el componente de la ablación: el agente se puede correr con uno, con otro o sin reranker. El diseño, las decisiones y las limitaciones están en [documentation/PLAN.md](documentation/PLAN.md) ("Diseño y resultados del reranker").

Las 1 500 consultas de `train` se reparten con semilla fija en 1 200 de ajuste y 300 de validación; las de `test` no se leen en ningún paso.

```bash
uv run python -m shopping_agent.retrieval.train --variant control --seed 0
```

Entrena con las consultas de ajuste y guarda los pesos y el grafo en `datasets/processed/reranker_<variante>.v2.pt` (13 MB, fuera de git; se regenera con este comando en unos 3 minutos). Imprime el nDCG@10 de validación del modelo guardado. Con la misma semilla el control se reproduce exactamente; GraphSAGE varía hasta ±0,002 entre corridas, por operaciones de GPU que no son deterministas. `--variant` admite las variantes de la comparación: `control` (el mismo modelo sin grafo; es la que usa el agente por defecto), `sage` (GraphSAGE), `sage_exact` (con aristas de etiquetas de ajuste), `gatv2`… Para la ablación hay que entrenar también `--variant sage`.

```bash
uv run python -m shopping_agent.eval.reranker --seeds 5
```

Compara en validación los modelos base, el control sin grafo y cada variante con 5 semillas (unos 15 minutos en GPU), y escribe [results/reranker_validation.md](results/reranker_validation.md) y su `.json`. Resumen (nDCG@10 sobre candidatos anotados, media ± desviación entre semillas):

| Sistema | nDCG@10 en validación |
|---|---|
| BM25 (base léxica) | 0,6750 |
| Denso | 0,7535 |
| Híbrido RRF | 0,7403 |
| Control sin grafo (mismo modelo, sin paso de mensajes; el del agente por defecto) | 0,7582 ± 0,0005 |
| GraphSAGE | 0,7617 ± 0,0006 |
| GraphSAGE con aristas de etiquetas | 0,7628 ± 0,0017 |

Reordenar mejora al híbrido en +0,018 con el control y +0,021 con GraphSAGE: el paso de mensajes añade +0,0035 (IC 95 % [−0,0001; +0,0073]), una diferencia pequeña, en el límite del ruido y sensible al número de épocas, y en la lista sobre todo el catálogo los dos rinden igual. Las aristas con etiquetas no aportan nada medible y ninguno de los dos las usa.

```bash
uv run python -m shopping_agent.eval.reranker_cost --variant control
```

Mide el coste en la búsqueda. Con el [control](results/reranker_cost_control.json): +2 ms por consulta en GPU (+89 ms en CPU) y 102 MiB más de VRAM. Con [GraphSAGE](results/reranker_cost_sage.json) (`--variant sage`): +12 ms (+127 ms en CPU) y 230 MiB más.

**Interruptor.** `SHOPPING_AGENT_RERANKER` (en el entorno o en el `.env`) elige qué reordena la búsqueda del agente: `control` (por defecto), `sage` (GraphSAGE), otra variante entrenada u `off` (el híbrido solo). Las transcripciones anotan cuál se usó. Hacen falta los pesos de la variante elegida: si no están, el agente se detiene con un mensaje que dice cómo generarlos. La ablación del GNN es `control` frente a `sage`:

```bash
SHOPPING_AGENT_RERANKER=sage uv run python -m shopping_agent.agent.chat --script scenarios/demo_compra.txt --restore --out results/chat_compra_gnn
```

Las transcripciones de demostración de `results/` (`chat_*` y `voz_demo_*`) se regeneraron con el reranker por defecto (`control`); cada una anota la búsqueda que usó. Las anteriores, hechas con la búsqueda híbrida sola, quedan en el historial de git.

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

**Audios de un escenario** (`audio/escenarios/<escenario>/`). Un archivo por turno del usuario, numerado con dos cifras en el orden de la conversación: el turno 1 se graba en `01.wav`, el 2 en `02.wav`, y así. Hay que decir el texto tal cual, porque es la transcripción correcta con la que se compara el ASR.

- Un turno por archivo, de 1 a 15 segundos, sin silencios largos al principio ni al final.
- WAV (también se leen FLAC, MP3, OGG y M4A), mono o estéreo, a 16 kHz o más.

**Qué hay que grabar para la evaluación.** Los seis escenarios de voz: 31 turnos en total. El guion, con el archivo y el texto exacto de cada turno, está en [scenarios/evaluacion/GUION_GRABACION.md](scenarios/evaluacion/GUION_GRABACION.md); se genera a partir de los escenarios y no se edita a mano. Cada escenario va en su carpeta (`audio/escenarios/01_compra_confirmada/01.wav`, `02.wav`…). Mientras falte algún archivo de un escenario, la evaluación usa para ese escenario los audios sintéticos de prueba y lo deja anotado en los resultados.

Para comprobar las grabaciones antes de correr el agente:

```bash
uv run python -m shopping_agent.eval.recordings
```

Transcribe cada archivo con el ASR del agente y lo compara con el texto de su turno ([results/escenarios/grabaciones.md](results/escenarios/grabaciones.md)): dice qué archivos faltan, qué se entendió en cada uno y cuáles se parecen más al texto de otro turno (un archivo mal numerado). No modifica los audios.

Los dos guiones de demostración siguen la misma convención, con el texto en un archivo de líneas: [scenarios/demo_compra.txt](scenarios/demo_compra.txt) (8 turnos) y [scenarios/demo_incidencias.txt](scenarios/demo_incidencias.txt) (10 turnos). Por ejemplo, para `demo_compra`:

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

## Evaluación

Qué se midió, con qué decisiones y qué quedó sin verificar está en [documentation/PLAN.md](documentation/PLAN.md) ("Diseño y resultados de la evaluación"). Aquí, cómo se reproduce cada tabla.

### Escenarios

Hay veinte escenarios en [scenarios/evaluacion/](scenarios/evaluacion/), uno por archivo JSON. Seis son además de voz, uno por cada situación obligatoria del enunciado. Cada escenario declara los turnos del usuario, los sucesos externos entre turnos y lo que se espera:

```json
{"say": "Añade dos de la primera al carrito.", "terms": ["primera"],
 "expect": [{"check": "cart", "lines": [{"product": "@elegida", "quantity": 2}]}, {"check": "orders", "count": 0}]},
{"remember": {"elegida": "candidate:1"}},
{"event": "set_offer", "product": "@elegida", "price_cents": 1450, "stock": 20}
```

- **Productos por posición, no por identificador.** `candidate:N` y `cart:N` son el candidato o la línea de carrito N en ese momento; `remember` les pone nombre para usarlo después. El escenario no depende de qué producto devuelva la búsqueda.
- **Condiciones fijadas por regla.** El precio y las existencias de los que depende el resultado los fija un suceso de la tienda (`set_offer`), no la suerte de la semilla. El mismo suceso sirve para cambiar el stock entre la cotización y la confirmación.
- **Estado inicial reproducible.** Cada escenario empieza con la tienda restaurada desde `store_seed.sqlite` (en una copia propia de la corrida), un hilo nuevo y un usuario nuevo, es decir, sin memoria previa. `new_conversation` abre otro hilo del mismo usuario.
- **Veredicto por código.** Un escenario es correcto si se cumplen todas sus comprobaciones (pedidos y sus líneas, carrito, inventario, presupuesto, si pidió aclaración, si propuso una alternativa…), no hay ninguna violación de restricciones y la corrida no dio error. Ningún LLM juzga nada. Las comprobaciones están en `eval/scenario_checks.py`.
- **Violaciones de restricciones.** Aparte de lo que espere cada escenario, se compara la tienda antes y después de cada turno para contar cinco clases: cantidad, presupuesto, existencias, pedido duplicado y cambio parcial (`eval/scenario_violations.py`).

```bash
uv run python -m shopping_agent.eval.scenarios --mode text
SHOPPING_AGENT_RERANKER=sage uv run python -m shopping_agent.eval.scenarios --mode text
SHOPPING_AGENT_RERANKER=off uv run python -m shopping_agent.eval.scenarios --mode text
uv run python -m shopping_agent.eval.scenarios --synthesize --speaker "Luis Moray"
uv run python -m shopping_agent.eval.scenarios --mode voice
uv run python -m shopping_agent.eval.scenario_report
```

Los tres primeros corren los 20 escenarios por texto con el reranker por defecto, con GraphSAGE y sin reranker (unos 8 minutos cada uno). El cuarto genera los audios de entrada de prueba en `audio/sinteticos/<escenario>/` con un hablante incluido en XTTS-v2. El quinto corre los seis escenarios de voz con audio (ASR → agente → TTS con la voz clonada) y después los repite con la transcripción correcta; usa las grabaciones de `audio/escenarios/<escenario>/` si están todos los turnos y, si no, los audios sintéticos, y lo deja anotado. El último escribe el resumen. `--only` limita la corrida a unos escenarios.

Qué queda de cada corrida:

| Dónde | Qué |
|---|---|
| `results/escenarios/<corrida>/<escenario>.json` | Turnos (texto, transcripción del ASR, respuesta, texto enviado al TTS), operaciones, tiempos por etapa e instantáneas del agente y de la tienda antes y después de cada turno |
| `results/escenarios/<corrida>/<escenario>.md` | Ficha del escenario: la conversación con sus operaciones, cada comprobación con su resultado, las violaciones y el estado final de la tienda |
| `results/escenarios/<corrida>/corrida.json` | Fecha, commit, modelos, carga inicial y veredictos |
| `results/escenarios/voz/metricas_voz.json` | Errores del ASR (WER, importes, cantidades y nombres de producto), inteligibilidad y semejanza de la voz, turno a turno |
| `results/escenarios/resumen.md` y `.json` | Tablas de todas las corridas |
| `results/escenarios/voz_sintetica/` | La corrida por voz anterior, con todos los audios de entrada sintéticos; se conserva para compararla con la voz real |
| `results/escenarios/grabaciones.md` y `.json` | Cada grabación del usuario frente al texto de su turno |
| `results/diagnostico_voz_05/` | Comprobación aparte de por qué falla el escenario 05 con la voz del usuario |
| `audio/corridas/voz/<escenario>/` | Audios de entrada y de respuesta (fuera de git) |

Resultados ([results/escenarios/resumen.md](results/escenarios/resumen.md)). «Antes» es la línea base, guardada en [results/escenarios_base/](results/escenarios_base/resumen.md); «después», con las guardas añadidas al agente tras diagnosticar los fallos ([documentation/DIAGNOSTICO_FALLOS.md](documentation/DIAGNOSTICO_FALLOS.md)):

| Corrida | Entrada | Reranker | Antes | Después |
|---|---|---|---|---|
| `texto` | texto | control (por defecto) | 14 de 20 | 20 de 20 |
| `texto_sage` | texto | GraphSAGE | 16 de 20 | 20 de 20 |
| `texto_sin_reranker` | texto | ninguno | 16 de 20 | 20 de 20 |
| `voz` | grabaciones del usuario (los 31 turnos) | control | — | 6 de 6 (5 de 6 antes de la guarda de los números sueltos) |
| `voz_sintetica` | audio sintético de prueba | control | 3 de 6 | 6 de 6 |
| `voz_texto_correcto` | transcripción correcta | control | 3 de 6 | 6 de 6 |

No hubo ninguna violación de restricciones, ni antes ni después. Los fallos de la línea base eran decisiones del LLM en el diálogo (no cotizaba, añadía o cambiaba un producto que no se le pidió, no contestaba una pregunta). Los 20 escenarios son ahora el conjunto con el que se ajustó el agente: el 100 % no es una tasa de aciertos general.

**Voz con las grabaciones del usuario** (11 y 12 de noviembre, los 31 turnos). El ASR tiene un WER del 1,4 %, sin errores en importes (0 de 3) ni en cantidades (0 de 8) y con uno en nombres de producto (1 de 13). La primera corrida, con el agente sin tocar, dio 5 de 6: en 05 Whisper escribió «he dicho 12, no 2», con cifras, donde se dijo «doce, no dos», y el LLM fijó un presupuesto de 12 € en vez de cambiar la cantidad (causa comprobada aparte en [results/diagnostico_voz_05/](results/diagnostico_voz_05/LEEME.md)). Se corrigió con una guarda y un aviso al LLM: con productos en el carrito, un número que no va con dinero no es un importe. Con eso la voz real da 6 de 6, y dos escenarios de reserva nuevos (25 y 26, corridas `reserva_cifras*`) pasan 2 de 2 con los tres rerankers. Sigue igual el escenario 01: «cafetera italiana» se entendió «cafetería italiana», lo que cambió la búsqueda y el pedido final (dos paquetes de cápsulas de café en lugar de una cafetera); cuenta como correcto porque sus comprobaciones se refieren al primer candidato y no miran qué producto es. Latencia media por turno con LLM: 11,97 s (ASR 0,35, LLM 5,03, TTS 6,54). El detalle, la comparación con el hablante sintético, los límites de la corrección y lo que no se ha verificado están en [documentation/PLAN.md](documentation/PLAN.md), apartado «Voz con las grabaciones del usuario».

Para comprobar que las correcciones no dependen de la redacción de esos 20 hay escenarios de reserva en [scenarios/reserva/](scenarios/reserva/), escritos antes de tocar el agente y corridos una sola vez al final. Los cuatro primeros (21 a 24): 3 de 4 con el control, 4 de 4 con GraphSAGE y 3 de 4 sin reranker (el que falla, por una expectativa mal planteada; ver el diagnóstico). Para la corrección de los números sueltos se añadieron otros dos (25 y 26), corridos aparte, también una sola vez: 2 de 2 en las tres configuraciones.

```bash
uv run python -m shopping_agent.eval.scenarios --mode text --scenarios scenarios/reserva --only 21_cierre_otras_palabras 22_agotado_otro_candidato 23_candidato_fuera_de_lista 24_dato_que_no_consta --name reserva
uv run python -m shopping_agent.eval.scenarios --mode text --scenarios scenarios/reserva --only 25_correccion_con_cifras 26_presupuesto_con_carrito --name reserva_cifras
```

### Recuperación en test

```bash
uv run python -m shopping_agent.eval.retrieval_test
```

Evaluación única con las 300 consultas de test: entrena los rerankers como en la validación (las mismas consultas de ajuste y las mismas cinco semillas) y escribe [results/retrieval_test.md](results/retrieval_test.md) y su `.json`, con la fecha y el commit. El comando se niega a repetirse si el resultado ya existe; nada se ajustó después de ver los números. Con `--render` solo vuelve a escribir la tabla a partir del resultado guardado, sin leer test (sirve para actualizar la columna de validación si esa tabla se regenera).

| Sistema | nDCG@10 en test [IC 95 %] | recall@50 | Dif. con el híbrido |
|---|---|---|---|
| BM25 (base léxica) | 0,6797 [0,6515; 0,7066] | 0,6455 | −0,0316 |
| Denso | 0,7278 [0,7016; 0,7524] | 0,6501 | +0,0165 |
| Híbrido RRF | 0,7113 [0,6844; 0,7368] | 0,7194 | |
| Híbrido + control sin grafo (la configuración del agente) | 0,7292 [0,7031; 0,7536] | 0,7194 | +0,0179 [+0,0086; +0,0275] |
| Híbrido + GraphSAGE (la variante del GNN) | 0,7363 [0,7104; 0,7605] | 0,7194 | +0,0249 [+0,0152; +0,0351] |

GraphSAGE supera al control sin grafo en +0,0071 (IC 95 % [+0,0028; +0,0117]). Los rerankers reordenan los 50 primeros del híbrido, así que comparten su recall@50.

## Organización del código

```
src/shopping_agent/
  data/        preparación de ESCI y de la tienda simulada
  retrieval/   BM25, denso, fusión RRF y métricas
    dev_data.py, first_stage.py   consultas de ajuste y validación; señales de la primera etapa
    graph.py, gnn.py              grafo heterogéneo consulta–producto (HeteroData); modelo (HeteroConv) y su pérdida
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
    scenario_format.py, scenario_checks.py   formato de los escenarios; comprobaciones por código
    scenario_violations.py                   violaciones de restricciones, turno a turno
    scenario_runner.py, scenarios.py         un escenario de principio a fin; comando que los corre
    scenario_report.py                       ficha por escenario y resumen de las corridas
    recordings.py                            grabaciones del usuario frente al guion, con el ASR
    retrieval_test.py                        evaluación final de la recuperación en test
```

Criterio de idioma: los identificadores del código (módulos, funciones, clases, variables, campos, claves de los JSON de resultados y opciones de los comandos) van en inglés. Va en español todo lo que es lenguaje: los textos para el usuario y para el LLM, los comentarios y la documentación, y los nombres que el LLM o las transcripciones muestran (nodos del grafo, herramientas y sus argumentos, códigos de rechazo). La función que implementa un nodo se llama como el nodo. Los archivos de resultados y de escenarios, que son contenido, también van en español.

## Pruebas

Las pruebas no necesitan GPU, modelos ni grabaciones: el grafo del agente se prueba con un LLM guionizado, el canal de voz con un ASR y un TTS simulados, y el reranker con un grafo sintético de doce productos. El formato de los escenarios, sus comprobaciones, las violaciones y el ejecutor se prueban igual, con el LLM guionizado; una prueba comprueba además que el guion de grabación corresponde a los escenarios. Las que no tratan de Postgres usan memoria volátil pedida de forma explícita; las de Postgres se omiten si `SHOPPING_AGENT_PG_URL` no está definida o el servidor no responde.

```bash
uv run pytest
```

## Uso de IA

Parte del código y la documentación se elaboró con asistencia de IA generativa (Claude Code) y fue revisado por el autor.
