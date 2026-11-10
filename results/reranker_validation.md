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
| `sage_candidate` | candidate | 0,7586 ± 0,0006 | 0,5502 ± 0,0007 | +0,0050 [−0,0015; +0,0117] | +0,0004 [−0,0003; +0,0011] |
| `sage_similar` | similar | 0,7619 ± 0,0015 | 0,5488 ± 0,0024 | +0,0084 [+0,0020; +0,0151] | +0,0037 [+0,0007; +0,0068] |
| `sage_brand` | brand | 0,7612 ± 0,0017 | 0,5470 ± 0,0052 | +0,0076 [+0,0004; +0,0149] | +0,0030 [−0,0007; +0,0068] |
| `sage_exact_only` | exact | 0,7595 ± 0,0011 | 0,5423 ± 0,0022 | +0,0060 [−0,0005; +0,0127] | +0,0013 [−0,0004; +0,0031] |
| `sage` | candidate, similar, brand | 0,7619 ± 0,0009 | 0,5474 ± 0,0027 | +0,0084 [+0,0017; +0,0153] | +0,0038 [+0,0004; +0,0073] |
| `sage_exact` | candidate, similar, brand, exact | 0,7631 ± 0,0015 | 0,5470 ± 0,0035 | +0,0095 [+0,0029; +0,0164] | +0,0049 [+0,0022; +0,0078] |
| `gatv2` | candidate, similar, brand | 0,7616 ± 0,0028 | 0,5491 ± 0,0026 | +0,0081 [+0,0015; +0,0148] | +0,0035 [+0,0012; +0,0058] |
| `gatv2_exact` | candidate, similar, brand, exact | 0,7632 ± 0,0009 | 0,5461 ± 0,0015 | +0,0097 [+0,0027; +0,0169] | +0,0051 [+0,0014; +0,0088] |

Frente al híbrido, que es lo que usa el agente sin reranker:

| Reranker | Anotados: dif. con el híbrido | Catálogo: dif. con el híbrido | Catálogo: dif. con el control |
|---|---|---|---|
| `control` | +0,0178 [+0,0097; +0,0265] | +0,0264 [+0,0113; +0,0417] | +0,0000 [+0,0000; +0,0000] |
| `sage_candidate` | +0,0182 [+0,0101; +0,0269] | +0,0266 [+0,0115; +0,0419] | +0,0002 [−0,0007; +0,0012] |
| `sage_similar` | +0,0216 [+0,0129; +0,0308] | +0,0252 [+0,0095; +0,0412] | −0,0011 [−0,0052; +0,0029] |
| `sage_brand` | +0,0208 [+0,0118; +0,0303] | +0,0234 [+0,0073; +0,0399] | −0,0029 [−0,0081; +0,0022] |
| `sage_exact_only` | +0,0192 [+0,0109; +0,0280] | +0,0187 [+0,0035; +0,0343] | −0,0077 [−0,0117; −0,0039] |
| `sage` | +0,0216 [+0,0127; +0,0310] | +0,0238 [+0,0077; +0,0400] | −0,0025 [−0,0080; +0,0027] |
| `sage_exact` | +0,0227 [+0,0139; +0,0319] | +0,0234 [+0,0082; +0,0391] | −0,0030 [−0,0072; +0,0012] |
| `gatv2` | +0,0213 [+0,0129; +0,0301] | +0,0255 [+0,0103; +0,0412] | −0,0008 [−0,0040; +0,0022] |
| `gatv2_exact` | +0,0229 [+0,0139; +0,0324] | +0,0225 [+0,0066; +0,0387] | −0,0039 [−0,0102; +0,0023] |
