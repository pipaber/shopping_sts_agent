# Corrida final en Google Colab (T4)

Archivos de la corrida final del notebook [notebooks/colab.ipynb](../../notebooks/colab.ipynb), descargados de la sesión de Colab con su celda «Descargar los resultados».

- **Cuándo y con qué:** 12 de noviembre de 2026, commit `d81bc00`, GPU Tesla T4 (15 360 MiB), 2 CPU, Ubuntu 24.04, CUDA 13.0. Las fechas de los archivos están en UTC.
- **Voz:** la del autor, clonada de su grabación de referencia a velocidad 1,10, con sus 31 grabaciones como entrada. Los audios no se guardan aquí ni en ninguna parte del repositorio.
- **Memoria del agente:** Postgres, instalado en la propia sesión.

## Qué hay

| Ruta | Qué es |
|---|---|
| `escenarios/texto/` | Los 20 escenarios por texto con el reranker por defecto: 20 de 20 |
| `escenarios/voz/` | Los seis escenarios por voz con las grabaciones del autor: 6 de 6, con `metricas_voz.json` |
| `escenarios/voz_texto_correcto/` | Los mismos seis con la transcripción correcta: 6 de 6 |
| `escenarios/resumen.md` y `.json` | El resumen que generó el notebook |
| `chat_compra.md` y `.json` | La conversación de compra por texto |
| `retrieval_train.json` | BM25, denso e híbrido con las consultas de train |
| `en_vivo/vivo-ceeaad0f/` | Dos turnos de la conversación en vivo, enviados con grabaciones del autor |

## Cómo leer el resumen

`escenarios/resumen.md` se generó dentro de Colab a partir de todo lo que había en `results/escenarios/` de la copia clonada. Solo tres corridas se ejecutaron allí: `texto`, `voz` y `voz_texto_correcto`. Las demás filas (`texto_sage`, `reserva`, `voz_sintetica`…) son las de la workstation, tal como estaban en el repositorio, y sus enlaces no funcionan desde esta carpeta. La tabla de «antes y después» compara con la línea base de la workstation.

## Lo que no está

- La salida de las celdas de instalación, pruebas y entrenamiento de los rerankers: sus cifras están en el README, apartado «Ejecución en Colab (T4)».
- Las corridas con GraphSAGE y sin reranker, y los escenarios de reserva: no se repitieron en Colab.
- La grabación con el micrófono del navegador, que no se probó en esta corrida.

Elaborado con asistencia de IA generativa (Claude Code).
