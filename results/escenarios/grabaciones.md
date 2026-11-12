# Grabaciones del usuario frente al guion

Audios en `audio/escenarios` (sin versionar): 31 de 31 archivos, transcritos con el ASR del agente sin correr el agente.

- No corresponden a su turno: ninguno.
- De los 31 que sí corresponden, 29 se entienden igual que el guion tras normalizar; WER 1.4 %.
- Errores del ASR en importes: 0 de 3.
- Errores del ASR en cantidades: 0 de 8.
- Errores del ASR en nombres de producto: 1 de 13.

## 01_compra_confirmada

4 de 4 archivos.

| Archivo | Duración | Texto del guion | Lo que entiende el ASR | Resultado |
|---|---|---|---|---|
| `01` | 5.5 s | Hola, busco una cafetera italiana. Tengo un presupuesto de 60 euros. | Hola, busco una cafetería italiana. Tengo un presupuesto de 60 euros. | distinto (WER 9 %) |
| `02` | 3.7 s | Añade dos de la primera al carrito. | Añade dos de la primera al carrito. | igual |
| `03` | 2.5 s | Quiero cerrar el pedido. | Quiero cerrar el pedido. | igual |
| `04` | 2.4 s | Sí, confirmo. | Sí, confirmo. | igual |

## 02_pedido_ambiguo

3 de 3 archivos.

| Archivo | Duración | Texto del guion | Lo que entiende el ASR | Resultado |
|---|---|---|---|---|
| `01` | 5.5 s | Quiero comprar un regalo para mi hermana. | Quiero comprar un regalo para mi hermana. | igual |
| `02` | 5.4 s | Unos auriculares bluetooth, y no quiero gastar más de 50 euros. | Unos auriculares Bluetooth y no quiero gastar más de 50 euros. | igual |
| `03` | 2.7 s | Ponme uno del primero. | Ponme uno del primero. | igual |

## 03_cambio_cantidad

5 de 5 archivos.

| Archivo | Duración | Texto del guion | Lo que entiende el ASR | Resultado |
|---|---|---|---|---|
| `01` | 6.0 s | Busco una botella de agua de acero inoxidable. Mi presupuesto es de 45 euros. | Busco una botella de agua de acero inoxidable. Mi presupuesto es de 45 euros. | igual |
| `02` | 2.5 s | Añade dos de la primera. | Añade dos de la primera. | igual |
| `03` | 2.8 s | Mejor que sean cuatro. | Mejor que sean cuatro. | igual |
| `04` | 2.1 s | Ciérralo. | Cierralo. | igual |
| `05` | 2.0 s | Sí. | Sí. | igual |

## 04_sin_existencias

5 de 5 archivos.

| Archivo | Duración | Texto del guion | Lo que entiende el ASR | Resultado |
|---|---|---|---|---|
| `01` | 3.2 s | Necesito una esterilla de yoga. | Necesito una esterilla de yoga. | igual |
| `02` | 2.8 s | Ponme una de la primera. | Ponme una de la primera. | igual |
| `03` | 3.4 s | Entonces ponme una de la segunda. | Entonces ponme una de la segunda. | igual |
| `04` | 2.3 s | Cierra el pedido. | Cierra el pedido. | igual |
| `05` | 2.2 s | Sí, confirmo. | Sí, confirmo. | igual |

## 05_correccion_transcripcion

6 de 6 archivos.

| Archivo | Duración | Texto del guion | Lo que entiende el ASR | Resultado |
|---|---|---|---|---|
| `01` | 2.7 s | Busco un ratón inalámbrico. | Busca un ratón inalámbrico. | distinto (WER 25 %) |
| `02` | 2.6 s | Añade dos del primero. | Añade dos del primero. | igual |
| `03` | 2.3 s | Cierra el pedido. | Cierra el pedido. | igual |
| `04` | 4.2 s | No, espera, he dicho doce, no dos. | No, espera, he dicho 12, no 2. | igual |
| `05` | 3.0 s | Ahora sí, cierra el pedido. | Ahora sí, cierra el pedido. | igual |
| `06` | 2.6 s | Sí, confirmo. | Sí, confirmo. | igual |

## 06_cambio_stock_confirmacion_repetida

8 de 8 archivos.

| Archivo | Duración | Texto del guion | Lo que entiende el ASR | Resultado |
|---|---|---|---|---|
| `01` | 3.8 s | Busco una lámpara de escritorio LED. | Busco una lámpara de escritorio LED. | igual |
| `02` | 2.9 s | Añade tres de la primera. | Añade 3 de la primera. | igual |
| `03` | 2.9 s | Quiero cerrar el pedido. | Quiero cerrar el pedido. | igual |
| `04` | 1.7 s | Sí. | Sí. | igual |
| `05` | 2.7 s | Vale, déjalo en una. | Vale, déjalo en una. | igual |
| `06` | 2.5 s | Cierra el pedido. | Cierra el pedido. | igual |
| `07` | 1.9 s | Sí. | Sí. | igual |
| `08` | 1.9 s | Sí. | sí | igual |
