# 05_correccion_transcripcion — Corrección de una transcripción antes de comprar

- Veredicto: **correcto**
- Entrada: texto
- Tipo: `correccion_transcripcion`
- Qué se prueba: El agente repite el pedido con dos unidades y el usuario corrige antes de confirmar: había dicho doce (dos y doce se confunden con facilidad al transcribir). No debe registrarse nada con dos unidades; el pedido final lleva doce.

## Turno 1 (6.5 s)

**Usuario (texto):** Busco un ratón inalámbrico.

- `buscar_productos(consulta="ratón inalámbrico")` → OK: estos son ahora los CANDIDATOS, del más al menos relevante: [1] id=B0757LNVBT | Ratón Inalámbrico Recargable, Silencioso Infame Ratón óptico Silencioso Click Mini, Ultra Delgado 1600 dpi para Computadora Portátil, PC, Portátil, Computadora, Macbook (Plata Clara) | marca: INPHIC | color: Plata clara …

**Agente:** Tengo el ratón inalámbrico INPHIC por 42,45 euros, el WisFox por 19,69, el INPHIC por 33,29 y el Anmck por 23,61. ¿Te interesa alguno?

**Enviado al TTS:** Tengo el ratón inalámbrico INPHIC por cuarenta y dos euros con cuarenta y cinco céntimos, el WisFox por diecinueve coma sesenta y nueve, el INPHIC por treinta y tres coma veintinueve y el Anmck por veintitrés coma sesenta y uno. ¿Te interesa alguno?

- ✔ `cart(empty=true)` — carrito: vacío

> `@elegido` = `B0757LNVBT` (candidate:1): Ratón Inalámbrico Recargable, Silencioso Infame Ratón óptico Silencioso Click Mini, Ultra Delgado 1600 dpi para Computadora Portátil, PC, Portátil, Computadora, Macbook (Plata Clara)

> **Suceso externo:** la tienda deja `B0757LNVBT` (@elegido) con precio 11,00 € y existencias 20.

## Turno 2 (5.1 s)

**Usuario (texto):** Añade dos del primero.

- `agregar_al_carrito(product_id="B0757LNVBT", cantidad=2)` → OK: hecho. Así queda el carrito. CARRITO: - id=B0757LNVBT | Ratón Inalámbrico Recargable, Silencioso Infame Ratón óptico… | 2 unidades × 11,00 € = 22,00 € | existencias: 20 Total del carrito: 22,00 €

**Agente:** Hecho, añadidas dos unidades. El total es 22,00 €. En el carrito hay 2 unidades de «Ratón Inalámbrico Recargable, Silencioso Infame Ratón óptico…» a 11,00 € cada una, 22,00 €. Total: 22,00 €.

**Enviado al TTS:** Hecho, añadidas dos unidades. El total es veintidós euros. En el carrito hay dos unidades de Ratón Inalámbrico Recargable a once euros cada una, veintidós euros. Total: veintidós euros.

- ✔ `cart(lines=[{"product": "@elegido", "quantity": 2}])` — carrito: 2 × B0757LNVBT

## Turno 3 (2.2 s)

**Usuario (texto):** Cierra el pedido.

- `cotizar()` → OK: cotización creada; falta la confirmación del usuario.

**Agente:** Te repito el pedido antes de registrarlo: 2 unidades de «Ratón Inalámbrico Recargable, Silencioso Infame Ratón óptico…» a 11,00 € cada una, 22,00 €. Total: 22,00 €. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar. *(esperando confirmación)*

**Enviado al TTS:** Te repito el pedido antes de registrarlo: dos unidades de Ratón Inalámbrico Recargable a once euros cada una, veintidós euros. Total: veintidós euros. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar.

- ✔ `awaiting_confirmation(value=true)` — esperando confirmación: sí
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 4 (5.3 s)

**Usuario (texto):** No, espera, he dicho doce, no dos.

- `cambiar_cantidad(product_id="B0757LNVBT", cantidad=12)` → OK: hecho. Así queda el carrito. CARRITO: - id=B0757LNVBT | Ratón Inalámbrico Recargable, Silencioso Infame Ratón óptico… | 12 unidades × 11,00 € = 132,00 € | existencias: 20 Total del carrito: 132,00 €

