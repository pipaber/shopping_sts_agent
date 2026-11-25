# Guion del video — Laboratorio 4

Elaborado el 24 de noviembre de 2026.

Video de 20 minutos como máximo, en cuatro bloques, uno por integrante; se entrega el 25 de noviembre de 2026 junto con el código. Piero hace la demostración porque el agente responde con su voz clonada.

## Reparto

Los tiempos y los temas de cada bloque son los del enunciado. El reparto de nombres es una propuesta: solo la demostración tiene que ser de Piero; los otros tres bloques se pueden intercambiar.

| Bloque | Quién | Minutos | Qué pide el enunciado |
| --- | --- | --- | --- |
| 1. Metodología | Yesenia | 0:00 – 4:00 | Diseño del sistema y decisiones principales |
| 2. Implementación | Diego | 4:00 – 8:00 | Recuperación, agente, estado y gestión de recursos |
| 3. Demostración | Piero | 8:00 – 16:00 | Una compra y un caso con aclaración, con entrada y respuesta por voz; al menos una interacción completa con su espera real |
| 4. Resultados | Edgar | 16:00 – 20:00 | Comparación con el modelo base, ablación, errores y limitaciones |

**Por qué Piero en la demostración.** El agente responde con la voz clonada de Piero. Si él habla y el agente contesta, el video muestra a la vez la voz real y la clonada, que es justo la semejanza que pide evaluar el enunciado. Con otra persona hablando, el agente respondería con una voz que no es la de quien pregunta y habría que explicarlo.

**Formato sugerido.** Cada uno graba su bloque por separado, con pantalla compartida y su voz, y se unen al final. Así nadie depende de los demás y la demostración se puede repetir sin regrabar el resto. Dejad unos segundos de margen: el máximo es 20 minutos.

## Antes de grabar

La demostración necesita unos 20 minutos de preparación en Colab antes de pulsar grabar. El micrófono del navegador y la celda que sube `audio.zip` no se han probado todavía: hay que probarlos antes del día de la entrega.

