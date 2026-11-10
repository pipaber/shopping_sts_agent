# 05_correccion_transcripcion — Corrección de una transcripción antes de comprar

- Veredicto: **correcto**
- Entrada: audio (sintéticos, hablante de prueba «Luis Moray» de XTTS-v2 (no es la voz del usuario))
- Tipo: `correccion_transcripcion`
- Qué se prueba: El agente repite el pedido con dos unidades y el usuario corrige antes de confirmar: había dicho doce (dos y doce se confunden con facilidad al transcribir). No debe registrarse nada con dos unidades; el pedido final lleva doce.

## Turno 1 (18.3 s)

**Usuario (transcripción del ASR):** Busco un ratón inalámbrico.

- `buscar_productos(consulta="ratón inalámbrico")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B08P34RJSX | Raton inalámbrico, Inphic 2.4G Raton inalámbrico Recargable con Receptor USB, 3 Niveles Ajustables De dpi para Computadora PortáTil, Pc, Mac, Computadora, Macbook, Plata | marca: INPHIC | color: plata | precio: 33,29 € |…

**Agente:** Tengo el ratón inalámbrico INPHIC de plata por 33,29 €, el de INPHIC de plata clara por 42,45 €, el de Anmck negro por 23,61 €, el de WisFox gris por 19,69 € y el OMEN VECTOR de HP por 10,84 €. ¿Te interesa alguno?

**Enviado al TTS:** Tengo el ratón inalámbrico INPHIC de plata por treinta y tres euros con veintinueve céntimos, el de INPHIC de plata clara por cuarenta y dos euros con cuarenta y cinco céntimos, el de Anmck negro por veintitrés euros con sesenta y un céntimos, el de WisFox gris por diecinueve euros con sesenta y nueve céntimos y el OMEN VECTOR de HP por diez euros con ochenta y cuatro céntimos. ¿Te interesa alguno?

- ✔ `cart(empty=true)` — carrito: vacío

> `@elegido` = `B08P34RJSX` (candidate:1): Raton inalámbrico, Inphic 2.4G Raton inalámbrico Recargable con Receptor USB, 3 Niveles Ajustables De dpi para Computadora PortáTil, Pc, Mac, Computadora, Macbook, Plata

> **Suceso externo:** la tienda deja `B08P34RJSX` (@elegido) con precio 11,00 € y existencias 20.

## Turno 2 (7.9 s)

**Usuario (transcripción del ASR):** Añade dos del primero.

- `agregar_al_carrito(product_id="B08P34RJSX", cantidad=2)` → OK: hecho. Así queda el carrito. CARRITO: - id=B08P34RJSX | Raton inalámbrico, Inphic 2.4G Raton inalámbrico Recargable con… | 2 unidades × 11,00 € = 22,00 € | existencias: 20 Total del carrito: 22,00 €

**Agente:** Hecho, añadidas dos unidades. En el carrito hay 2 unidades de «Raton inalámbrico, Inphic 2.4G Raton inalámbrico Recargable con…» a 11,00 € cada una, 22,00 €. Total: 22,00 €.

**Enviado al TTS:** Hecho, añadidas dos unidades. En el carrito hay dos unidades de Raton inalámbrico a once euros cada una, veintidós euros. Total: veintidós euros.

- ✔ `cart(lines=[{"product": "@elegido", "quantity": 2}])` — carrito: 2 × B08P34RJSX

## Turno 3 (8.0 s)

**Usuario (transcripción del ASR):** Cierra el pedido.

- `cotizar()` → OK: cotización creada; falta la confirmación del usuario.

**Agente:** Te repito el pedido antes de registrarlo: 2 unidades de «Raton inalámbrico, Inphic 2.4G Raton inalámbrico Recargable con…» a 11,00 € cada una, 22,00 €. Total: 22,00 €. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar. *(esperando confirmación)*

**Enviado al TTS:** Te repito el pedido antes de registrarlo: dos unidades de Raton inalámbrico a once euros cada una, veintidós euros. Total: veintidós euros. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar.

- ✔ `awaiting_confirmation(value=true)` — esperando confirmación: sí
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 4 (15.6 s)

**Usuario (transcripción del ASR):** No, espera, he dicho doce, no dos.

- `cambiar_cantidad(product_id="B08P34RJSX", cantidad=12)` → OK: hecho. Así queda el carrito. CARRITO: - id=B08P34RJSX | Raton inalámbrico, Inphic 2.4G Raton inalámbrico Recargable con… | 12 unidades × 11,00 € = 132,00 € | existencias: 20 Total del carrito: 132,00 €

**Agente:** Hecho, añadidas 10 unidades más. En total, 12 unidades de «Raton inalámbrico, Inphic 2.4G Raton inalámbrico Recargable con…» a 11,00 € cada una, 132,00 €. Total: 132,00 €. En el carrito hay 12 unidades de «Raton inalámbrico, Inphic 2.4G Raton inalámbrico Recargable con…» a 11,00 € cada una, 132,00 €. Total: 132,00 €.

**Enviado al TTS:** Hecho, añadidas diez unidades más. En total, doce unidades de Raton inalámbrico a once euros cada una, ciento treinta y dos euros. Total: ciento treinta y dos euros. En el carrito hay doce unidades de Raton inalámbrico a once euros cada una, ciento treinta y dos euros. Total: ciento treinta y dos euros.

- ✔ `orders(count=0)` — pedidos registrados: 0
- ✔ `cart(lines=[{"product": "@elegido", "quantity": 12}])` — carrito: 12 × B08P34RJSX

## Turno 5 (8.6 s)

**Usuario (transcripción del ASR):** Ahora sí, cierra el pedido.

- `cotizar()` → OK: cotización creada; falta la confirmación del usuario.

**Agente:** Te repito el pedido antes de registrarlo: 12 unidades de «Raton inalámbrico, Inphic 2.4G Raton inalámbrico Recargable con…» a 11,00 € cada una, 132,00 €. Total: 132,00 €. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar. *(esperando confirmación)*

**Enviado al TTS:** Te repito el pedido antes de registrarlo: doce unidades de Raton inalámbrico a once euros cada una, ciento treinta y dos euros. Total: ciento treinta y dos euros. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar.

- ✔ `awaiting_confirmation(value=true)` — esperando confirmación: sí
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 6 (4.2 s)

**Usuario (transcripción del ASR):** Sí, confirmo.

- `confirmar_pedido(quote_id="b9a1d97f000145b39c6c8473164c6430")` → OK: pedido registrado

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
| 1 | 0.34 | 0.03 | 7.76 | 0.03 | 10.10 | 18.27 | 43.0 s |
| 2 | 0.33 | 0.00 | 4.77 | 0.05 | 2.72 | 7.87 | 11.5 s |
| 3 | 0.33 | 0.00 | 2.27 | 0.04 | 5.36 | 8.01 | 22.9 s |
| 4 | 0.35 | 0.00 | 7.86 | 0.05 | 7.36 | 15.63 | 30.7 s |
| 5 | 0.34 | 0.00 | 2.35 | 0.04 | 5.89 | 8.62 | 24.8 s |
| 6 | 0.33 | 0.00 | 0.00 | 0.04 | 3.81 | 4.18 | 15.6 s |
| **Media de los turnos con LLM (5)** | 0.34 | 0.01 | 5.00 | 0.04 | 6.29 | 11.68 | |
| **Media de los turnos sin LLM (1)** | 0.33 | 0.00 | 0.00 | 0.04 | 3.81 | 4.18 | |

