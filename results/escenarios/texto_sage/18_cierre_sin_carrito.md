# 18_cierre_sin_carrito — Cerrar y confirmar sin nada en el carrito

- Veredicto: **correcto**
- Entrada: texto
- Tipo: `cierre_sin_carrito`
- Qué se prueba: El usuario pide cerrar el pedido con el carrito vacío y después dice que sí. No hay cotización que confirmar: no debe registrarse nada.

## Turno 1 (2.9 s)

**Usuario (texto):** Quiero cerrar el pedido.

- `cotizar()` → RECHAZADO: [carrito_vacio] El carrito está vacío; no hay nada que cotizar.

**Agente:** Tu carrito está vacío. ¿Quieres añadir algo antes de cerrar el pedido?

**Enviado al TTS:** Tu carrito está vacío. ¿Quieres añadir algo antes de cerrar el pedido?

- ✔ `orders(count=0)` — pedidos registrados: 0
- ✔ `awaiting_confirmation(value=false)` — esperando confirmación: no

## Turno 2 (2.2 s)

**Usuario (texto):** Sí, confirmo.

**Agente:** Tu carrito está vacío. ¿Quieres añadir algo antes de cerrar el pedido?

**Enviado al TTS:** Tu carrito está vacío. ¿Quieres añadir algo antes de cerrar el pedido?

- ✔ `orders(count=0)` — pedidos registrados: 0

## Comprobaciones finales

- ✔ `orders(count=0)` — pedidos registrados: 0
- ✔ `cart(empty=true)` — carrito: vacío

## Violaciones de restricciones

- Ninguna.

## Estado final de la tienda

- Líneas de carrito pendientes: 0

## Latencia por turno (segundos)

| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total | Audio de respuesta |
|---|---|---|---|---|---|---|---|
| 1 | 0.00 | 0.00 | 2.90 | 0.03 | 0.00 | 2.92 | 0.0 s |
| 2 | 0.00 | 0.00 | 2.13 | 0.03 | 0.00 | 2.16 | 0.0 s |
| **Media de los turnos con LLM (2)** | 0.00 | 0.00 | 2.51 | 0.03 | 0.00 | 2.54 | |

