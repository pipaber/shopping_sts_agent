# 12_memoria_preferencias — Memoria de preferencias entre conversaciones

- Veredicto: **correcto**
- Entrada: texto
- Tipo: `memoria_preferencias`
- Qué se prueba: El usuario deja dicha una preferencia en una conversación y pregunta por ella en otra nueva (otro hilo, mismo usuario). La preferencia debe estar en el estado de la segunda conversación y en la respuesta.

## Turno 1 (3.3 s)

**Usuario (texto):** Recuerda para otras veces que prefiero el color azul.

- `guardar_preferencia(preferencia="color azul")` → OK: preferencia guardada.

**Agente:** He guardado que te gusta el color azul. ¿En qué puedo ayudarte ahora?

**Enviado al TTS:** He guardado que te gusta el color azul. ¿En qué puedo ayudarte ahora?

- ✔ `preference(contains="azul")` — preferencias: ['color azul']

> **Conversación nueva** del mismo usuario (hilo `eval-3e6f9559-12_memoria_preferencias-c2`).

## Turno 2 (3.2 s)

**Usuario (texto):** Hola, ¿recuerdas qué color prefiero?

- `guardar_preferencia(preferencia="color azul")` → OK: preferencia guardada.

**Agente:** Sí, he guardado tu preferencia de color azul.

**Enviado al TTS:** Sí, he guardado tu preferencia de color azul.

- ✔ `preference(contains="azul")` — preferencias: ['color azul']
- ✔ `response_contains(text="azul")` — la respuesta contiene «azul»

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
| 1 | 0.00 | 0.00 | 3.31 | 0.03 | 0.00 | 3.34 | 0.0 s |
| 2 | 0.00 | 0.00 | 3.14 | 0.03 | 0.00 | 3.17 | 0.0 s |
| **Media de los turnos con LLM (2)** | 0.00 | 0.00 | 3.23 | 0.03 | 0.00 | 3.26 | |

