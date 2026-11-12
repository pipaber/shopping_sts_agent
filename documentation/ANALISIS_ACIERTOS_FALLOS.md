# Análisis de aciertos y fallos

Seis aciertos y nueve fallos del sistema, cada uno con lo que se pidió, lo que hizo el sistema, dónde se ve y por qué pasó. Todos salen de corridas guardadas en `results/`; las fichas enlazadas traen la conversación completa, con cada operación y cada comprobación. Elaborado con asistencia de IA generativa; conviene revisarlo con las fichas delante.

Dos avisos para leerlo bien:

- **«Correcto» significa que se cumplieron las comprobaciones del escenario**, que miran la tienda (carrito, pedidos, existencias, presupuesto) y algunas frases de la respuesta. No miran si la explicación es buena ni, en algún caso, si el producto es el que se pidió. Donde un escenario pasa sin que eso esté bien, aquí cuenta como fallo.
- **Los 20 escenarios son el conjunto con el que se ajustó el agente.** El 20 de 20 no es una tasa de aciertos general. Los escenarios de reserva (21 a 26), escritos antes de cada arreglo y corridos una sola vez, son la única comprobación de que los arreglos no dependen de la redacción.

| | Caso | Estado |
|---|---|---|
| A1 | La confirmación repetida no duplica el pedido | funciona |
| A2 | La tienda cambia entre la cotización y el sí | funciona |
| A3 | Corregir antes de comprar | funciona |
| A4 | La tienda dice no: presupuesto y existencias | funciona; la explicación es mejorable |
| A5 | Memoria de preferencias entre conversaciones | funciona; el LLM hace un paso de más |
| A6 | Reordenar los candidatos mejora la búsqueda, también en test | funciona |
| F1 | «Ciérralo» no cerraba el pedido | corregido |
| F2 | Añadía un producto que nadie había pedido | corregido |
| F3 | Afirmaba algo que el catálogo no dice | corregido |
| F4 | «He dicho 12, no 2» fijó un presupuesto de 12 € | corregido |
| F5 | «Cafetera» se entendió «cafetería» y se compró otra cosa | **sin corregir**, y el escenario pasa |
| F6 | Dice que un dato no consta sin abrir el detalle | **sin corregir** |
| F7 | Una respuesta hablada sale ininteligible | **sin corregir** |
| F8 | Explicaciones pobres tras un rechazo | **sin corregir** |
| F9 | El grafo aporta poco | límite del resultado, no un error |

## Aciertos

### A1. La confirmación repetida no duplica el pedido

- **Qué se pidió.** Con el pedido ya registrado, el usuario vuelve a decir «Sí».
- **Qué hizo.** `confirmar_pedido` devolvió «el pedido ya estaba registrado; no se duplicó» y el agente contestó «Ese pedido ya estaba registrado con el número 1, así que no lo he duplicado». Queda un solo pedido y las existencias bajan una sola vez.
- **Evidencia.** [voz/06](../results/escenarios/voz/06_cambio_stock_confirmacion_repetida.md), turnos 7 y 8, con las grabaciones del usuario. También [voz/01](../results/escenarios/voz/01_compra_confirmada.md).
- **Por qué funciona.** No depende de que el LLM se acuerde. Cada cotización tiene un identificador y la tienda registra el pedido con él: confirmar dos veces la misma cotización es la misma operación. Además, el «sí» que llega mientras se espera la confirmación lo resuelve el código y no pasa por el LLM (por eso ese turno tarda 2 s y no 12).

### A2. La tienda cambia entre la cotización y el sí

- **Qué se pidió.** Tres lámparas. El agente repite el pedido y, antes del «Sí», la tienda se queda con una sola unidad.
- **Qué hizo.** La confirmación se rechazó (`stock_insuficiente`), no se registró nada ni se tocó el carrito, y el agente explicó el motivo y ofreció dos salidas: dejarlo en una unidad o una de tres alternativas con existencias. El usuario dijo «Vale, déjalo en una», el agente cambió la cantidad, volvió a cotizar y esperó otro sí.
- **Evidencia.** [voz/06](../results/escenarios/voz/06_cambio_stock_confirmacion_repetida.md), turnos 3 a 7. La variante en la que el producto se agota del todo y se cambia por otro: [texto/20](../results/escenarios/texto/20_agotado_al_confirmar.md).
- **Por qué funciona.** La confirmación vuelve a comprobar precio y existencias contra la tienda en el momento de registrar; la cotización no reserva nada. El mensaje del rechazo lo escribe el código, con las cifras de la tienda, y no el LLM. Y una confirmación rechazada obliga a cotizar de nuevo: no se puede comprar sin haber oído el pedido tal como queda.
- **Matiz.** Esta parte falló en la línea base (ver F2): el mecanismo de la tienda ya funcionaba, pero el LLM leía «déjalo en una» como «una de las alternativas».

