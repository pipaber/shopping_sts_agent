# 12_memoria_preferencias — Memoria de preferencias entre conversaciones

- Veredicto: **correcto**
- Entrada: texto
- Tipo: `memoria_preferencias`
- Qué se prueba: El usuario deja dicha una preferencia en una conversación y pregunta por ella en otra nueva (otro hilo, mismo usuario). La preferencia debe estar en el estado de la segunda conversación y en la respuesta.

## Turno 1 (5.2 s)

**Usuario (texto):** Recuerda para otras veces que prefiero el color azul.

- `guardar_preferencia(preferencia="color azul")` → OK: preferencia guardada.

**Agente:** He guardado que te gusta el color azul. ¿En qué puedo ayudarte ahora?

**Enviado al TTS:** He guardado que te gusta el color azul. ¿En qué puedo ayudarte ahora?

- ✔ `preference(contains="azul")` — preferencias: ['color azul']

> **Conversación nueva** del mismo usuario (hilo `eval-2258b5f4-12_memoria_preferencias-c2`).

## Turno 2 (4.7 s)

**Usuario (texto):** Hola, ¿recuerdas qué color prefiero?

- `guardar_preferencia(preferencia="color azul")` → OK: preferencia guardada.

**Agente:** Sí, he guardado que tu color preferido es azul.

**Enviado al TTS:** Sí, he guardado que tu color preferido es azul.

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
| 1 | 0.00 | 0.00 | 5.17 | 0.03 | 0.00 | 5.20 | 0.0 s |
| 2 | 0.00 | 0.00 | 4.64 | 0.03 | 0.00 | 4.67 | 0.0 s |
| **Media de los turnos con LLM (2)** | 0.00 | 0.00 | 4.90 | 0.03 | 0.00 | 4.93 | |

