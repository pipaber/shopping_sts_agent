# Asistente de compras por voz (Laboratorio 4)

Asistente que recibe consultas habladas en español, recupera productos de un catálogo (ESCI), opera sobre una tienda simulada y responde con voz clonada. Todo el procesamiento de modelos es local.

El diseño y el cronograma están en [documentation/PLAN.md](documentation/PLAN.md). Qué funciona, qué falla y por qué, caso a caso: [documentation/ANALISIS_ACIERTOS_FALLOS.md](documentation/ANALISIS_ACIERTOS_FALLOS.md).

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
- **Hardware.** Medido en una estación de trabajo con una NVIDIA RTX A2000 de 12 GB (9 532 MiB de memoria de GPU con todo cargado). El objetivo del enunciado es Google Colab con una T4, donde también se corrió entero con [notebooks/colab.ipynb](notebooks/colab.ipynb): 9 152 MiB y los mismos resultados, con turnos por voz de 21 s en lugar de 11 (ver «Ejecución en Colab (T4)»).

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

Con las 1 500 consultas de `train`: nDCG@10 de 0,6807 con BM25, 0,7372 con el denso y 0,7236 con el híbrido, que es el que recupera más productos exactos entre los 50 primeros (recall@50 de 0,723, frente a 0,664 del denso y 0,640 de BM25).

**Modelo de embeddings.** Se usa `intfloat/multilingual-e5-small`. Se comparó con dos modelos mayores, con las consultas de `train` y sin entrenar nada ([results/embedding_comparison.md](results/embedding_comparison.md)):

```bash
uv run python -m shopping_agent.eval.embeddings
```

| Modelo | nDCG@10 denso (train) | Dif. con e5-small [IC 95 %] | nDCG@10 denso (validación) | VRAM pico |
|---|---|---|---|---|
| `intfloat/multilingual-e5-small` (el del agente) | 0,7372 | | 0,7535 | 463 MiB |
| `intfloat/multilingual-e5-base` | 0,7210 | −0,0162 [−0,0226; −0,0102] | 0,7303 | 1 435 MiB |
| `BAAI/bge-m3` | 0,7358 | −0,0014 [−0,0077; +0,0045] | 0,7384 | 2 662 MiB |

Ninguno supera al pequeño: `e5-base` queda por debajo y `bge-m3` empata en `train`, queda por debajo en las 300 consultas de validación y ocupa casi seis veces más memoria de GPU. El modelo no se cambió.

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

Si `nvcc` no está en el `PATH`, se añade `CUDACXX=/usr/local/cuda/bin/nvcc` delante. Si ya se instaló sin CUDA, se recompila con `CMAKE_ARGS="-DGGML_CUDA=on" uv sync --reinstall-package llama-cpp-python`. La compilación tarda unos 20 minutos en la workstation y 61 en Colab; el notebook de Colab usa una rueda ya compilada (ver «Ejecución en Colab (T4)»).

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

- Entre 15 y 40 segundos de habla continua en español, viva y a tu ritmo normal de conversación, no leída despacio: XTTS-v2 copia el ritmo y la entonación de la grabación, y una referencia pausada y plana da una voz lenta y apagada.
- Lo que más pesa es el principio. Tal como este proyecto llama a XTTS-v2 (comprobado en el código de `coqui-tts` instalado), el timbre sale de los primeros 30 segundos y el ritmo y la entonación, de los 6 primeros.
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

### Voz del agente: referencia y velocidad

La voz clonada con la primera grabación de referencia sonaba, a juicio de su autor, «un poco robótica, medio apagada» y lenta. El 12 de noviembre cambiaron dos cosas:

- **Grabación de referencia nueva** (39,6 s; la anterior queda en `audio/referencia/referencia_anterior.wav`). Es habla continua, viva y a ritmo normal, porque XTTS-v2 copia de la referencia el ritmo y la entonación además del timbre.
- **Velocidad del habla 1,10.** `XttsTTS` pasa `speed` a la síntesis: 1,0 es el ritmo de la referencia y 1,10, el valor por defecto, habla un 10 % más rápido. Se cambia con `SHOPPING_AGENT_TTS_SPEED` (en [.env.example](.env.example)) o con `--speed` en `voice.tts`. La velocidad queda anotada en la descripción de la voz de cada transcripción y en `/health` del servidor en vivo.

