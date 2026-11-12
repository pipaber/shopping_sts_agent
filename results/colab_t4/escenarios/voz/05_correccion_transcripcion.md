# 05_correccion_transcripcion — Corrección de una transcripción antes de comprar

- Veredicto: **correcto**
- Entrada: audio (grabaciones del usuario)
- Tipo: `correccion_transcripcion`
- Qué se prueba: El agente repite el pedido con dos unidades y el usuario corrige antes de confirmar: había dicho doce (dos y doce se confunden con facilidad al transcribir). No debe registrarse nada con dos unidades; el pedido final lleva doce.

## Turno 1 (20.0 s)

**Usuario (transcripción del ASR):** Busca un ratón inalámbrico.

**Texto correcto:** Busco un ratón inalámbrico.

- `buscar_productos(consulta="ratón inalámbrico")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B08P34RJSX | Raton inalámbrico, Inphic 2.4G Raton inalámbrico Recargable con Receptor USB, 3 Niveles Ajustables De dpi para Computadora PortáTil, Pc, Mac, Computadora, Macbook, Plata | marca: INPHIC | color: plata | precio: 33,29 € |…

**Agente:** Tengo el ratón inalámbrico Inphic por 33,29 euros, el de Anmck por 23,61 y el de WisFox por 19,69 euros. ¿Te interesa alguno?

**Enviado al TTS:** Tengo el ratón inalámbrico Inphic por treinta y tres euros con veintinueve céntimos, el de Anmck por veintitrés coma sesenta y uno y el de WisFox por diecinueve euros con sesenta y nueve céntimos. ¿Te interesa alguno?

- ✔ `cart(empty=true)` — carrito: vacío

> `@elegido` = `B08P34RJSX` (candidate:1): Raton inalámbrico, Inphic 2.4G Raton inalámbrico Recargable con Receptor USB, 3 Niveles Ajustables De dpi para Computadora PortáTil, Pc, Mac, Computadora, Macbook, Plata

> **Suceso externo:** la tienda deja `B08P34RJSX` (@elegido) con precio 11,00 € y existencias 20.

## Turno 2 (15.0 s)

**Usuario (transcripción del ASR):** Añade dos del primero.

- `agregar_al_carrito(product_id="B08P34RJSX", cantidad=2)` → OK: hecho. Así queda el carrito. CARRITO: - id=B08P34RJSX | Raton inalámbrico, Inphic 2.4G Raton inalámbrico Recargable con… | 2 unidades × 11,00 € = 22,00 € | existencias: 20 Total del carrito: 22,00 €

**Agente:** Hecho, añadidas dos unidades. En el carrito hay 2 unidades de «Raton inalámbrico, Inphic 2.4G Raton inalámbrico Recargable con…» a 11,00 € cada una, 22,00 €. Total: 22,00 €.

**Enviado al TTS:** Hecho, añadidas dos unidades. En el carrito hay dos unidades de Raton inalámbrico a once euros cada una, veintidós euros. Total: veintidós euros.

- ✔ `cart(lines=[{"product": "@elegido", "quantity": 2}])` — carrito: 2 × B08P34RJSX

## Turno 3 (16.7 s)

**Usuario (transcripción del ASR):** Cierra el pedido.

- `cotizar()` → OK: cotización creada; falta la confirmación del usuario.

**Agente:** Te repito el pedido antes de registrarlo: 2 unidades de «Raton inalámbrico, Inphic 2.4G Raton inalámbrico Recargable con…» a 11,00 € cada una, 22,00 €. Total: 22,00 €. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar. *(esperando confirmación)*

**Enviado al TTS:** Te repito el pedido antes de registrarlo: dos unidades de Raton inalámbrico a once euros cada una, veintidós euros. Total: veintidós euros. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar.

- ✔ `awaiting_confirmation(value=true)` — esperando confirmación: sí
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 4 (32.9 s)

**Usuario (transcripción del ASR):** No, espera, he dicho 12, no 2.

**Texto correcto:** No, espera, he dicho doce, no dos.

- `cambiar_cantidad(product_id="B08P34RJSX", cantidad=12)` → OK: hecho. Así queda el carrito. CARRITO: - id=B08P34RJSX | Raton inalámbrico, Inphic 2.4G Raton inalámbrico Recargable con… | 12 unidades × 11,00 € = 132,00 € | existencias: 20 Total del carrito: 132,00 €

**Agente:** Hecho, añadidas 10 unidades más. En total, 12 unidades de «Raton inalámbrico, Inphic 2.4G Raton inalámbrico Recargable con…» a 11,00 € cada una, 132,00 €. Total: 132,00 €. En el carrito hay 12 unidades de «Raton inalámbrico, Inphic 2.4G Raton inalámbrico Recargable con…» a 11,00 € cada una, 132,00 €. Total: 132,00 €.

**Enviado al TTS:** Hecho, añadidas diez unidades más. En total, doce unidades de Raton inalámbrico a once euros cada una, ciento treinta y dos euros. Total: ciento treinta y dos euros. En el carrito hay doce unidades de Raton inalámbrico a once euros cada una, ciento treinta y dos euros. Total: ciento treinta y dos euros.

- ✔ `orders(count=0)` — pedidos registrados: 0
- ✔ `cart(lines=[{"product": "@elegido", "quantity": 12}])` — carrito: 12 × B08P34RJSX

## Turno 5 (15.6 s)

**Usuario (transcripción del ASR):** Ahora sí, cierra el pedido.

- `cotizar()` → OK: cotización creada; falta la confirmación del usuario.

**Agente:** Te repito el pedido antes de registrarlo: 12 unidades de «Raton inalámbrico, Inphic 2.4G Raton inalámbrico Recargable con…» a 11,00 € cada una, 132,00 €. Total: 132,00 €. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar. *(esperando confirmación)*

**Enviado al TTS:** Te repito el pedido antes de registrarlo: doce unidades de Raton inalámbrico a once euros cada una, ciento treinta y dos euros. Total: ciento treinta y dos euros. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar.

- ✔ `awaiting_confirmation(value=true)` — esperando confirmación: sí
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 6 (8.6 s)

**Usuario (transcripción del ASR):** Sí, confirmo.

- `confirmar_pedido(quote_id="5321b68b8a864105aa05972fce4df5e0")` → OK: pedido registrado

**Agente:** Pedido número 1 registrado: 12 unidades de «Raton inalámbrico, Inphic 2.4G Raton inalámbrico Recargable con…» a 11,00 € cada una, 132,00 €. Total: 132,00 €. Gracias por tu compra.

**Enviado al TTS:** Pedido número uno registrado: doce unidades de Raton inalámbrico a once euros cada una, ciento treinta y dos euros. Total: ciento treinta y dos euros. Gracias por tu compra.

- ✔ `orders(count=1)` — pedidos registrados: 1

## Comprobaciones finales

- ✔ `orders(count=1)` — pedidos registrados: 1
- ✔ `order(lines=[{"product": "@elegido", "quantity": 12}], total_cents=13200)` — pedido 1: 12 × B08P34RJSX; total 13200 céntimos
- ✔ `stock(product="@elegido", equals=8)` — existencias de B08P34RJSX: 8
- ✔ `cart(empty=true)` — carrito: vacío

## Violaciones de restricciones

- Ninguna.

## Estado final de la tienda

- Pedido 1: total 132,00 €
  - pedido 1: 12 × `B08P34RJSX` a 11,00 €
- Inventario `B08P34RJSX`: 41 → 8
- Líneas de carrito pendientes: 0

## Latencia por turno (segundos)

| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total | Audio de respuesta |
|---|---|---|---|---|---|---|---|
| 1 | 0.41 | 0.07 | 9.27 | 0.03 | 10.20 | 19.99 | 17.3 s |
| 2 | 0.35 | 0.00 | 7.87 | 0.04 | 6.71 | 14.98 | 12.3 s |
| 3 | 0.35 | 0.00 | 3.39 | 0.04 | 12.96 | 16.74 | 22.7 s |
| 4 | 0.40 | 0.00 | 12.40 | 0.05 | 20.09 | 32.94 | 33.8 s |
| 5 | 0.36 | 0.00 | 3.34 | 0.04 | 11.87 | 15.61 | 20.0 s |
| 6 | 0.36 | 0.00 | 0.00 | 0.03 | 8.26 | 8.64 | 14.7 s |
| **Media de los turnos con LLM (5)** | 0.38 | 0.01 | 7.26 | 0.04 | 12.37 | 20.05 | |
| **Media de los turnos sin LLM (1)** | 0.36 | 0.00 | 0.00 | 0.03 | 8.26 | 8.64 | |

