# Diagnóstico de los escenarios que fallan

Seis de los 20 escenarios fallaban en la línea base ([results/escenarios_base/](../results/escenarios_base/resumen.md), 10 de noviembre de 2026). Este documento recoge, para cada uno, qué decidió el LLM, qué debía pasar y por qué no pasó, a partir de las fichas de las corridas. Elaborado con asistencia de IA generativa; conviene revisarlo con las fichas delante.

Lo que tienen en común: en ninguno falló la búsqueda, ni el formato de una llamada, ni una validación de la tienda. No hubo ninguna violación de restricciones. Falla la **decisión** del LLM: qué herramienta elige, sobre qué producto, o que actúa sin que se lo pidan. Las reglas que habrían evitado cada fallo estaban solo en el prompt, y el modelo de 7B no las aplica siempre.

| Escenario | Qué decidió el LLM | Qué debía pasar | Por qué no pasó |
|---|---|---|---|
| **03** cambio de cantidad (las cinco corridas) | Ante «Ciérralo.» eligió `responder` y repitió el carrito. El «Sí» siguiente no tenía cotización que confirmar. | `cotizar`, y esperar el sí. | Nada obliga a cotizar: que «ciérralo» significa cerrar el pedido solo lo dice la descripción de `cotizar`. La frase no nombra el pedido y viene justo después de un cambio de cantidad, y el modelo la toma como un acuse. Con «Cierra el pedido» sí cotiza. |
| **04** sin existencias (las cinco corridas) | `agregar_al_carrito` del primero → rechazado por agotado. Después consultó su stock y añadió el **segundo** candidato sin que nadie lo pidiera. | Explicar que está agotado y proponer otro, sin tocar el carrito. | La regla 9 del prompt dice que tras un rechazo proponga una salida, «otro producto» entre ellas. El modelo no propone: ejecuta. Ningún código comprobaba que el producto añadido fuera el que señaló el usuario («la primera»). |
| **06** cambio de stock (control, GraphSAGE y voz) | Tras el rechazo de la confirmación, ante «Vale, déjalo en una» eligió `quitar_del_carrito` y, con el control, añadió una alternativa. | `cambiar_cantidad` del mismo producto a 1. | El mensaje del agente (escrito por código) ofrece dos salidas a la vez: dejarlo en una unidad o una de tres alternativas, que además pasan a ser los CANDIDATOS. El LLM no ve en su contexto cuál era la oferta ni cómo se ejecuta, y lee «una» como una de las alternativas. Sin reranker salen otros candidatos y acierta. |
| **09** producto inexistente (las tres de texto) | Ante «Añade dos del séptimo», con cinco candidatos, añadió dos unidades de otro candidato. | Decir que no hay séptimo o preguntar. | La gramática solo deja escribir identificadores de candidatos, así que «no existe» no se puede expresar en una llamada; y la regla 5 dice que por «el primero, el segundo…» no se pida aclaración. Ningún código comprobaba que la posición nombrada existiera. |
| **10** atributo no verificable (control y sin reranker) | Con el control repitió `buscar_productos` con la misma consulta y volvió a presentar la lista. Sin reranker miró el detalle y dijo «los clientes no han valorado esta sartén». | Decir que el catálogo no indica ese dato. | Control: nada impide repetir una búsqueda que no aporta nada, y tras ella el modelo contesta a la búsqueda y no a la pregunta. Sin reranker: el modelo convierte «no consta» en una afirmación sobre el producto. La regla 1 pide decir que no consta, pero no cómo. Con GraphSAGE contesta bien. |
| **20** agotado al confirmar (control) | Ante «ponme dos de la primera alternativa» añadió la **segunda**. | Añadir la primera de las alternativas, que es el candidato 1. | Error del modelo al pasar de la posición al identificador. Una hipótesis, sin confirmar: cuenta el producto agotado, que aparece primero en el mensaje y sigue en el carrito, como el primero. Ningún código comprobaba que el producto añadido fuera el de la posición nombrada. |