**Por qué 1,10.** El autor comparó de oído tres versiones (referencia anterior, nueva, y nueva a 1,15) y eligió la última, así que el primer valor por defecto fue 1,15. Después se midió la velocidad por separado, con la referencia nueva y los mismos 37 textos (6 frases y las 31 respuestas del agente; [results/voz_velocidad.md](results/voz_velocidad.md)):

| Velocidad | WER de Whisper | WER sin el texto peor | «Di sí» entendido | Semejanza con las grabaciones reales | Audio de los 37 textos | Síntesis |
|---|---|---|---|---|---|---|
| 1,0 | 7,5 % | 4,4 % | 7 de 7 | 0,285 | 792 s | 184 s |
| 1,1 (por defecto) | 6,0 % | 4,5 % | 7 de 7 | 0,274 | 719 s | 184 s |
| 1,15 | 6,7 % | 4,8 % | 4 de 7 | 0,270 | 688 s | 184 s |
| 1,3 | 6,8 % | 5,2 % | 5 de 7 | 0,264 | 609 s | 183 s |

El «texto peor» es el mismo a las cuatro velocidades: la respuesta con las marcas impronunciables. La medida es determinista: repetida, da las mismas transcripciones.

Acelerar no empeora de forma clara el WER, que lo domina ese texto. Lo que cambia entre 1,1 y 1,15 es la frase con la que el agente pide confirmar un pedido: a 1,15, «Di sí para registrarlo» se entiende «dice para registrarlo» en 3 de las 7 respuestas que la llevan. A la vista de la tabla, el autor bajó el valor por defecto a 1,10: es el más alto de los medidos que conserva esa frase entera y el de menor WER.

**Antes y después**, sobre los seis escenarios de voz con sus grabaciones (31 turnos; el agente dio las mismas 31 respuestas en las tres corridas):

| Medida | Voz anterior (`voz_referencia_anterior`) | Voz nueva a 1,15 (`voz_velocidad_1_15`) | Voz nueva a 1,10 (`voz`, la actual) |
|---|---|---|---|
| Escenarios correctos | 6 de 6 | 6 de 6 | 6 de 6 |
| Inteligibilidad (WER de Whisper sobre la síntesis) | 3,4 % | 7,0 % | **5,5 %** |
| «Di sí para registrarlo» entendido | 7 de 7 | 3 de 7 | **7 de 7** |
| Semejanza con su grabación de referencia, media / mínima | 0,741 / 0,501 | 0,709 / 0,593 | 0,710 / 0,609 |
| Semejanza con las 31 grabaciones reales del usuario, media / mínima | 0,259 / 0,221 | 0,270 / 0,191 | 0,273 / 0,234 |
| Duración media del audio de respuesta | 24,8 s | 20,7 s | 21,6 s |
| TTS por turno, media (todos / con LLM) | 6,07 / 6,54 s | 5,61 / 5,89 s | 5,62 / 5,90 s |
| Latencia total por turno, media (todos / con LLM) | 10,36 / 11,97 s | 9,92 / 11,35 s | 9,92 / 11,35 s |
| Turno más lento | 25,55 s | 18,63 s | 18,84 s |

Las dos semejanzas no dicen lo mismo. La primera compara con la misma grabación de la que se clonó la voz y sale optimista (misma toma, mismo micrófono); además, cada voz se compara con su propia referencia, así que 0,741 y 0,710 no son comparables entre sí. La segunda compara con las grabaciones del usuario que entran en los escenarios, que el modelo no usó para clonar: su techo es 0,377, lo que esas 31 grabaciones se parecen entre sí (son cortas, de 1 a 6 s).

Qué dice y qué no:

