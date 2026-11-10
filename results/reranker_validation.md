# Reranker: comparación en validación

1200 consultas de ajuste y 300 de validación (partición de train, semilla 42); 5 semillas de entrenamiento por variante. Las consultas de test no se han usado.

- **nDCG@10 anotados**: la métrica del enunciado (solo los candidatos anotados de cada consulta).
- **nDCG@10 catálogo**: los 10 primeros sobre todo el catálogo, contando lo no anotado como irrelevante. Los rerankers reordenan los 50 primeros del híbrido, como en el agente.
- Media ± desviación típica entre semillas. Las diferencias se calculan consulta a consulta, con intervalo del 95 % por bootstrap de consultas.

| Sistema | nDCG@10 anotados | nDCG@10 catálogo |
|---|---|---|
| BM25 (base léxica) | 0,6750 | 0,4399 |
| Denso (e5-small) | 0,7535 | 0,5114 |
| Híbrido RRF | 0,7403 | 0,5236 |

| Reranker | Aristas | nDCG@10 anotados | nDCG@10 catálogo | Anotados: dif. con el denso | Anotados: dif. con el control |
|---|---|---|---|---|---|
| `control` | ninguna | 0,7582 ± 0,0005 | 0,5500 ± 0,0012 | +0,0046 [−0,0019; +0,0113] | +0,0000 [+0,0000; +0,0000] |
| `sage_candidate` | candidate | 0,7585 ± 0,0003 | 0,5505 ± 0,0006 | +0,0050 [−0,0016; +0,0117] | +0,0003 [−0,0004; +0,0010] |
| `sage_similar` | similar | 0,7615 ± 0,0017 | 0,5494 ± 0,0019 | +0,0080 [+0,0016; +0,0146] | +0,0034 [+0,0003; +0,0064] |
| `sage_brand` | brand | 0,7609 ± 0,0013 | 0,5477 ± 0,0054 | +0,0074 [+0,0003; +0,0146] | +0,0028 [−0,0008; +0,0065] |
| `sage_exact_only` | exact | 0,7596 ± 0,0010 | 0,5420 ± 0,0018 | +0,0060 [−0,0005; +0,0128] | +0,0014 [−0,0003; +0,0031] |
| `sage` | candidate, similar, brand | 0,7617 ± 0,0006 | 0,5463 ± 0,0031 | +0,0082 [+0,0013; +0,0153] | +0,0035 [−0,0001; +0,0073] |
| `sage_exact` | candidate, similar, brand, exact | 0,7628 ± 0,0017 | 0,5470 ± 0,0036 | +0,0093 [+0,0026; +0,0161] | +0,0046 [+0,0020; +0,0074] |
| `gatv2` | candidate, similar, brand | 0,7616 ± 0,0022 | 0,5505 ± 0,0015 | +0,0081 [+0,0014; +0,0150] | +0,0034 [+0,0013; +0,0058] |
| `gatv2_exact` | candidate, similar, brand, exact | 0,7630 ± 0,0006 | 0,5462 ± 0,0016 | +0,0094 [+0,0024; +0,0166] | +0,0048 [+0,0012; +0,0085] |

Frente al híbrido, que es lo que usa el agente sin reranker:

| Reranker | Anotados: dif. con el híbrido | Catálogo: dif. con el híbrido | Catálogo: dif. con el control |
|---|---|---|---|
| `control` | +0,0178 [+0,0097; +0,0265] | +0,0264 [+0,0113; +0,0417] | +0,0000 [+0,0000; +0,0000] |
| `sage_candidate` | +0,0182 [+0,0101; +0,0268] | +0,0269 [+0,0118; +0,0422] | +0,0005 [−0,0003; +0,0014] |
| `sage_similar` | +0,0212 [+0,0125; +0,0305] | +0,0259 [+0,0101; +0,0419] | −0,0005 [−0,0045; +0,0035] |
| `sage_brand` | +0,0206 [+0,0116; +0,0299] | +0,0241 [+0,0080; +0,0404] | −0,0023 [−0,0074; +0,0028] |
| `sage_exact_only` | +0,0192 [+0,0109; +0,0281] | +0,0184 [+0,0033; +0,0341] | −0,0079 [−0,0119; −0,0042] |
| `sage` | +0,0214 [+0,0125; +0,0306] | +0,0227 [+0,0065; +0,0391] | −0,0036 [−0,0093; +0,0019] |
| `sage_exact` | +0,0224 [+0,0137; +0,0317] | +0,0234 [+0,0082; +0,0391] | −0,0030 [−0,0071; +0,0012] |
| `gatv2` | +0,0213 [+0,0129; +0,0302] | +0,0269 [+0,0117; +0,0425] | +0,0006 [−0,0024; +0,0035] |
| `gatv2_exact` | +0,0226 [+0,0136; +0,0321] | +0,0226 [+0,0068; +0,0388] | −0,0038 [−0,0099; +0,0022] |