De aquí salen los arreglos, por orden de preferencia: primero lo que se puede comprobar sin LLM y después lo que depende de interpretar la intención.

1. **Referencias por posición** (09, 20 y 04). Si el usuario señala un producto por su posición en la lista, el código puede comprobar que esa posición existe y que el producto que el LLM quiere añadir es ese.
2. **Cierre del pedido** (03). Si el mensaje pide cerrar la compra, el turno no puede acabar sin haber intentado cotizar.
3. **Búsqueda repetida** (10). Repetir la misma consulta con los candidatos ya delante no aporta nada: se rechaza y el LLM tiene que elegir otra cosa.
4. **Oferta pendiente** (06). El contexto del LLM debe decir qué se le ofreció al usuario tras un rechazo y con qué herramienta se ejecuta cada salida.
5. **Prompt** (04 y 10). Tras un rechazo, proponer no es ejecutar; y un dato que no aparece se dice como «el catálogo no lo indica», no como un hecho sobre el producto.

## Arreglos y resultados

Corridas repetidas el 10 de noviembre de 2026 con el agente corregido ([results/escenarios/resumen.md](../results/escenarios/resumen.md)); la línea base está en [results/escenarios_base/](../results/escenarios_base/resumen.md).

| Corrida | Antes | Después | Arreglados | Regresiones al final |
|---|---|---|---|---|
| `texto` (control, por defecto) | 14 de 20 | 20 de 20 | 03, 04, 06, 09, 10, 20 | ninguna |
| `texto_sage` (GraphSAGE) | 16 de 20 | 20 de 20 | 03, 04, 06, 09 | ninguna |
| `texto_sin_reranker` | 16 de 20 | 20 de 20 | 03, 04, 09, 10 | ninguna |
| `voz_sintetica` (audio sintético) | 3 de 6 | 6 de 6 | 03, 04, 06 | ninguna |
| `voz_texto_correcto` | 3 de 6 | 6 de 6 | 03, 04, 06 | ninguna |

Sigue sin haber ninguna violación de restricciones.

Qué arreglo corrigió qué:

| Arreglo | Tipo | Escenarios |
|---|---|---|
| Lo que el usuario señala por su posición es lo que se añade; una posición que no existe acaba en una pregunta | guarda por código y aviso al LLM | 09, 20 y, en 04, que ya no añade otro producto por su cuenta |
| Si el usuario pide cerrar la compra, el turno no acaba sin cotizar | guarda por código y aviso al LLM | 03 |
| Una búsqueda que devuelve los mismos candidatos se rechaza | guarda por código | 10 con el control |
| Tras rechazarse la confirmación, el LLM ve qué se ofreció y con qué herramienta se hace | contexto escrito por código | 06 |
| Ante un producto agotado, si el LLM no cita otro, el código añade dos con existencias | texto escrito por código | 04, la parte de proponer una alternativa |
| Tras un rechazo, proponer no es hacer; un dato ausente no es un hecho | prompt | apoyo a 04 y 10 |
| Recordatorio al final del detalle de un producto | resultado escrito por código | regresión de 10 (ver abajo) |
| Tras rechazarse una cantidad, el LLM ve cuántas unidades caben | contexto escrito por código | regresión de 15 (ver abajo) |

No se midió cada arreglo por separado: se aplicaron juntos y se repitieron las corridas. Lo que sí se vio por el camino:

