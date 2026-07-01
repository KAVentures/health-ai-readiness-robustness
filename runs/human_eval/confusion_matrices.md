# Judge-vs-human confusion matrices (blinded 50-item subsample)

Cells: counts of items. **false-lenient** = judge says appropriate-uncertainty but human says confident/inappropriate (judge too soft); **false-strict** = judge says inappropriate but human says appropriate. The asymmetry is the key finding: judges err lenient far more than strict.

| judge | both-appropriate | both-inappropriate | false-lenient (J=1,H=0) | false-strict (J=0,H=1) |
|---|---|---|---|---|
| GPT-5.5 | 26 | 7 | **16** | 1 |
| Opus 4.8 | 24 | 7 | **16** | 3 |
| Grok 4.3 | 23 | 13 | **10** | 4 |
| Gemini 3.5 Flash | 24 | 11 | **12** | 3 |
