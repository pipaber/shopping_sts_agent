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

Los modelos (embeddings y LLM) se descargan en la caché de Hugging Face. Si el disco del sistema tiene poco espacio, `HF_HOME` en el `.env` la lleva a otro disco; ocupa unos 6 GB.

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

## Memoria del agente (Postgres)

Los checkpoints de la conversación (`PostgresSaver`) y la memoria entre conversaciones (`PostgresStore`) se guardan en Postgres. La conexión se lee de `SHOPPING_AGENT_PG_URL` y las tablas se crean solas la primera vez. Sin esa variable el agente funciona igual, pero con memoria volátil.

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

## Pruebas

Las pruebas no necesitan GPU ni modelos: el grafo se prueba con un LLM guionizado. Las de Postgres se omiten si `SHOPPING_AGENT_PG_URL` no está definida o el servidor no responde.

```bash
uv run pytest
```

## Uso de IA

Parte del código y la documentación se elaboró con asistencia de IA generativa (Claude Code) y fue revisado por el autor.