### A3. Corregir antes de comprar

- **Qué se pidió.** El agente repite un pedido de dos ratones y el usuario corrige: «No, espera, he dicho doce, no dos». En otro escenario, a la pregunta «¿Lo confirmo?» contesta «Sí, pero que sean tres».
- **Qué hizo.** En los dos casos no registró el pedido que tenía cotizado. Cambió la cantidad, volvió a repetir el pedido y solo compró con un sí limpio: doce ratones por 132,00 € y tres paraguas por 27,00 €.
- **Evidencia.** [voz/05](../results/escenarios/voz/05_correccion_transcripcion.md), turnos 3 a 6, y [texto/13](../results/escenarios/texto/13_confirmacion_con_cambio.md).
- **Por qué funciona.** Solo cuenta como confirmación una respuesta que es un sí y nada más; eso lo decide el código. «Sí, pero…» va al LLM como un mensaje normal, y cualquier cambio en el carrito invalida la cotización anterior.
- **Matiz.** El caso de «doce, no dos» por voz solo pasa desde la corrección de F4: la primera vez falló.

### A4. La tienda dice no: presupuesto y existencias

- **Qué se pidió.** Con 30 € de presupuesto, tres mochilas de 12 €. En otro escenario, cinco linternas cuando quedan tres.
- **Qué hizo.** Las dos operaciones se rechazaron y el carrito no cambió: `presupuesto_excedido` («El total sería 36,00 € y supera el presupuesto de 30,00 € por 6,00 €. Dentro del presupuesto caben como máximo 2 unidades») y `stock_insuficiente` («Solo quedan 3 unidades»). Después el usuario pidió lo que sí cabía y se añadió.
- **Evidencia.** [texto/07](../results/escenarios/texto/07_presupuesto_excedido.md) y [texto/15](../results/escenarios/texto/15_stock_insuficiente.md).
- **Por qué funciona.** El LLM propone la operación y la tienda la valida entera o no la hace: no hay cambios a medias. En ninguna corrida, ni antes ni después de corregir el agente, hubo una violación de restricciones (cantidad, presupuesto, existencias, pedido duplicado, cambio parcial).
- **Matiz.** La tienda lo dice bien y el agente lo cuenta peor. En el caso del presupuesto contestó «¿Te interesa una unidad o quieres buscar otro?» cuando la tienda le había dicho que cabían dos. Es F8.

### A5. Memoria de preferencias entre conversaciones

- **Qué se pidió.** En una conversación: «Recuerda para otras veces que prefiero el color azul». En otra nueva, con otro hilo y el mismo usuario: «¿Recuerdas qué color prefiero?».
- **Qué hizo.** Contestó «Sí, he guardado tu preferencia de color azul».
- **Evidencia.** [texto/12](../results/escenarios/texto/12_memoria_preferencias.md).
- **Por qué funciona.** Hay dos memorias distintas en Postgres. La conversación (carrito, candidatos, cotización) se guarda por hilo y no pasa a otra conversación. Las preferencias se guardan por usuario en el Store y se cargan al empezar cualquier conversación suya.
- **Matiz.** En la segunda conversación el LLM volvió a llamar a `guardar_preferencia("color azul")` antes de contestar. No hace daño, porque guardar lo ya guardado no cambia nada, pero es un paso que sobra.

### A6. Reordenar los candidatos mejora la búsqueda, también en test

