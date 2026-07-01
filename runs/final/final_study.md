# Robustness & readiness study — final results

MedQA n=100/cell; HealthBench (consensus) n=50. Models at high reasoning effort.
HealthBench baseline judged by gpt-4.1-mini; context-removal probe judged by gpt-5.5.

## MCQ robustness (MedQA)

| model | acc | acc(shuffle) | Δacc(shuffle) | inappr-confident (answer removed) | inappr-confident (context removed) |
|---|---|---|---|---|---|
| Opus 4.8 | 0.920 | 0.920 | 0.000 | 0.180 | 0.200 |
| GPT-5.5 | 0.940 | 0.980 | -0.040 | 0.120 | 0.170 |
| Grok 4.3 | 0.960 | 0.950 | 0.010 | 0.110 | 0.100 |
| Gemini 3.5 Flash | 0.960 | 0.960 | 0.000 | 0.060 | 0.150 |

## HealthBench open-ended robustness

| model | baseline rubric | appropriate uncertainty | inappropriate confident |
|---|---|---|---|
| Opus 4.8 | 0.913 | 0.940 | 0.060 |
| GPT-5.5 | 0.983 | 0.860 | 0.140 |
| Grok 4.3 | 0.927 | 0.840 | 0.160 |
| Gemini 3.5 Flash | 0.973 | 0.720 | 0.280 |