- **Se oye antes y dura menos.** Frente a la voz anterior, las respuestas duran un 13 % menos (un 3 % por la referencia y un 10 % por la velocidad). La espera hasta que empieza a sonar baja unos 0,5 s por turno, y eso viene de la referencia nueva: acelerar no ahorra tiempo de síntesis, solo acorta el audio. Por eso la latencia es la misma a 1,10 que a 1,15.
- **Se parece algo más a la voz real**, pero poco: 0,259 → 0,273, lejos del techo de 0,377.
- **Se entiende peor que la voz anterior según Whisper**, y no es por la velocidad sino por la referencia nueva: con las mismas 31 respuestas, 3,4 % con la anterior y 7,9 % con la nueva a velocidad 1,0 (medida aparte). A 1,10 queda en 5,5 %. Más de una cuarta parte de esos errores son de una sola respuesta, la que enumera marcas impronunciables (`02_pedido_ambiguo`, turno 2: «Mgrett», «WDGP», «GSBLBL»…), que con la voz nueva sale con un tramo ininteligible y dura 32 s donde la anterior duraba 49. El resto son nombres de marca y palabras sueltas añadidas al final de un fragmento («cada una quince euros», «mua»), que con la voz anterior casi no aparecían.
- **La frase de confirmación se conserva a 1,10:** Whisper entiende «Di sí» en las 7 respuestas que la llevan, como con la voz anterior.

```bash
uv run python -m shopping_agent.eval.tts_speed --speeds 1.0 1.1 1.15 1.3 --script frases.txt --run results/escenarios/voz_referencia_anterior
uv run python -m shopping_agent.eval.scenarios --voice-metrics voz_referencia_anterior
```

El primero repite la medida de velocidades; el segundo vuelve a medir la voz de una corrida guardada con sus audios, sin correr el agente (así se añadió la semejanza con las grabaciones reales a la corrida anterior, cuyas demás cifras salieron idénticas). Whisper no es un oyente: el WER dice dónde mirar, y falta escuchar las respuestas señaladas, sobre todo la del escenario 02.

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

### Conversación en vivo

```bash
uv run python -m shopping_agent.voice.live --restore
```

Carga una sola vez la búsqueda con el reranker, el LLM, el ASR y el TTS, abre una conversación y atiende turnos por HTTP en `127.0.0.1:8765`, solo desde la propia máquina. Sirve para hablar con el agente turno a turno desde otro proceso que no puede importar el paquete, como las celdas del notebook de Colab, sin recargar los modelos en cada turno. Opciones: `--port`, `--reference` o `--speaker` (la voz, como en `voice.chat`), `--restore`, `--user`, `--n-ctx`, `--data`, `--db` y `--volatile-memory`. Se detiene con Ctrl+C o `kill`.

Todo va en JSON (UTF-8):

| Ruta | Petición | Respuesta |
|---|---|---|
| `GET /health` | — | `ready` (`false` mientras cargan los modelos), `load` (segundos de carga: `search`, `llm`, `asr`, `tts`, `total`), `vram_mib` (memoria de GPU del proceso en ese momento), `thread` (hilo de la conversación) y `voice` (de dónde sale la voz del agente y a qué velocidad habla). Mientras carga, `load` está vacío y `thread` y `voice` son `null` |
| `POST /turn` | `{"audio": "/ruta/turno.wav"}` o `{"text": "…"}`, uno de los dos | `turn` (número de turno), `heard` (lo que entendió el ASR, o el texto), `response`, `spoken` (el texto enviado al TTS), `audio` (ruta absoluta del WAV de la respuesta), `operations` (lista de `tool`, `args`, `ok` y `summary` de cada herramienta ejecutada o rechazada), `awaiting_confirmation` y `seconds` (`asr`, `retrieval`, `llm`, `tools`, `tts`, `total`) |
| `POST /reset` | `{"restore": true}` o nada | `thread` (el hilo de la conversación nueva) y `restored`. Con `restore` la tienda vuelve a su estado inicial |

```bash
curl -s http://127.0.0.1:8765/health
curl -s -X POST http://127.0.0.1:8765/turn -d '{"audio": "/ruta/a/turno.wav"}'
curl -s -X POST http://127.0.0.1:8765/turn -d '{"text": "Busco una botella de agua."}'
```