**Agente:** Hecho, añadidas 10 unidades más. El total es 132,00 €. En el carrito hay 12 unidades de «Ratón Inalámbrico Recargable, Silencioso Infame Ratón óptico…» a 11,00 € cada una, 132,00 €. Total: 132,00 €.

**Enviado al TTS:** Hecho, añadidas diez unidades más. El total es ciento treinta y dos euros. En el carrito hay doce unidades de Ratón Inalámbrico Recargable a once euros cada una, ciento treinta y dos euros. Total: ciento treinta y dos euros.

- ✔ `orders(count=0)` — pedidos registrados: 0
- ✔ `cart(lines=[{"product": "@elegido", "quantity": 12}])` — carrito: 12 × B0757LNVBT

## Turno 5 (2.3 s)

**Usuario (texto):** Ahora sí, cierra el pedido.

- `cotizar()` → OK: cotización creada; falta la confirmación del usuario.

**Agente:** Te repito el pedido antes de registrarlo: 12 unidades de «Ratón Inalámbrico Recargable, Silencioso Infame Ratón óptico…» a 11,00 € cada una, 132,00 €. Total: 132,00 €. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar. *(esperando confirmación)*

**Enviado al TTS:** Te repito el pedido antes de registrarlo: doce unidades de Ratón Inalámbrico Recargable a once euros cada una, ciento treinta y dos euros. Total: ciento treinta y dos euros. ¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar.

- ✔ `awaiting_confirmation(value=true)` — esperando confirmación: sí
- ✔ `orders(count=0)` — pedidos registrados: 0

## Turno 6 (0.0 s)

**Usuario (texto):** Sí, confirmo.

- `confirmar_pedido(quote_id="2fd6096d254b4895ba5ce3fadd5a0772")` → OK: pedido registrado

**Agente:** Pedido número 1 registrado: 12 unidades de «Ratón Inalámbrico Recargable, Silencioso Infame Ratón óptico…» a 11,00 € cada una, 132,00 €. Total: 132,00 €. Gracias por tu compra.

**Enviado al TTS:** Pedido número uno registrado: doce unidades de Ratón Inalámbrico Recargable a once euros cada una, ciento treinta y dos euros. Total: ciento treinta y dos euros. Gracias por tu compra.

- ✔ `orders(count=1)` — pedidos registrados: 1

## Comprobaciones finales

- ✔ `orders(count=1)` — pedidos registrados: 1
- ✔ `order(lines=[{"product": "@elegido", "quantity": 12}], total_cents=13200)` — pedido 1: 12 × B0757LNVBT; total 13200 céntimos
- ✔ `stock(product="@elegido", equals=8)` — existencias de B0757LNVBT: 8
- ✔ `cart(empty=true)` — carrito: vacío

## Violaciones de restricciones

- Ninguna.

## Estado final de la tienda

- Pedido 1: total 132,00 €
  - pedido 1: 12 × `B0757LNVBT` a 11,00 €
- Inventario `B0757LNVBT`: 3 → 8
- Líneas de carrito pendientes: 0

## Latencia por turno (segundos)

| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total | Audio de respuesta |
|---|---|---|---|---|---|---|---|
| 1 | 0.00 | 0.03 | 6.48 | 0.03 | 0.00 | 6.54 | 0.0 s |
| 2 | 0.00 | 0.00 | 5.06 | 0.05 | 0.00 | 5.11 | 0.0 s |
| 3 | 0.00 | 0.00 | 2.17 | 0.04 | 0.00 | 2.21 | 0.0 s |
| 4 | 0.00 | 0.00 | 5.30 | 0.04 | 0.00 | 5.34 | 0.0 s |
| 5 | 0.00 | 0.00 | 2.22 | 0.05 | 0.00 | 2.27 | 0.0 s |
| 6 | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 | 0.03 | 0.0 s |
| **Media de los turnos con LLM (5)** | 0.00 | 0.01 | 4.25 | 0.04 | 0.00 | 4.29 | |
| **Media de los turnos sin LLM (1)** | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 | 0.03 | |

