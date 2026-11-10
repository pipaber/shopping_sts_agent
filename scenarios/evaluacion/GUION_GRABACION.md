# Guion de grabación de los escenarios de voz

Generado con `python -m shopping_agent.eval.scenarios --recording-script` a partir de los JSON de
esta carpeta; no se edita a mano. Un archivo por turno, con el texto dicho tal cual: es la
transcripción correcta con la que se compara el ASR. Formato y consejos de grabación, en el README.

## 01_compra_confirmada — Compra confirmada

| Archivo | Texto que hay que decir |
|---|---|
| `audio/escenarios/01_compra_confirmada/01.wav` | Hola, busco una cafetera italiana. Tengo un presupuesto de 60 euros. |
| `audio/escenarios/01_compra_confirmada/02.wav` | Añade dos de la primera al carrito. |
| `audio/escenarios/01_compra_confirmada/03.wav` | Quiero cerrar el pedido. |
| `audio/escenarios/01_compra_confirmada/04.wav` | Sí, confirmo. |

## 02_pedido_ambiguo — Pedido ambiguo que requiere aclaración

| Archivo | Texto que hay que decir |
|---|---|
| `audio/escenarios/02_pedido_ambiguo/01.wav` | Quiero comprar un regalo para mi hermana. |
| `audio/escenarios/02_pedido_ambiguo/02.wav` | Unos auriculares bluetooth, y no quiero gastar más de 50 euros. |
| `audio/escenarios/02_pedido_ambiguo/03.wav` | Ponme uno del primero. |

## 03_cambio_cantidad — Cambio de cantidad manteniendo las demás restricciones

| Archivo | Texto que hay que decir |
|---|---|
| `audio/escenarios/03_cambio_cantidad/01.wav` | Busco una botella de agua de acero inoxidable. Mi presupuesto es de 45 euros. |
| `audio/escenarios/03_cambio_cantidad/02.wav` | Añade dos de la primera. |
| `audio/escenarios/03_cambio_cantidad/03.wav` | Mejor que sean cuatro. |
| `audio/escenarios/03_cambio_cantidad/04.wav` | Ciérralo. |
| `audio/escenarios/03_cambio_cantidad/05.wav` | Sí. |

## 04_sin_existencias — Producto sin existencias que requiere alternativa

| Archivo | Texto que hay que decir |
|---|---|
| `audio/escenarios/04_sin_existencias/01.wav` | Necesito una esterilla de yoga. |
| `audio/escenarios/04_sin_existencias/02.wav` | Ponme una de la primera. |
| `audio/escenarios/04_sin_existencias/03.wav` | Entonces ponme una de la segunda. |
| `audio/escenarios/04_sin_existencias/04.wav` | Cierra el pedido. |
| `audio/escenarios/04_sin_existencias/05.wav` | Sí, confirmo. |

## 05_correccion_transcripcion — Corrección de una transcripción antes de comprar

| Archivo | Texto que hay que decir |
|---|---|
| `audio/escenarios/05_correccion_transcripcion/01.wav` | Busco un ratón inalámbrico. |
| `audio/escenarios/05_correccion_transcripcion/02.wav` | Añade dos del primero. |
| `audio/escenarios/05_correccion_transcripcion/03.wav` | Cierra el pedido. |
| `audio/escenarios/05_correccion_transcripcion/04.wav` | No, espera, he dicho doce, no dos. |
| `audio/escenarios/05_correccion_transcripcion/05.wav` | Ahora sí, cierra el pedido. |
| `audio/escenarios/05_correccion_transcripcion/06.wav` | Sí, confirmo. |

## 06_cambio_stock_confirmacion_repetida — Cambio de stock entre cotización y confirmación, y confirmación repetida

| Archivo | Texto que hay que decir |
|---|---|
| `audio/escenarios/06_cambio_stock_confirmacion_repetida/01.wav` | Busco una lámpara de escritorio LED. |
| `audio/escenarios/06_cambio_stock_confirmacion_repetida/02.wav` | Añade tres de la primera. |
| `audio/escenarios/06_cambio_stock_confirmacion_repetida/03.wav` | Quiero cerrar el pedido. |
| `audio/escenarios/06_cambio_stock_confirmacion_repetida/04.wav` | Sí. |
| `audio/escenarios/06_cambio_stock_confirmacion_repetida/05.wav` | Vale, déjalo en una. |
| `audio/escenarios/06_cambio_stock_confirmacion_repetida/06.wav` | Cierra el pedido. |
| `audio/escenarios/06_cambio_stock_confirmacion_repetida/07.wav` | Sí. |
| `audio/escenarios/06_cambio_stock_confirmacion_repetida/08.wav` | Sí. |