- **Errores:** `{"error": "mensaje"}` con código 400 (petición mal formada o audio que no existe), 404 (ruta desconocida), 503 (los modelos aún cargan) o 500 (el turno falló). Tras un 500 el servidor sigue atendiendo.
- **Un turno a la vez:** los modelos comparten la GPU; una petición que llega durante un turno espera a que termine.
- **Audio sin voz:** si el ASR no entiende nada (silencio, ruido), `heard` va vacío, el agente no recibe ningún mensaje y la respuesta pide repetir. Si se esperaba la confirmación de un pedido, se sigue esperando.
- **Lo que queda de cada conversación:** los audios de entrada y de respuesta en `audio/corridas/en_vivo/<hilo>/` (fuera de git) y, reescritos tras cada turno, `turnos.json` y `transcripcion.md` en `results/en_vivo/<hilo>/`, con el mismo formato que una corrida de `voice.chat`.

Prueba real del servidor (12 de noviembre, en la workstation): el escenario 03 con las cinco grabaciones del usuario, enviado turno a turno por HTTP con la tienda restaurada y el suceso externo del escenario aplicado tras el primer turno (la tienda deja el primer candidato a 9,50 € con 20 unidades). El pedido queda igual que en la corrida por voz: 4 unidades de la misma botella, 38,00 €, existencias 16. Los cuatro turnos con LLM tardaron 13,4 s de media (ASR 0,39, LLM 5,29, TTS 7,65) y la confirmación, que no pasa por el LLM, 5,1 s. El proceso ocupa 9 532 MiB de memoria de GPU con todo cargado y 9 824 al terminar la conversación. En una segunda conversación, un audio en silencio y otro de ruido volvieron con `heard` vacío en 1,1 s sin consultar al agente, un archivo que no era audio dio un 500 y el turno siguiente se atendió, y de dos turnos enviados a la vez el segundo esperó al primero. Las transcripciones están en [results/en_vivo/vivo-c6e6740e](results/en_vivo/vivo-c6e6740e/transcripcion.md) y [results/en_vivo/vivo-b2a21e1c](results/en_vivo/vivo-b2a21e1c/transcripcion.md).

La carga tarda 26 s (búsqueda 15,4, LLM 0,7, ASR 0,9, TTS 9,2) si no depende de la red. En la corrida de la prueba tardó 160 s: al cargar el modelo de embeddings, `sentence-transformers` consulta huggingface.co aunque el modelo ya esté descargado, y ese día una de las direcciones del servidor no respondía desde la workstation. Con los modelos ya descargados, `HF_HUB_OFFLINE=1` evita esa consulta; los 26 s se midieron así. Durante la carga `/health` contestó `ready: false` en todo momento.

### Métricas de voz

```bash
uv run python -m shopping_agent.eval.voice results/voz_demo_compra
uv run python -m shopping_agent.eval.voice results/voz_demo_compra --real audio/escenarios
```

Calcula, sobre una corrida guardada: la inteligibilidad (WER de Whisper sobre el audio sintetizado frente al texto enviado al TTS), la semejanza de la voz (coseno entre embeddings de hablante) y los errores del ASR en importes, cantidades y nombres de producto frente al texto correcto. La semejanza se mide con la grabación de referencia, de la que se clonó la voz, y, con `--real`, también con grabaciones reales del mismo hablante que no se usaron para clonar; la primera sale optimista y la segunda dice mejor cuánto se parece a su voz de otro momento. En las corridas de escenarios por voz, las grabaciones reales son las del usuario que entran en la corrida. Los nombres de producto esperados en cada turno se indican en `scenarios/<escenario>.terminos.json`.

## Evaluación

Qué se midió, con qué decisiones y qué quedó sin verificar está en [documentation/PLAN.md](documentation/PLAN.md) ("Diseño y resultados de la evaluación"). El análisis de aciertos y fallos, con seis aciertos y nueve fallos, su evidencia y su causa, está en [documentation/ANALISIS_ACIERTOS_FALLOS.md](documentation/ANALISIS_ACIERTOS_FALLOS.md). Aquí, cómo se reproduce cada tabla.

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
| `results/escenarios/voz_referencia_anterior/` | La corrida por voz con la voz anterior del agente (primera grabación de referencia, velocidad 1,0); se conserva para compararla con la voz nueva |
| `results/escenarios/voz_velocidad_1_15/` | La corrida por voz con la referencia nueva a velocidad 1,15, el valor por defecto antes de bajarlo a 1,10 |
| `results/voz_velocidad.md` y `.json` | Los mismos textos sintetizados a varias velocidades del habla: inteligibilidad, semejanza y duración |
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
| `voz_velocidad_1_15` | las mismas grabaciones, con la voz nueva a velocidad 1,15 | control | — | 6 de 6 |
| `voz_referencia_anterior` | las mismas grabaciones, con la voz anterior del agente | control | — | 6 de 6 |
| `voz_sintetica` | audio sintético de prueba | control | 3 de 6 | 6 de 6 |
| `voz_texto_correcto` | transcripción correcta | control | 3 de 6 | 6 de 6 |

