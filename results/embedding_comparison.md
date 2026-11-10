# Modelos de embedding: comparación con las consultas de train

1500 consultas de train, de las que 300 son las de validación del reranker (semilla 42). Nada se entrena y las consultas de test no se han usado.

- **nDCG@10**: la métrica del enunciado, sobre los candidatos anotados de cada consulta.
- **recall@50**: fracción de productos exactos entre los 50 primeros de todo el catálogo.
- **Diferencias**: frente a `intfloat/multilingual-e5-small`, el modelo en uso, consulta a consulta, con intervalo del 95 % por bootstrap de consultas.
- Mismo texto para todos: título, marca, color y viñetas, cortado a 256 tokens.
- Los candidatos se codificaron en media precisión, que mueve el nDCG en el cuarto decimal.

| Modelo | Sistema | nDCG@10 | Dif. en train | recall@50 | nDCG@10 validación | Dif. en validación |
|---|---|---|---|---|---|---|
| `intfloat/multilingual-e5-small` | Denso | 0,7372 |  | 0,6637 | 0,7535 |  |
| `intfloat/multilingual-e5-small` | Híbrido RRF | 0,7236 |  | 0,7230 | 0,7402 |  |
| `intfloat/multilingual-e5-base` | Denso | 0,7210 | −0,0162 [−0,0226; −0,0102] | 0,6482 | 0,7303 | −0,0233 [−0,0378; −0,0087] |
| `intfloat/multilingual-e5-base` | Híbrido RRF | 0,7138 | −0,0098 [−0,0145; −0,0051] | 0,7215 | 0,7201 | −0,0201 [−0,0327; −0,0087] |
| `BAAI/bge-m3` | Denso | 0,7358 | −0,0014 [−0,0077; +0,0045] | 0,6831 | 0,7384 | −0,0151 [−0,0298; −0,0016] |
| `BAAI/bge-m3` | Híbrido RRF | 0,7230 | −0,0006 [−0,0052; +0,0042] | 0,7349 | 0,7300 | −0,0102 [−0,0221; +0,0010] |

| Modelo | Dimensión | Catálogo (s) | Consulta (ms) | VRAM pico (MiB) | Precisión |
|---|---|---|---|---|---|
| `intfloat/multilingual-e5-small` | 384 | ya guardado | 0,83 | 463 | simple |
| `intfloat/multilingual-e5-base` | 768 | 114 | 0,75 | 1435 | media |
| `BAAI/bge-m3` | 1024 | 344 | 1,09 | 2662 | media |

Se reproduce con `python -m shopping_agent.eval.embeddings`.
