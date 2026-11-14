# Comparación de voces: resultados

| Variante | Semejanza (media) | Semejanza (mín.) | WER | Sílabas/s | Tono (Hz) | Variación del tono (st) | Síntesis (s) | Síntesis / audio | VRAM (MiB) |
|---|---|---|---|---|---|---|---|---|---|
| Voz real: grupo de medida (19 turnos, entre sí) | 0.361 | — | — | 4.66 | 106 | 4.68 | — | — | — |
| Voz real: 12 turnos del grupo de clonar | 0.378 | — | — | 4.84 | 105 | 5.50 | — | — | — |
| Voz real: grabación de referencia | 0.413 | — | — | 5.70 | 120 | 4.93 | — | — | — |
| Voz real: referencia anterior | 0.363 | — | — | 6.71 | 93 | 2.70 | — | — | — |
| `A_xtts_actual` | 0.245 | 0.231 | 9.6 % | 4.95 | 115 | 5.46 | 39.6 | 0.25 | 1958 |
| `B1_xtts_ritmo30` | 0.252 | 0.211 | 6.3 % | 5.47 | 119 | 5.48 | 34.8 | 0.23 | 1958 |
| `B2_xtts_varias` | 0.300 | 0.263 | 5.4 % | 5.47 | 119 | 5.22 | 35.2 | 0.23 | 1960 |
| `B3_xtts_varias_t075` | 0.291 | 0.260 | 1.8 % | 5.66 | 121 | 5.49 | 33.7 | 0.23 | 1960 |
| `B4_xtts_turnos` | 0.312 | 0.296 | 2.4 % | 6.06 | 114 | 5.15 | 31.7 | 0.23 | 1960 |
| `B5_xtts_todo` | 0.321 | 0.289 | 4.8 % | 5.78 | 107 | 5.27 | 35.8 | 0.23 | 1960 |
| `C2_f5_turnos` | 0.369 | 0.290 | 7.5 % | 6.18 | 108 | 3.28 | 57.3 | 0.40 | 1354 |
| `C_f5_spanish` | 0.312 | 0.295 | 9.9 % | 5.31 | 120 | 7.22 | 47.9 | 0.30 | 1308 |
| `D1_chatterbox_v3` | 0.271 | 0.245 | 3.6 % | 5.71 | 122 | 4.33 | 85.3 | 0.62 | 4546 |
| `D2_chatterbox_latam` | 0.278 | 0.245 | 5.4 % | 6.47 | 115 | 3.40 | 74.3 | 0.61 | 4700 |
| `D3_chatterbox_latam_turnos` | 0.328 | 0.270 | 2.7 % | 6.49 | 112 | 3.93 | 81.6 | 0.62 | 4920 |
| `E_xtts_conversion` | 0.287 | 0.260 | 13.3 % | 5.08 | 117 | 5.27 | 29.8 | 0.19 | 4012 |

## Qué es cada variante

- `A_xtts_actual`: XTTS-v2 como está: referencia nueva, ritmo de 6 s, velocidad 1,10.
- `B1_xtts_ritmo30`: XTTS-v2, referencia nueva, ritmo condicionado con 30 s, velocidad 1,0.
- `B2_xtts_varias`: XTTS-v2, timbre promediado de las dos referencias y 12 turnos reales; ritmo como B1 (30 s de la referencia nueva).
- `B3_xtts_varias_t075`: Como B2 con temperatura 0,75 (la de XTTS-v2 por defecto).
- `B4_xtts_turnos`: XTTS-v2 solo con los 12 turnos reales (sin las grabaciones de referencia), velocidad 1,0.
- `B5_xtts_todo`: XTTS-v2, timbre y ritmo de todas las grabaciones de clonar (113 s), velocidad 1,0.
- `C2_f5_turnos`: F5-Spanish clonando de dos turnos reales (11,5 s) en vez de la grabación de referencia.
- `C_f5_spanish`: F5-TTS con el ajuste al español (F5-Spanish), 11 s de la referencia nueva y su transcripción.
- `D1_chatterbox_v3`: Chatterbox multilingüe V3 (idioma «es»), referencia nueva.
- `D2_chatterbox_latam`: Chatterbox, ajuste al español de Latinoamérica, referencia nueva.
- `D3_chatterbox_latam_turnos`: Como D2 clonando de los 12 turnos reales seguidos (43 s) en vez de la grabación de referencia.
- `E_xtts_conversion`: Conversión de voz de Chatterbox sobre los audios de A_xtts_actual (su tiempo se suma al de esa variante).

## Lo que Whisper entendió en la frase 7 (marcas difíciles)