- **Qué se pidió.** Ordenar los productos de cada consulta de ESCI; se mide con nDCG@10.
- **Qué hizo.** El reranker que usa el agente (el control sin grafo, sobre los 50 primeros del híbrido) mejora al híbrido en +0,018 en validación y en +0,018 en test (0,7113 → 0,7292; IC 95 % de la diferencia [+0,0086; +0,0275]). El híbrido recupera más productos exactos entre los 50 primeros que el denso solo (0,719 frente a 0,650).
- **Evidencia.** [results/retrieval_test.md](../results/retrieval_test.md) y [results/reranker_validation.md](../results/reranker_validation.md).
- **Por qué funciona.** El híbrido trae buenos candidatos pero los ordena peor que el denso; el reranker aprende, con las etiquetas de 1 200 consultas de ajuste, a combinar las dos señales.
- **Por qué es creíble.** Test se evaluó una sola vez, con todo ya decidido, y la mejora medida fue la misma que en validación. El comando se niega a repetirse.
- **Matiz.** Es una mejora de 2 puntos de nDCG sobre 71. Y lo que añade el grafo sobre este control es todavía menos (F9).

## Fallos

### F1. «Ciérralo» no cerraba el pedido (corregido)

- **Qué se pidió.** Tras cambiar la cantidad a cuatro: «Ciérralo».
- **Qué hizo.** Repitió el carrito («Hecho, el carrito ahora tiene 4 unidades… ¿Necesitas algo más?») sin cotizar. El «Sí» siguiente no tenía nada que confirmar y no se registró ningún pedido. Pasó en las cinco corridas de la línea base.
- **Evidencia.** [línea base, texto/03](../results/escenarios_base/texto/03_cambio_cantidad.md); corregido en [texto/03](../results/escenarios/texto/03_cambio_cantidad.md).
- **Causa.** Nada obligaba a cotizar. Que «ciérralo» significa cerrar la compra solo lo decía la descripción de una herramienta, y el LLM de 7B tomó la frase, que no nombra el pedido, como un acuse. Con «Cierra el pedido» sí cotizaba.
- **Arreglo.** Una guarda por código: si el mensaje pide cerrar la compra, el turno no termina sin haber intentado cotizar. Comprobado con otras frases en el escenario de reserva 21 («Eso es todo, ya puedes tramitarlo», «Listo, quiero pagar ya»): pasa en las tres configuraciones.
- **Lo que queda.** La guarda reconoce una lista corta de formas de cerrar. Con «ya lo tengo todo» decide el LLM, como antes.

### F2. Añadía un producto que nadie había pedido (corregido)

- **Qué se pidió.** Tres situaciones: «Ponme una de la primera» cuando la primera está agotada; «Añade dos del séptimo» con cinco candidatos en la lista; «ponme dos de la primera alternativa».
- **Qué hizo.** En la primera, tras el rechazo por agotado añadió por su cuenta el segundo candidato, y el pedido final salió con dos unidades de un producto que el usuario no eligió. En la segunda añadió dos unidades de otro candidato. En la tercera añadió la segunda alternativa.
- **Evidencia.** Línea base: [texto/04](../results/escenarios_base/texto/04_sin_existencias.md), [texto/09](../results/escenarios_base/texto/09_producto_inexistente.md) y [texto/20](../results/escenarios_base/texto/20_agotado_al_confirmar.md). Corregido: [texto/04](../results/escenarios/texto/04_sin_existencias.md), [texto/09](../results/escenarios/texto/09_producto_inexistente.md), [texto/20](../results/escenarios/texto/20_agotado_al_confirmar.md).
- **Causa.** La tienda validaba que el producto existiera y tuviera existencias, pero ningún código comprobaba que fuera el que señaló el usuario. El LLM solo puede escribir identificadores de candidatos, así que «no hay séptimo» no se podía expresar en una llamada; y tras un rechazo, en vez de proponer una salida la ejecutaba.
- **Arreglo.** Si el usuario señala un producto por su posición, el código comprueba que esa posición existe y que el producto que se va a añadir es ese; una posición que no existe acaba en una pregunta. Comprobado en los escenarios de reserva 22 y 23.
- **Lo que queda.** Solo reconoce ordinales con artículo («el segundo»). Con «el número dos» decide el LLM. Y la pregunta que hace a veces no ayuda: «¿cuál es el sexto de la lista que te interesa?», sin decir que solo hay cinco.
- **Del mismo tipo.** En el escenario 06, ante «Vale, déjalo en una» el LLM quitó el producto y añadió una alternativa: leyó «una» como una de las alternativas. Se corrigió dándole en el contexto qué se le había ofrecido al usuario y con qué herramienta se hace cada salida.

### F3. Afirmaba algo que el catálogo no dice (corregido)