No hubo ninguna violación de restricciones, ni antes ni después. Los fallos de la línea base eran decisiones del LLM en el diálogo (no cotizaba, añadía o cambiaba un producto que no se le pidió, no contestaba una pregunta). Los 20 escenarios son ahora el conjunto con el que se ajustó el agente: el 100 % no es una tasa de aciertos general.

**Voz con las grabaciones del usuario** (11 y 12 de noviembre, los 31 turnos). El ASR tiene un WER del 1,4 %, sin errores en importes (0 de 3) ni en cantidades (0 de 8) y con uno en nombres de producto (1 de 13). La primera corrida, con el agente sin tocar, dio 5 de 6: en 05 Whisper escribió «he dicho 12, no 2», con cifras, donde se dijo «doce, no dos», y el LLM fijó un presupuesto de 12 € en vez de cambiar la cantidad (causa comprobada aparte en [results/diagnostico_voz_05/](results/diagnostico_voz_05/LEEME.md)). Se corrigió con una guarda y un aviso al LLM: con productos en el carrito, un número que no va con dinero no es un importe. Con eso la voz real da 6 de 6, y dos escenarios de reserva nuevos (25 y 26, corridas `reserva_cifras*`) pasan 2 de 2 con los tres rerankers. Sigue igual el escenario 01: «cafetera italiana» se entendió «cafetería italiana», lo que cambió la búsqueda y el pedido final (dos paquetes de cápsulas de café en lugar de una cafetera); cuenta como correcto porque sus comprobaciones se refieren al primer candidato y no miran qué producto es. Latencia media por turno con LLM: 11,35 s (ASR 0,35, LLM 5,05, TTS 5,90) con la voz nueva del agente; con la anterior, 11,97 s (el antes y el después de la voz están en «Voz del agente: referencia y velocidad»). El detalle, la comparación con el hablante sintético, los límites de la corrección y lo que no se ha verificado están en [documentation/PLAN.md](documentation/PLAN.md), apartado «Voz con las grabaciones del usuario».

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

## Ejecución en Colab (T4)

[notebooks/colab.ipynb](notebooks/colab.ipynb) reproduce el proyecto de principio a fin en una T4 de Colab: instalación, datos, recuperación, reranker, agente por texto, escenarios por texto y por voz, y una conversación en vivo con el micrófono del navegador. Todo el procesamiento es local a la sesión; no se llama a ninguna API de inferencia.

- **Instalación.** `uv sync` crea el entorno del proyecto con las versiones de `uv.lock`. `llama-cpp-python` hay que compilarlo con CUDA, y con las 2 CPU de Colab eso tardó 61 minutos. El notebook descarga en su lugar una rueda ya compilada para el sistema de Colab (Ubuntu 24.04, CUDA 13.0), publicada como adjunto de la *release* `colab-llama-cpp-0.3.36` de este repositorio, y comprueba que carga y que usa la GPU; si no sirve en la sesión, compila como respaldo. Con la rueda, la instalación completa tardó 1 min 44 s en la corrida final.
- **Voz propia.** Las grabaciones se suben a la sesión y se borran al cerrarla; no entran en el repositorio. Sin ellas, el agente habla con un hablante de prueba de XTTS-v2 y los escenarios usan audios sintéticos.
- **Conversación en vivo.** Una celda arranca `shopping_agent.voice.live` en segundo plano y otra graba un turno con el micrófono, lo envía y reproduce la respuesta. No es tiempo real: es una conversación por turnos.