- `A_xtts_actual` (WER 37%): «Tengo estos auriculares Bluetooth para ti, los de Megret por 9 euros con 18 céntimos, los de Time por 9 euros con 84 céntimos, los de VDGP por 32 euros con 6 céntimos, los de VSDB Belier por 25 euros con 15 céntimos y los de Workmark Marejo, o el Mejian también te vea, y los que se están teniendo consciente, por si le conecta el dinero con 49 céntimos. ¿Te interesa alguno? He anotado un presupuesto de 50 euros»
- `B1_xtts_ritmo30` (WER 24%): «Tengo estos auriculares Bluetooth para ti. Los de Magret por 9 euros con 18 céntimos. Los de TAM por 9 euros con 84 céntimos. Los de WDGP por 32 euros con 6 céntimos. Los de GESIT es elitare. Aspado un artes. Dugo un vistios. De, em tu quieres, con 15 céntimos. y los de Olive por 16 euros con 49 céntimos. ¿Te interesa alguno? He anotado un presupuesto de 50 euros.»
- `B2_xtts_varias` (WER 22%): «Tengo estos auriculares Bluetooth para ti. Los de Magret por 9 euros con 18 céntimos. Los de TAN por 9 euros con 84 céntimos. Los de WDGP por 32 euros con 6 céntimos. Los de GESIT ES IBIKAE. ASPALO UN ARTIAS. DUGO UN MISTIOS. DE EL TOQUIERES con 15 céntimos. y los de OREF por 16 euros con 49 céntimos. ¿Te interesa alguno? He anotado un presupuesto de 50 euros.»
- `B3_xtts_varias_t075` (WER 6%): «Tengo estos auriculares Bluetooth para ti. Los de Migret por 9 euros con 18 céntimos. Los de Time por 9 euros con 84 céntimos. Los de WDGP por 32 euros con 6 céntimos. Los de DSSJVL por 25 euros con 15 céntimos. Y los de OliveViv por 16 euros con 49 céntimos. ¿Te interesa alguno? He anotado un presupuesto de 50 euros»
- `B4_xtts_turnos` (WER 7%): «Tengo estos auriculares Bluetooth para ti. Los de Megret por 9 euros con 18 céntimos. Los de Time por 9 euros con 84 céntimos. Los de VDGP por 32 euros con 6 céntimos. Los de GSTMLA por 25 euros con 15 céntimos. Y los de Holif por 16 euros con 49 céntimos. ¿Te interesa alguno? He anotado un presupuesto de 50 euros.»
- `B5_xtts_todo` (WER 15%): «Tengo estos auriculares Bluetooth para ti. Los de Magret por 9 euros con 18 céntimos. Los de Tang por 9 euros con 84 céntimos. Los de Buda BDSP por 32 euros con 6 céntimos. Los de GSI 8E Adephambos 5 o 25 euros con 15 céntimos. Y los de Boliv por 16 euros con 49 céntimos. ¿Te interesa alguno? He anotado un presupuesto de 50 euros.»
- `C2_f5_turnos` (WER 7%): «Tengo estos auriculares Bluetooth para ti, los de Gret por 9 euros con 18 céntimos, los de TN por 9 euros con 84 céntimos, los de URI por 32 euros con 6 céntimos, los de CELOVE por 25 euros con 15 céntimos y los de OLIP por 16 euros con 49 céntimos. ¿Te interesa alguno? He anotado un presupuesto de 50 euros.»
- `C_f5_spanish` (WER 10%): «Tengo estos auriculares BlueSplit Red. Para ti, los de Megret por 9 euros con 18 céntimos, los de Tean por 9 euros con 84 céntimos, los de Utipe por 32 euros con 6 céntimos, los de Chazelbel por 25 euros con 15 céntimos y los de Olip por 16 euros con 49 céntimos. ¿Te interesa alguno? He anotado un presupuesto de 50 euros.»
- `D1_chatterbox_v3` (WER 7%): «Tengo estos auriculares, Bluetooth, para ti. Los de Megret por 9 euros con 18 céntimos, los de Time por 9 euros con 84 céntimos, los de EGREP por 32 euros con 6 céntimos, los de Segepleo por 25 euros con 15 céntimos y los de Olive por 16 euros con 49 céntimos. ¿Te interesa alguno? He anotado un presupuesto de 50 euros.»
- `D2_chatterbox_latam` (WER 9%): «Tengo estos auriculares Bluetooth para ti. Los de MGRED por 9 euros con 18 céntimos, los de TIME por 9 euros con 84 céntimos, los de MGLE DEP por 32 euros con 6 céntimos, los de GCBL por 25 euros con 15 céntimos y los de OLIVE por 16 euros con 49 céntimos. ¿Te interesa alguno? He anotado un presupuesto de 50 euros.»
- `D3_chatterbox_latam_turnos` (WER 9%): «Tengo estos auriculares Bluetooth para ti. Los de M-GRED por 9 euros con 18 céntimos. Los de TIME por 9 euros con 84 céntimos. Los de WDAP por 32 euros con 6 céntimos. Los de GSBLE por 25 euros con 15 céntimos. Y los de OLIP por 16 euros con 49 céntimos. ¿Te interesa alguno? He anotado un presupuesto de 50 euros.»
- `E_xtts_conversion` (WER 40%): «Tengo estos auriculares Bluetooth para ti. Los de Meguet por 9 euros con 18 céntimos. Los de Time por 9 euros con 84 céntimos. Los de VDFP por 32 euros con 6 céntimos. Los de VSTV Belier por 25 euros con 15 céntimos. Y los de Ockmark, Maraco. Olmecian también te fea. Y la fecha está en ser parte del consiente. Monsele con el tema URB por 49 céntimos. ¿Te interesa alguno? y anotar un presupuesto de 50 euros.»