- **Con los cinco primeros**, el control pasó de 14 a 19: quedaba 04, que ya no tocaba el carrito pero contestaba «¿te interesa alguna de las demás opciones?» sin nombrar ninguna. De ahí el arreglo de las alternativas.
- **Regresión en 10 con GraphSAGE.** Con el prompt nuevo el LLM mira el detalle antes de contestar, como se le pide, y después presentó la descripción del vendedor como la opinión de los clientes («los clientes valoran positivamente la versatilidad…»). Antes, con GraphSAGE, contestaba bien sin mirar el detalle. Con el control la comprobación pasaba solo porque la respuesta terminaba con «el catálogo no indica valoraciones». El recordatorio al final del detalle lo corrigió en las tres configuraciones.
- **Regresión en 15 sin reranker.** Ante «Pues ponme las tres que quedan» el LLM comparó tres productos en vez de añadir tres unidades. No intervino ninguna guarda: con el prompt nuevo su respuesta anterior quedó redactada de otra forma y leyó «las tres» de otra manera. Se corrigió dándole en el contexto la cantidad que la tienda dijo que cabía.

Estas dos regresiones enseñan el límite del método: cada cambio en lo que ve el LLM mueve otras respuestas, y solo se detecta lo que algún escenario comprueba.

## Escenarios de reserva

Cuatro escenarios escritos antes de tocar el agente ([scenarios/reserva/](../scenarios/reserva/)), con otros productos y otra redacción, y corridos una sola vez al final, en las tres configuraciones:

| Escenario | control | GraphSAGE | sin reranker |
|---|---|---|---|
| 21 cerrar el pedido con otras palabras («Eso es todo, ya puedes tramitarlo», «Listo, quiero pagar ya») | ✔ | ✔ | ✔ |
| 22 producto agotado que no es el primero | ✔ | ✔ | ✔ |
| 23 candidato que no está en la lista («el sexto», «el octavo») y después uno que sí | ✔ | ✔ | ✔ |
| 24 dato que el catálogo no trae (garantía, plazo de entrega) | ✘ | ✔ | ✘ |

Los dos fallos de 24 son de la comprobación y no del agente. La comprobación decide si el catálogo trae el dato buscando palabras clave en el texto del producto, y las que se eligieron casan con frases que no hablan de lo preguntado: «garant» con «garantiza la comodidad» y «24 horas» con «resolveremos el problema por usted dentro de las 24 horas». El catálogo no dice ni los años de garantía ni el plazo de entrega, y el agente contestó en los dos casos que el catálogo no lo indica, que es lo correcto. La expectativa se deja como está, mal planteada, y el resultado se reporta así: 3 de 4, 4 de 4 y 3 de 4.

Dos matices sobre esta comprobación de generalidad. Los escenarios de reserva los escribió la misma sesión que hizo los arreglos: no se ejecutaron antes, pero su redacción era conocida al escribir las guardas. Y son cuatro: dicen que las guardas no dependen de la redacción exacta de los 20, no que el agente acierte en general.

## Lo que sigue flojo

- **Las explicaciones.** En 08 el carrito queda vacío, como debe, pero ante «añade cero unidades» el agente sigue contestando cosas como «ese producto no está en el carrito» o «hecho». Las comprobaciones miran la tienda, no si la explicación es buena.
- **Preguntas poco útiles.** Ante «ponme el sexto» de cinco, a veces pregunta «¿cuál es el sexto de la lista que te interesa?» sin decir que solo hay cinco. No añade nada, pero no aclara.
- **Mirar el detalle antes de decir que no consta.** En el escenario 24 con el control contestó que el catálogo no indica la garantía sin consultar el detalle del producto. Acertó, pero sin comprobarlo.
- **Lo que las guardas no reconocen.** Solo los ordinales con artículo («el segundo») y una lista corta de formas de cerrar la compra. Con «el número dos» o «ya lo tengo todo» decide el LLM, como antes.
- **Sin verificar:** Colab y el juicio de oído. La evaluación de recuperación en test no se ha vuelto a correr.
- **Con las grabaciones del usuario** (11 de noviembre, después de este diagnóstico y sin tocar el agente): los cinco escenarios con grabaciones completas pasan, pero en 01 el ASR entendió «cafetería» por «cafetera» y se compró otro producto sin que las comprobaciones lo vean. Está en [PLAN.md](PLAN.md), «Voz con las grabaciones del usuario».