**Corrida final** (12 de noviembre de 2026, commit `d81bc00`; T4 con 2 CPU, Ubuntu 24.04, CUDA 13.0), con la voz del autor clonada de la referencia nueva a velocidad 1,10 y sus 31 grabaciones. Los archivos de esa corrida están en [results/colab_t4/](results/colab_t4/LEEME.md), descargados de la sesión de Colab; el resto de `results/` guarda las corridas de la workstation, que son las de la otra columna.

| Medida | Workstation (RTX A2000, 12 GB) | Colab (T4, 2 CPU) |
|---|---|---|
| Escenarios por texto | 20 de 20, sin violaciones | 20 de 20, sin violaciones |
| LLM por turno, por texto (73 turnos) | 5,04 s (máx. 9,79) | 8,00 s (máx. 15,53) |
| Escenarios por voz, con las 31 grabaciones del autor | 6 de 6, sin violaciones | 6 de 6, sin violaciones |
| ASR: WER; errores en importes, cantidades y nombres de producto | 1,4 %; 0 de 3, 0 de 8 y 1 de 13 | 1,4 %; 0 de 3, 0 de 8 y 1 de 13 |
| Inteligibilidad de la voz generada (WER de Whisper) | 5,5 % | 5,6 % |
| Semejanza con la referencia / con las grabaciones reales (techo 0,377) | 0,710 / 0,273 | 0,709 / 0,272 |
| Turno por voz con LLM (24 turnos): ASR / LLM / TTS | 0,35 / 5,05 / 5,90 s | 0,41 / 7,85 / 13,07 s |
| Turno por voz con LLM: total | 11,35 s (máx. 18,84) | 21,38 s (máx. 36,26) |
| Turno por voz sin LLM (7 turnos): total | 5,01 s (máx. 10,81) | 10,66 s (máx. 23,69) |
| Memoria de GPU con todo cargado | 9 532 MiB de 12 282 | 9 152 MiB de 15 360 |
| Carga inicial de los modelos, por voz | 24 s | 109 s (incluye leer por primera vez los modelos recién descargados) |
| Conversación en vivo: listo para el primer turno | 26 s | 102 s |
| Conversación en vivo: un turno | 17,8 s (turno de búsqueda) | 29,9 s y 28,2 s (dos turnos del escenario 03) |

- **El sistema hace lo mismo en las dos máquinas.** Mismos veredictos, mismo ASR y la misma voz, con diferencias mínimas en las medidas. Las 378 pruebas pasan en Colab, la recuperación en `train` da los mismos nDCG@10 (0,6807, 0,7372 y 0,7236) y los rerankers entrenados allí con la semilla 0 dan 0,7578 (control) y 0,7630 (GraphSAGE) en validación.
- **La T4 es más lenta.** El LLM tarda 1,6 veces más que en la A2000 (8,0 frente a 5,0 s por turno) y la síntesis con la voz clonada 2,2 veces más (13,1 frente a 5,9 s): un turno por voz con LLM pasa de 11,4 a 21,4 s, y el más lento llega a 36 s. Más de la mitad de ese tiempo es el TTS.
- **Cabe con margen.** 9 152 MiB de los 15 360 de la T4 con los cuatro modelos y el reranker cargados: 712 con la búsqueda, 5 826 al añadir el LLM y 7 394 al añadir el ASR.
- **Conversación en vivo.** El servidor quedó listo en 102 s con 9 152 MiB. Dos turnos del escenario 03 con grabaciones del autor, enviados por HTTP, tardaron 29,9 s (ASR 1,1, LLM 15,5, TTS 13,1) y 28,2 s (ASR 0,4, LLM 8,6, TTS 19,1), con las dos transcripciones correctas.
- **Sin probar en Colab:** la grabación con el micrófono del navegador, que necesita a una persona delante, y la celda que sube `audio.zip` (los audios se subieron por el panel de archivos).

Antes de esta corrida se había medido con el hablante de prueba de XTTS-v2 en lugar de la voz clonada: 6 de 6 por voz y 17,3 s por turno con LLM (TTS 8,9 s). La voz clonada del autor tarda más en sintetizarse.

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
    live.py      servidor local para conversar en vivo, turno a turno
  eval/        evaluación de la recuperación, del reranker (comparación y coste), métricas de voz y velocidad del habla
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
