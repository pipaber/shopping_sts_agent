# Por qué falla el escenario 05 con la voz del usuario

Comprobación aparte del 11 de noviembre de 2026, con el agente sin cambios (commit `702e04e`, reranker de control). No forma parte de las corridas de evaluación ni del resumen.

En la corrida `voz` con las grabaciones del usuario, el escenario `05_correccion_transcripcion` falla ([ficha](../escenarios/voz/05_correccion_transcripcion.md)). El ASR cambió dos cosas respecto al guion: en el turno 1 escribió «Busca» por «Busco», y en el turno 4 escribió los números con cifras («he dicho 12, no 2» por «he dicho doce, no dos»). Para saber cuál de las dos hace fallar el escenario, se corrió por texto una copia del escenario con un solo cambio cada vez. Las copias no se guardan en `scenarios/`: son el escenario 05 con la frase indicada.

| Corrida | Único cambio respecto al escenario 05 | Resultado | Turno 4 |
|---|---|---|---|
| [solo_cifras](solo_cifras/05_correccion_transcripcion.md) | Turno 4: «No, espera, he dicho 12, no 2.» | fallo | `fijar_presupuesto(importe_eur=12)` |
| [solo_busca](solo_busca/05_correccion_transcripcion.md) | Turno 1: «Busca un ratón inalámbrico.» | correcto | `cambiar_cantidad(cantidad=12)` |

La causa son las cifras: con «12, no 2» el LLM fija un presupuesto de 12 € en lugar de cambiar la cantidad a doce. Son dos corridas de un escenario, con un LLM determinista; no dicen con qué frecuencia Whisper escribe los números con cifras ni qué haría el LLM con otras frases.

Para repetirlo: copiar `scenarios/evaluacion/05_correccion_transcripcion.json` a una carpeta aparte, cambiar la frase y correr

```bash
uv run python -m shopping_agent.eval.scenarios --mode text --scenarios <carpeta> --name solo_cifras --out results/diagnostico_voz_05
```

Elaborado con asistencia de IA generativa.
