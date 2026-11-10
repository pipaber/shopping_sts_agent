# Recuperación: evaluación final en test

- Fecha: 2026-11-10T15:04:54; commit `7c385b8`. Evaluación única: nada se ajustó después de ver estos números.
- 300 consultas de test, que no se habían usado antes. Rerankers entrenados con 1200 consultas de ajuste de train y 5 semillas, las mismas que en validación.
- nDCG@10 sobre los candidatos anotados (E=1, S=0,1, C=0,01, I=0) y recall@50 de productos exactos sobre todo el catálogo.
- Entre corchetes, intervalo del 95 % por bootstrap de consultas; en los rerankers, sobre la media entre semillas de cada consulta. Las diferencias son consulta a consulta.
- Los rerankers reordenan los 50 primeros del híbrido: su recall@50 es el del híbrido.

| Sistema | nDCG@10 en test | Desv. entre semillas | recall@50 | Dif. con el híbrido | Dif. con el control | nDCG@10 en validación |
|---|---|---|---|---|---|---|
| BM25 (base léxica) | 0,6797 [0,6515; 0,7066] |  | 0,6455 [0,6077; 0,6815] | −0,0316 [−0,0441; −0,0191] |  | 0,6750 |
| Denso (e5-small) | 0,7278 [0,7016; 0,7524] |  | 0,6501 [0,6131; 0,6854] | +0,0165 [+0,0042; +0,0291] |  | 0,7535 |
| Híbrido RRF | 0,7113 [0,6844; 0,7368] |  | 0,7194 [0,6854; 0,7526] | +0,0000 [+0,0000; +0,0000] |  | 0,7403 |
| Híbrido + control sin grafo | 0,7292 [0,7031; 0,7536] | ± 0,0006 | 0,7194 [0,6854; 0,7526] | +0,0179 [+0,0086; +0,0275] | +0,0000 [+0,0000; +0,0000] | 0,7582 |
| Híbrido + GraphSAGE | 0,7363 [0,7104; 0,7605] | ± 0,0025 | 0,7194 [0,6854; 0,7526] | +0,0249 [+0,0152; +0,0351] | +0,0071 [+0,0028; +0,0117] | 0,7619 |