- **Qué se pidió.** «¿Qué valoración le dan los clientes a la primera?». El catálogo no trae valoraciones.
- **Qué hizo.** Con el reranker por defecto repitió la búsqueda y volvió a recitar la lista, sin contestar. Sin reranker miró el detalle y dijo «los clientes no han valorado esta sartén»: convirtió «no consta» en un hecho sobre el producto.
- **Evidencia.** [línea base, texto/10](../results/escenarios_base/texto/10_atributo_no_verificable.md); corregido en [texto/10](../results/escenarios/texto/10_atributo_no_verificable.md): «El catálogo no indica valoraciones de los clientes para este producto».
- **Causa.** Nada impedía repetir una búsqueda que no aporta nada, y la regla de decir que un dato no consta estaba solo en el prompt, sin decir cómo.
- **Arreglo.** Una búsqueda que devuelve los mismos candidatos se rechaza; y el detalle de un producto termina con un recordatorio de que lo que no aparece ahí no consta.
- **Lo que enseñó.** El primer arreglo rompió otra corrida: con GraphSAGE, que antes contestaba bien, el agente empezó a presentar la descripción del vendedor como la opinión de los clientes. Y el prompt nuevo rompió el escenario 15 sin reranker: ante «Pues ponme las tres que quedan» comparó tres productos en vez de añadir tres unidades. Las dos regresiones se corrigieron. Cada cambio en lo que ve el LLM mueve otras respuestas, y solo se detecta lo que algún escenario comprueba.

### F4. «He dicho 12, no 2» fijó un presupuesto de 12 € (corregido)

- **Qué se pidió.** Con la voz real del usuario: «No, espera, he dicho doce, no dos».
- **Qué hizo.** Whisper lo escribió con cifras, «he dicho 12, no 2», y con esa frase el LLM llamó a `fijar_presupuesto(12)` en vez de `cambiar_cantidad(12)`. El carrito siguió con dos unidades, la cotización se rechazó dos veces por superar los 12 € y no se compró nada.
- **Evidencia.** [results/diagnostico_voz_05/](../results/diagnostico_voz_05/LEEME.md): el mismo escenario por texto, cambiando solo esa frase, falla igual. Corregido en [voz/05](../results/escenarios/voz/05_correccion_transcripcion.md).
- **Causa.** No fue una palabra mal entendida: los números eran los correctos. Fue la forma de escribirlos. Las métricas del ASR no lo ven, porque al normalizar «12» y «doce» son lo mismo y el turno cuenta como idéntico.
- **Arreglo.** Una guarda (con productos en el carrito, `fijar_presupuesto` se rechaza si el mensaje no habla de dinero) y un aviso al LLM en esa misma situación. Comprobado con otra frase y otro producto en los escenarios de reserva 25 y 26.
- **Lo que queda.** «Súbelo a 80» con el carrito lleno se rechaza y el agente pregunta: una pregunta de más. Otras lecturas equivocadas de una cifra las sigue decidiendo el LLM.

### F5. «Cafetera» se entendió «cafetería» y se compró otra cosa (sin corregir)

- **Qué se pidió.** Con la voz real: «Hola, busco una cafetera italiana. Tengo un presupuesto de 60 euros».
- **Qué hizo.** Whisper entendió «cafetería italiana». El agente buscó eso y el primer candidato fue un paquete de 120 cápsulas de café, que además presentó como «una cafetera Nespresso de FRHOME». El usuario añadió dos «de la primera» y el pedido final son dos paquetes de cápsulas. Con la transcripción correcta, el primer candidato es una cafetera De'Longhi.
- **Evidencia.** [voz/01](../results/escenarios/voz/01_compra_confirmada.md) frente a [voz_texto_correcto/01](../results/escenarios/voz_texto_correcto/01_compra_confirmada.md); la tabla «Audio frente a transcripción correcta» del [resumen](../results/escenarios/resumen.md) lo marca como el único escenario con otra tienda final.
- **Causa.** Un error del ASR en una sola palabra, justo la que define la búsqueda. Nada después lo puede detectar: la consulta es válida, hay candidatos y el importe y la cantidad se entendieron bien.
- **El escenario cuenta como correcto, y no debería leerse así.** Sus comprobaciones se refieren al «primer candidato», al que la tienda fija precio y existencias para que el resultado no dependa de qué producto salga. Ninguna mira que sea una cafetera. La expectativa se dejó como estaba para no cambiar lo que se espera a posteriori. El 6 de 6 por voz dice que el flujo y la tienda son coherentes en los seis escenarios, no que en los seis se comprara lo pedido: en uno no.
- **Por qué no se ha arreglado.** Hay dos salidas, las dos sin probar: darle a Whisper vocabulario del dominio, o que el agente diga en voz alta qué ha buscado para que el usuario lo oiga. Las dos tocan el comportamiento y habría que volver a correr la evaluación. Con una toma por turno tampoco se sabe si es sistemático: en 31 grabaciones hay dos palabras cambiadas y solo esta cambió la compra.

