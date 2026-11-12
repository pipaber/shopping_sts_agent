# 05_correccion_transcripcion — Corrección de una transcripción antes de comprar

- Veredicto: **fallo**
- Entrada: audio (grabaciones del usuario)
- Tipo: `correccion_transcripcion`
- Qué se prueba: El agente repite el pedido con dos unidades y el usuario corrige antes de confirmar: había dicho doce (dos y doce se confunden con facilidad al transcribir). No debe registrarse nada con dos unidades; el pedido final lleva doce.

## Turno 1 (25.5 s)

**Usuario (transcripción del ASR):** Busca un ratón inalámbrico.

**Texto correcto:** Busco un ratón inalámbrico.

- `buscar_productos(consulta="ratón inalámbrico")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B08P34RJSX | Raton inalámbrico, Inphic 2.4G Raton inalámbrico Recargable con Receptor USB, 3 Niveles Ajustables De dpi para Computadora PortáTil, Pc, Mac, Computadora, Macbook, Plata | marca: INPHIC | color: plata | precio: 33,29 € |…

**Agente:** Tengo el ratón inalámbrico INPHIC en plata por 33,29 €, el de INPHIC en plata clara por 42,45 €, el de Anmck en negro por 23,61 €, el de WisFox en gris por 19,69 € y el OMEN VECTOR de HP por 10,84 €. ¿Te interesa alguno?

**Enviado al TTS:** Tengo el ratón inalámbrico INPHIC en plata por treinta y tres euros con veintinueve céntimos, el de INPHIC en plata clara por cuarenta y dos euros con cuarenta y cinco céntimos, el de Anmck en negro por veintitrés euros con sesenta y un céntimos, el de WisFox en gris por diecinueve euros con sesenta y nueve céntimos y el OMEN VECTOR de HP por diez euros con ochenta y cuatro céntimos. ¿Te interesa alguno?

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

## Turno 4 (12.4 s)

**Usuario (transcripción del ASR):** No, espera, he dicho 12, no 2.

**Texto correcto:** No, espera, he dicho doce, no dos.

- `fijar_presupuesto(importe_eur=12)` → OK: presupuesto fijado en 12,00 €. Aviso: el carrito suma 22,00 € y lo supera en 10,00 €.

**Agente:** El carrito suma 22,00 €, lo que supera tu presupuesto de 12,00 € en 10,00 €. ¿Qué quieres hacer? En el carrito hay 2 unidades de «Raton inalámbrico, Inphic 2.4G Raton inalámbrico Recargable con…» a 11,00 € cada una, 22,00 €. Total: 22,00 €. Tu presupuesto es de 12,00 € y lo superas en 10,00 €.

**Enviado al TTS:** El carrito suma veintidós euros, lo que supera tu presupuesto de doce euros en diez euros. ¿Qué quieres hacer? En el carrito hay dos unidades de Raton inalámbrico a once euros cada una, veintidós euros. Total: veintidós euros. Tu presupuesto es de doce euros y lo superas en diez euros.

- ✔ `orders(count=0)` — pedidos registrados: 0
- ✘ `cart(lines=[{"product": "@elegido", "quantity": 12}])` — carrito: 2 × B08P34RJSX

## Turno 5 (9.7 s)

**Usuario (transcripción del ASR):** Ahora sí, cierra el pedido.

- `cotizar()` → RECHAZADO: [presupuesto_excedido] El total sería 22,00 € y supera el presupuesto de 12,00 € por 10,00 €.

**Agente:** Ese ratón cuesta 11,00 € y el carrito supera tu presupuesto de 12,00 € en 10,00 €. ¿Quieres reducir el número de unidades o cambiar por otro?

**Enviado al TTS:** Ese ratón cuesta once euros y el carrito supera tu presupuesto de doce euros en diez euros. ¿Quieres reducir el número de unidades o cambiar por otro?

- ✘ `awaiting_confirmation(value=true)` — esperando confirmación: no
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 6 (9.8 s)

**Usuario (transcripción del ASR):** Sí, confirmo.

- `cotizar()` → RECHAZADO: [presupuesto_excedido] El total sería 22,00 € y supera el presupuesto de 12,00 € por 10,00 €.

**Agente:** Ese ratón cuesta 11,00 € y el carrito supera tu presupuesto de 12,00 € en 10,00 €. ¿Quieres reducir el número de unidades o cambiar por otro?

**Enviado al TTS:** Ese ratón cuesta once euros y el carrito supera tu presupuesto de doce euros en diez euros. ¿Quieres reducir el número de unidades o cambiar por otro?

- ✘ `orders(count=1)` — pedidos registrados: 0

## Comprobaciones finales

- ✘ `orders(count=1)` — pedidos registrados: 0
- ✘ `order(lines=[{"product": "@elegido", "quantity": 12}], total_cents=13200)` — no hay ningún pedido
- ✘ `stock(product="@elegido", equals=8)` — existencias de B08P34RJSX: 20
- ✘ `cart(empty=true)` — carrito: 2 × B08P34RJSX

## Violaciones de restricciones

- Ninguna.

## Estado final de la tienda

- Inventario `B08P34RJSX`: 41 → 20
- Líneas de carrito pendientes: 1

## Latencia por turno (segundos)

| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total | Audio de respuesta |
|---|---|---|---|---|---|---|---|
| 1 | 0.34 | 0.03 | 7.83 | 0.03 | 17.23 | 25.47 | 44.0 s |
| 2 | 0.33 | 0.00 | 4.75 | 0.05 | 2.73 | 7.86 | 11.5 s |
| 3 | 0.33 | 0.00 | 2.25 | 0.04 | 5.36 | 7.98 | 22.9 s |
| 4 | 0.35 | 0.00 | 5.84 | 0.03 | 6.18 | 12.41 | 26.0 s |
| 5 | 0.34 | 0.00 | 6.11 | 0.03 | 3.24 | 9.72 | 13.4 s |
| 6 | 0.33 | 0.00 | 6.24 | 0.03 | 3.22 | 9.82 | 13.4 s |
| **Media de los turnos con LLM (6)** | 0.34 | 0.01 | 5.50 | 0.04 | 6.33 | 12.21 | |

