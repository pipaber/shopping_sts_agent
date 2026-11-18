# Corrida en Google Colab (T4) con F5-Spanish

Archivos de la corrida del notebook [notebooks/colab.ipynb](../../notebooks/colab.ipynb) con la voz de F5-Spanish, descargados de la sesión de Colab con su celda «Descargar los resultados». La corrida anterior, con XTTS-v2, está en [results/colab_t4/](../colab_t4/LEEME.md).

- **Cuándo y con qué:** 17 de noviembre de 2026 por la noche (hora de Lima), commit `a8f7c00`, GPU Tesla T4 (15 360 MiB), 2 CPU. Las fechas de los archivos están en UTC y por eso dicen 18 de noviembre.
- **Voz:** la del autor, clonada con F5-Spanish de dos de sus turnos grabados (`01_compra_confirmada/01` y `03_cambio_cantidad/01`) a velocidad 0,9, con sus 31 grabaciones como entrada. Los audios no se guardan aquí ni en ninguna parte del repositorio.
- **Memoria del agente:** Postgres, instalado en la propia sesión.
- **Segunda corrida del día.** La primera, sobre el commit `60765e8`, dio los mismos veredictos y la misma calidad de voz con una síntesis algo más rápida (13,8 s por turno con LLM, frente a 16,1 s en esta); la sesión caducó antes de descargar sus archivos.

## Qué hay

| Ruta | Qué es |
|---|---|
| `escenarios/texto/` | Los 20 escenarios por texto con el reranker por defecto: 20 de 20 |
| `escenarios/voz/` | Los seis escenarios por voz con las grabaciones del autor: 6 de 6, con `metricas_voz.json` |
| `escenarios/voz_texto_correcto/` | Los mismos seis con la transcripción correcta: 6 de 6 |
| `escenarios/resumen.md` y `.json` | El resumen que generó el notebook |
| `chat_compra.md` y `.json` | La conversación de compra por texto |
| `retrieval_train.json` | BM25, denso e híbrido con las consultas de train |

## Cómo leer el resumen

`escenarios/resumen.md` se generó dentro de Colab a partir de todo lo que había en `results/escenarios/` de la copia clonada. Solo tres corridas se ejecutaron allí: `texto`, `voz` y `voz_texto_correcto`. Las demás filas (`texto_sage`, `reserva`, `voz_xtts`…) son las de la workstation, tal como estaban en el repositorio, y sus enlaces no funcionan desde esta carpeta.

## Lo que no está

- La salida de las celdas de instalación, pruebas y entrenamiento de los rerankers: lo que se comprobó está en el README, apartado «Ejecución en Colab (T4)».
- La conversación en vivo: se probó en la primera corrida del día, no en esta.
- La grabación con el micrófono del navegador, que no se probó.

Elaborado con asistencia de IA generativa (Claude Code).