### F6. Dice que un dato no consta sin abrir el detalle (sin corregir)

- **Qué se pidió.** «¿Cuántos años de garantía tiene la segunda?», sobre una silla de oficina.
- **Qué hizo.** Contestó «El catálogo no indica cuántos años de garantía tiene esa silla» sin llamar a `detalle_producto`. Acertó, porque el catálogo no lo dice, pero no lo comprobó: contestó con lo que tenía de la lista.
- **Evidencia.** [reserva/24](../results/escenarios/reserva/24_dato_que_no_consta.md), turno 2, con el reranker por defecto.
- **Causa.** El recordatorio de F3 está al final del detalle de un producto: solo actúa si el LLM lo abre. Nada le obliga a abrirlo antes de decir que algo no consta.
- **El escenario cuenta como fallo, por otro motivo.** La comprobación decide si el catálogo trae el dato buscando palabras clave en el texto del producto, y «garant» casa con «garantiza la comodidad». Así que marca como error una respuesta que era correcta. Son dos problemas distintos en el mismo turno: una expectativa mal planteada, que se dejó como está, y un agente que acierta sin mirar.
- **Por qué no se ha arreglado.** Obligar a abrir el detalle antes de cualquier «no consta» añade una llamada al LLM (unos 3 s) a preguntas que ya se contestan bien, y es otro cambio en lo que ve el LLM, con el riesgo visto en F3.

### F7. Una respuesta hablada sale ininteligible (sin corregir)

- **Qué se pidió.** «Unos auriculares Bluetooth y no quiero gastar más de 50 euros». La respuesta enumera cinco candidatos de marcas «Mgrett», «TAIN», «WDGP», «GSBLBL» y «HoLiv».
- **Qué hizo.** El texto de la respuesta es correcto. El audio, con la voz nueva del agente, no: dura 32 s donde con la voz anterior duraba 49, y Whisper entiende en el último tramo palabras sin relación con el texto. Son 20 de los 73 errores de inteligibilidad de toda la corrida.
- **Evidencia.** [voz/02](../results/escenarios/voz/02_pedido_ambiguo.md), turno 2; el detalle por respuesta, en `results/escenarios/voz/metricas_voz.json`. El audio está en `audio/corridas/voz/02_pedido_ambiguo/respuesta_02.wav`, fuera de git.
- **Causa.** XTTS-v2 con marcas que no son palabras pronunciables. Sale mal a todas las velocidades medidas, así que no es la velocidad; y con la referencia anterior salía entero, así que depende de la grabación de referencia.
- **Por qué no se ha arreglado.** Falta lo primero: que alguien lo escuche. La medida es de Whisper, que no es un oyente. Las salidas posibles (otra toma de referencia, no leer en voz alta las marcas que no son palabras, respuestas habladas más cortas) no se han probado, y la segunda toca el texto que redacta el agente.
- **Relacionado.** La voz nueva se entiende peor que la anterior según Whisper (5,5 % de WER frente a 3,4 %), y además de este caso añade a veces palabras sueltas al final de un fragmento. El detalle está en el PLAN, «Voz del agente: referencia nueva y velocidad».

### F8. Explicaciones pobres tras un rechazo (sin corregir)

