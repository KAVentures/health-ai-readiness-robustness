# Larger-n MedQA (n = 300 per cell)

Accuracy for `none`/`shuffle`; inappropriate-confident rate (1 − appropriate abstention) for the removal conditions. Wilson 95% CIs. Only error-free runs are included.

| model | acc (none) | acc (shuffle) | Δacc | inappropriate — answer removed | inappropriate — context removed |
|---|---|---|---|---|---|
| Opus 4.8 | 0.953 | 0.953 | +0.000 | 0.157 [0.12, 0.20] | 0.223 [0.18, 0.27] |
| GPT-5.5 | 0.960 | 0.967 | -0.007 | 0.143 [0.11, 0.19] | 0.177 [0.14, 0.22] |
| Grok 4.3 | 0.920 | 0.923 | -0.003 | 0.093 [0.07, 0.13] | 0.087 [0.06, 0.12] |
| Gemini 3.5 Flash | 0.953 | 0.950 | +0.003 | 0.077 [0.05, 0.11] | 0.127 [0.09, 0.17] |