- [ ] Abrir el [notebook en Colab](https://colab.research.google.com/github/pipaber/shopping_sts_agent/blob/main/notebooks/colab.ipynb) y poner el entorno en GPU T4.
- [ ] Ejecutar las secciones 1 a 8 (unos 15 minutos: instalación, datos, recuperación y rerankers).
- [ ] Sección 11: marcar `SUBIR_AUDIOS` y subir `audio/audio.zip` del portátil de Piero. Sin esas grabaciones el agente no habla con su voz.
- [ ] Sección 13, primera celda: arrancar el agente en vivo (minuto y medio). Debe decir que la voz está clonada de los turnos grabados.
- [ ] Sección 13, segunda celda: aceptar el permiso del micrófono y hacer un turno de prueba completo con **Hablar** y **Enviar**.
- [ ] Grabar la pantalla con el audio del sistema además del micrófono, para que se oiga la respuesta del agente.
- [ ] No dejar la sesión parada mucho rato: Colab la cierra por inactividad y hay que repetir todo.

**Si la celda de subida falla.** Subir `audio.zip` con el panel de archivos de Colab (queda en `/content`) y descomprimirlo en la terminal de Colab con `cd /content/shopping_sts_agent && mkdir -p audio && unzip -o -q /content/audio.zip -d audio`. Así se hizo en las corridas de prueba.

**Si el micrófono falla.** Plan B, diciendo en el video que la entrada es una grabación: ejecutar la sección 12 (los seis escenarios por voz con las grabaciones de Piero, unos 20 minutos) y reproducir entradas y respuestas con la sección 15. El enunciado pide entrada y respuesta por voz, no que sea en directo.

**Al hablar.** Frases completas, cerca del micrófono y sin prisa. En las pruebas, «cafetera» se transcribió una vez como «cafetería» y el agente buscó otra cosa: por eso la demostración propuesta usa botellas de agua y auriculares.

## Bloque 1 — Metodología (Yesenia, 4 min)

Idea central: un asistente por turnos con tres etapas locales (oír, decidir y hablar), donde el modelo de lenguaje propone y el código decide.

| Tiempo | Qué decir | Qué mostrar |
| --- | --- | --- |
| 0:00 – 0:30 | El problema: comprar hablando en español. El asistente busca, compara, cotiza y registra el pedido solo después de un sí. | Diagrama «Cómo funciona» del README |
| 0:30 – 1:30 | Las tres etapas y sus modelos, con el motivo de cada uno (lista de abajo). | El mismo diagrama; tabla de decisiones del PLAN, apartado 2 |
| 1:30 – 2:30 | Los datos: ESCI reducido en español y la tienda simulada. | README, apartado de datos |
| 2:30 – 3:30 | Las decisiones de diseño (lista de abajo). | PLAN, apartado 1 |
| 3:30 – 4:00 | Cómo se evalúa: 20 escenarios con estado inicial reproducible y veredicto por código, 6 de ellos por voz y repetidos con la transcripción correcta. Paso a Diego. | Carpeta `scenarios/evaluacion/` |

**Modelos y por qué**

- **ASR:** Whisper large-v3-turbo con `faster-whisper`. Buen español, rápido y unos 2 GB de memoria de GPU.
- **LLM:** Qwen2.5-7B-Instruct cuantizado (GGUF Q4_K_M) con `llama-cpp-python`. Ocupa unos 5 GB y una gramática JSON le obliga a devolver siempre una llamada a herramienta válida.
- **Búsqueda:** BM25 más embeddings `multilingual-e5-small`, fusionados, y un reranker entrenado por el grupo.
- **TTS:** F5-Spanish clonando la voz de Piero a partir de dos grabaciones suyas. Se empezó con XTTS-v2, se compararon doce formas de clonar con las mismas frases y se eligió de oído la que más se parecía.

**Datos**

- Catálogo: 43 674 productos de ESCI en español (el enunciado pide 5 000).
- Consultas: 1 500 de `train` (1 200 para ajustar y 300 para validar) y 300 de `test`, que se midieron una sola vez.
- Tienda simulada con precios, existencias, carritos y pedidos, generada con semilla fija y restaurable.
- Las etiquetas ESCI solo se usan para medir y para entrenar el reranker con `train`. El agente nunca las lee.

**Decisiones principales**

1. Todo se ejecuta en Colab con una T4, sin ninguna API externa de inferencia.
2. El LLM propone el paso y el código lo valida: cantidades, presupuesto y existencias se comprueban por código.
3. Al confirmar se vuelven a comprobar las condiciones y el pedido se registra entero o no se registra; repetir el sí no lo duplica.
4. Lo que el catálogo no dice de un producto se responde como desconocido.
5. El control es un grafo explícito de LangGraph, no un agente preconstruido.
6. Nada se ajusta con las consultas de `test`.

## Bloque 2 — Implementación (Diego, 4 min)

Idea central: la búsqueda combina dos recuperadores y un reranker, el agente es un grafo con doce pasos y doce herramientas, y todos los modelos caben juntos en 8,1 GB de los 15 de la T4.

| Tiempo | Qué decir | Qué mostrar |
| --- | --- | --- |
| 4:00 – 5:00 | Recuperación en tres pasos (lista de abajo). | `src/shopping_agent/retrieval/` |
| 5:00 – 6:15 | El agente: grafo, herramientas y validaciones por código. | `agent/graph.py`, `agent/tools.py`, `agent/guards.py` |
| 6:15 – 7:00 | Estado y memoria. | `agent/state.py`, `agent/memory.py` |
| 7:00 – 8:00 | Gestión de recursos en la T4. Paso a Piero. | Salida de la celda de escenarios por voz, que imprime la memoria al cargar cada modelo |

**Recuperación**

1. BM25 sobre el texto del producto (la base léxica) y búsqueda densa con `multilingual-e5-small`.
2. Fusión de las dos listas por posiciones (RRF) y corte en los 50 primeros.
3. Un reranker reordena esos 50. El que usa el agente es una red de dos torres sin grafo (el «control»). La variante con GraphSAGE usa un grafo heterogéneo de consultas y productos (43 674 productos, 1 500 consultas; aristas de candidato, similitud y marca) y sirve para la ablación.

**Agente**

- Grafo explícito de LangGraph con doce nodos: interpretar el turno, validar, ejecutar la herramienta, pedir aclaración, cotizar, confirmar, registrar el pedido y proponer una alternativa, entre otros.
- Doce herramientas: buscar, ver el detalle, comparar de 2 a 4 productos, consultar precio y existencias, añadir al carrito, fijar una cantidad, quitar, guardar el presupuesto, guardar una preferencia, preparar la cotización, preguntar al usuario y responder.
- En cada paso el LLM elige una herramienta y sus argumentos; el código comprueba que sean válidos antes de ejecutarla y le devuelve el resultado.
- Validaciones que no dependen del LLM: no se cierra un pedido sin cotizarlo antes, «el segundo» tiene que existir en la última lista mostrada, no se repite una búsqueda idéntica y un número suelto no se toma como presupuesto si ya hay carrito.
- La confirmación es una transacción: vuelve a comprobar precio, existencias y presupuesto, y descuenta inventario y registra el pedido a la vez. Un segundo sí devuelve el mismo pedido.

**Estado y memoria**

- El estado de la conversación guarda mensajes, candidatos mostrados, carrito, presupuesto, cotización pendiente y operaciones ejecutadas.
- Postgres guarda ese estado entre turnos y las preferencias del usuario entre conversaciones. La tienda es una base SQLite.

**Recursos en la T4 (medidos en Colab)**

- Memoria de GPU acumulada al cargar: 712 MiB la búsqueda, 5 826 con el LLM, 7 394 con el ASR y 8 140 con la voz, de 15 360.
- Los modelos se cargan una sola vez (entre 89 y 108 s) y esa carga se mide aparte de los turnos.
- Los embeddings del catálogo se calculan una vez (3 minutos) y se reutilizan.
- `llama-cpp-python` tarda 61 minutos en compilarse con CUDA en Colab; el notebook descarga una versión ya compilada y la instalación completa baja a menos de 2 minutos.

## Bloque 3 — Demostración (Piero, 8 min)

Dos conversaciones por voz en la sección 13 del notebook: una compra con cambio de cantidad (5 turnos) y un pedido ambiguo que obliga a aclarar (3 turnos). Son los escenarios 03 y 02 de la evaluación, que pasan por voz en todas las corridas.

| Tiempo | Qué pasa |
| --- | --- |
| 8:00 – 8:40 | Presentación: el notebook ya está preparado y el agente arrancado. Leer la línea «Agente listo…», que dice la voz y la memoria ocupada. Avisar de que es por turnos y de que la voz que responde es la de Piero clonada. |
| 8:40 – 12:30 | Caso 1: compra con cambio de cantidad. El primer turno se muestra entero, con su espera real. |
| 12:30 – 14:45 | Caso 2: pedido ambiguo. Pulsar **Salir** y volver a ejecutar la celda: empieza una conversación nueva con la tienda restaurada. |
| 14:45 – 16:00 | Cierre: abrir la transcripción que guarda el notebook y señalar las operaciones ejecutadas y el pedido registrado. Paso a Edgar. |

**Caso 1 — compra con cambio de cantidad**

| Turno | Piero dice | Qué debe hacer el agente |
| --- | --- | --- |
| 1 | «Busco una botella de agua de acero inoxidable. Mi presupuesto es de 45 euros.» | Busca, anota el presupuesto y lee varias opciones con su precio |
| 2 | «Añade dos de la primera.» | Añade dos unidades y dice el total |
| 3 | «Mejor que sean cuatro.» | Deja cuatro unidades, sin perder el presupuesto |
| 4 | «Ciérralo.» | Repite el pedido completo y pide confirmación; todavía no registra nada |
| 5 | «Sí.» | Registra el pedido y dice su número |

Si sobra tiempo, un sexto turno repitiendo «Sí, confirmo» muestra que el pedido no se duplica.

**Caso 2 — pedido ambiguo**

| Turno | Piero dice | Qué debe hacer el agente |
| --- | --- | --- |
| 1 | «Quiero comprar un regalo para mi hermana.» | No busca: pregunta qué tipo de regalo |
| 2 | «Unos auriculares bluetooth, y no quiero gastar más de 50 euros.» | Busca, anota el presupuesto y lee las opciones |
| 3 | «Ponme uno del primero.» | Añade una unidad al carrito |

**Qué señalar en pantalla en cada turno**

- «Tú:» es lo que entendió el ASR; comparar con lo dicho.
- Las líneas con punto son las operaciones que ejecutó el código, con «hecho» o «rechazado».
- La última línea da el tiempo del turno por etapa: ASR, LLM y voz.

**Tiempos a esperar.** En la T4 un turno con LLM tarda entre 23 y 25 s de media, y los de búsqueda son los más lentos (hasta 49 s en las pruebas). Las respuestas que leen una lista o el carrito duran entre 20 y 30 s. Ocho turnos caben en los ocho minutos con poco margen: solo una interacción tiene que verse con su espera real, así que las demás esperas se pueden recortar en la edición, avisándolo en pantalla.

**Qué puede salir distinto.** Los productos y precios que lea el agente son los de la tienda restaurada, no hace falta que coincidan con ningún ejemplo. Las marcas raras del catálogo se pronuncian deformadas. Si el ASR entiende mal una palabra, corregir de viva voz («he dicho…») también es parte de lo que el sistema sabe hacer; conviene dejarlo en el video y comentarlo.

## Bloque 4 — Resultados (Edgar, 4 min)

Idea central: la búsqueda supera a la base léxica, el grafo aporta poco, el agente completa los 20 escenarios y los 6 de voz, y el coste está en la latencia.

| Tiempo | Qué decir | Qué mostrar |
| --- | --- | --- |
| 16:00 – 17:00 | Recuperación frente a la base léxica, en `test`. | `results/retrieval_test.md` |
| 17:00 – 17:45 | Ablación del reranker. | La misma tabla y `results/escenarios/resumen.md` |
| 17:45 – 18:30 | Escenarios, voz y latencia. | `results/escenarios/resumen.md`; tabla de Colab del README |
| 18:30 – 19:40 | Errores y limitaciones. | `documentation/ANALISIS_ACIERTOS_FALLOS.md` |
| 19:40 – 20:00 | Cierre. | Repositorio |

**Recuperación en test** (300 consultas, medidas una sola vez; nDCG@10 con los pesos del enunciado)

| Sistema | nDCG@10 | recall@50 |
| --- | --- | --- |
| BM25 (base léxica) | 0,6797 | 0,6455 |
| Denso | 0,7278 | 0,6501 |
| Híbrido | 0,7113 | 0,7194 |
| Híbrido + reranker sin grafo (el del agente) | 0,7292 | 0,7194 |
| Híbrido + reranker con GraphSAGE | 0,7363 | 0,7194 |

- El sistema del agente mejora a BM25 en 0,05 de nDCG@10.
- El denso solo ordena mejor que el híbrido, pero el híbrido encuentra más productos exactos entre los 50 primeros (0,72 frente a 0,65). Por eso el híbrido genera los candidatos y el reranker los ordena.
- La tabla se reprodujo en Colab con la misma configuración: los tres primeros valores salen idénticos y los rerankers, 0,7289 y 0,7340.

**Ablación: el reranker**

- Con grafo frente a sin grafo: GraphSAGE gana 0,0071 de nDCG@10 (intervalo del 95 %: de 0,0028 a 0,0117). Es una mejora real pero pequeña; casi todo lo aporta reordenar, no el grafo.
- En los 20 escenarios, las tres variantes (sin grafo, con GraphSAGE y sin reranker) dan 20 de 20.
- En cuatro escenarios de reserva, escritos antes de corregir el agente y no usados para ajustarlo: 3 de 4 sin grafo, 4 de 4 con GraphSAGE y 3 de 4 sin reranker.
- El agente se quedó con el reranker sin grafo, decidido antes de mirar `test`.

**Escenarios, voz y latencia**

- Escenarios por texto: 20 de 20, sin incumplir cantidades, presupuesto ni existencias, y sin pedidos duplicados. Antes de añadir las validaciones por código eran 14 de 20.
- Escenarios por voz con las 31 grabaciones de Piero: 6 de 6, también con la transcripción correcta.
- ASR: 1,4 % de palabras mal transcritas; errores en 0 de 3 importes, 0 de 8 cantidades y 1 de 13 nombres de producto.
- Voz generada: Whisper entiende mal el 5,1 % de las palabras. La semejanza con grabaciones reales de Piero es 0,40, frente a 0,27 de la voz anterior (XTTS-v2), y él mismo la validó de oído.
- Latencia en la T4, desde que termina la grabación hasta que la respuesta puede sonar: entre 23 y 25 s por turno con LLM (ASR 0,4 s, LLM 8,5 s, voz de 14 a 16 s). La carga inicial, de 89 a 108 s, se mide aparte.

**Errores y limitaciones** (el análisis recoge 6 aciertos y 9 fallos, con su causa)

- Corregidos con validaciones por código: «Ciérralo» no cerraba el pedido; añadía un producto que nadie había pedido; afirmaba algo que el catálogo no dice; «He dicho 12, no 2» fijó un presupuesto de 12 euros.
- Sin corregir: «cafetera» se transcribió «cafetería» y se compró otra cosa, y el escenario pasa igual; a veces dice que un dato no consta sin abrir el detalle del producto; las explicaciones tras un rechazo son pobres.
- Límites: no es tiempo real y más de la mitad del turno es la síntesis de voz; las respuestas que leen el carrito llegan a 40 s; las marcas que no son palabras se pronuncian deformadas; todo se midió con un hablante, un micrófono, una toma por turno y una semilla; la semejanza de la voz se midió con grabaciones de la misma sesión.

## Dónde está cada cosa

Todo lo que se muestra en pantalla está en este repositorio. Las cifras de este guion salen de esos archivos; si alguna no coincide, vale la del archivo.

| Para | Archivo |
| --- | --- |
| Diagrama del sistema y resumen | [README](../README.md), apartado «Cómo funciona» |
| Decisiones de diseño y modelos | [PLAN.md](PLAN.md), apartados 1 y 2 |
| Notebook de Colab | [notebooks/colab.ipynb](https://colab.research.google.com/github/pipaber/shopping_sts_agent/blob/main/notebooks/colab.ipynb) |
| Código de la búsqueda y del agente | [src/shopping_agent/](../src/shopping_agent) (`retrieval/`, `agent/`, `voice/`) |
| Los 20 escenarios | [scenarios/evaluacion/](../scenarios/evaluacion) |
| Tabla de recuperación en test | [results/retrieval_test.md](../results/retrieval_test.md) |
| Resumen de escenarios por corrida | [results/escenarios/resumen.md](../results/escenarios/resumen.md) |
| Corrida en Colab con la voz final | [results/colab_t4_f5/](../results/colab_t4_f5/LEEME.md) y README, apartado «Ejecución en Colab (T4)» |
| Aciertos, fallos y limitaciones | [ANALISIS_ACIERTOS_FALLOS.md](ANALISIS_ACIERTOS_FALLOS.md) |

**Pendiente de la entrega, además del video:** adjuntar en el formulario el zip con los audios (las grabaciones de Piero y las respuestas del agente), que no están en el repositorio porque es público.

Guion elaborado con asistencia de IA generativa (Claude Code). Cada integrante debe revisar su bloque contra los archivos enlazados antes de grabar, y conviene declarar el uso de IA en la entrega.