- **Qué se pidió.** «Añade cero unidades del primero» y después «Añade menos dos unidades del primero».
- **Qué hizo.** El carrito quedó vacío, como debe. Pero la explicación fue «Ese producto no está en el carrito. ¿Quieres añadirlo o buscas otro?», las dos veces: el LLM había elegido `quitar_del_carrito`, que se rechazó, y contó ese rechazo en lugar de decir que la cantidad no es válida.
- **Evidencia.** [texto/08](../results/escenarios/texto/08_cantidad_invalida.md). Del mismo tipo, en [texto/07](../results/escenarios/texto/07_presupuesto_excedido.md): la tienda dice que caben dos unidades y el agente ofrece una.
- **Causa.** El código garantiza que la tienda no cambia y que las cifras de la respuesta son las de la tienda. La frase la redacta el LLM a partir del resultado de la herramienta que eligió, y si eligió una que no venía a cuento, explica lo que no era.
- **El escenario pasa**, porque sus comprobaciones miran la tienda. Es el límite de una evaluación por código: no juzga si la explicación sirve.
- **Por qué no se ha arreglado.** Haría falta que el código escribiera más respuestas, como ya hace con los rechazos de la confirmación, o un juicio de las explicaciones que no existe. No se hizo por tiempo.

### F9. El grafo aporta poco (límite del resultado)

- **Qué se esperaba.** Que un reranker con GNN (GraphSAGE sobre un grafo de consultas y productos) ordenara mejor que el mismo modelo sin paso de mensajes.
- **Qué salió.** En validación, +0,0035 de nDCG@10 con un intervalo que incluye el cero ([−0,0001; +0,0073]). En test, +0,0071 con un intervalo que lo excluye ([+0,0028; +0,0117]). Y en los escenarios no se distinguen: 20 de 20 con el control, con GraphSAGE y sin reranker.
- **Evidencia.** [results/reranker_validation.md](../results/reranker_validation.md), [results/retrieval_test.md](../results/retrieval_test.md) y el [resumen](../results/escenarios/resumen.md) de los escenarios.
- **Causa.** Con los embeddings congelados, el coseno y BM25 ya dan casi toda la señal y queda poco que propagar por el grafo. La única arista que aporta por sí sola es la de productos parecidos; las de etiquetas no añaden nada medible.
- **Qué se decidió.** El agente usa por defecto el control, sin grafo. La decisión se tomó con la validación, antes de ver test, y no se ha cambiado después: cambiarla ahora sería elegir con test. GraphSAGE cuesta además +12 ms por consulta frente a +2 ms, y 230 MiB de VRAM frente a 102.
- **Cómo hay que contarlo.** El GNN está implementado y medido, y su efecto es real en test pero pequeño: un 1 % relativo. No es lo que hace funcionar al agente.

## Lo que sigue sin arreglar

| Qué | Por qué se deja así |
|---|---|
| Un error del ASR en la palabra que define la búsqueda cambia la compra (F5) | Las salidas tocan el comportamiento del agente y no se han probado; una sola toma no dice si es sistemático |
| El escenario 01 por voz pasa aunque se compró otra cosa (F5) | No se cambia una expectativa después de ver el resultado; se dice aquí |
| El agente dice «no consta» sin abrir el detalle (F6) | Obligarle añade latencia a preguntas que ya contesta bien y mueve otras respuestas |
| La comprobación del escenario 24 marca como error una respuesta correcta (F6) | Mismo criterio: la expectativa mal planteada se deja y se reporta 3 de 4 |
| Una respuesta con marcas impronunciables sale ininteligible con la voz nueva (F7) | Nadie la ha escuchado todavía; las salidas no se han probado |
| Explicaciones pobres cuando el LLM elige una herramienta que no venía a cuento (F8) | Las comprobaciones no las juzgan; arreglarlo es escribir más respuestas por código |
| Las guardas reconocen pocas formas de decir las cosas (F1, F2) | Fuera de «el segundo» o «cierra el pedido» decide el LLM, como antes |
| El grafo aporta un 1 % (F9) | Es el resultado de la ablación, no un error |

## Qué tienen en común

- **Los aciertos son del código; los fallos, de la decisión del LLM o de lo que le llega.** En ningún fallo falló una validación de la tienda ni hubo una violación de restricciones. Fallaba qué herramienta elegía el LLM, sobre qué producto, o qué texto recibía del ASR.
- **Los arreglos que duran son los que el código puede comprobar.** Una regla en el prompt no bastó en ninguno de los seis fallos de la línea base; una guarda por código, sí.
- **Cada arreglo mueve otra cosa.** Los arreglos rompieron dos escenarios que antes pasaban (F3). Por eso hay escenarios de reserva, y por eso el 20 de 20 solo dice que el agente está ajustado a esos 20.
- **Por voz, el eslabón más débil es el texto que entra y el audio que sale**, no el agente: una palabra del ASR (F5), una cifra escrita de otra forma (F4), una marca impronunciable (F7).
