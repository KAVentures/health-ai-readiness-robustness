# Multi-annotator validity + inter-rater reliability

Annotators: **G, O, R1** (3 humans). Common items labeled by all: **50**.


## 1. Each annotator vs LLM judges (validity)

Cohen's κ of each human annotator against each judge (raw agreement in JSON).

| annotator | n | human rate | vs GPT-5.5 (κ) | vs Opus (κ) | vs Grok (κ) | vs Gemini (κ) |
|---|---|---|---|---|---|---|
| G | 50 | 0.700 | 0.396 | 0.421 | 0.450 | 0.272 |
| O | 50 | 0.520 | 0.260 | 0.262 | 0.554 | 0.430 |
| R1 | 50 | 0.540 | 0.281 | 0.202 | 0.425 | 0.378 |

## 2. Human inter-rater reliability

**Fleiss' κ across all 3 humans (n=50 common items): 0.643.**

| pair | n | raw agreement | Cohen's κ |
|---|---|---|---|
| G ↔ O | 50 | 0.740 | 0.472 |
| G ↔ R1 | 50 | 0.800 | 0.587 |
| O ↔ R1 | 50 | 0.940 | 0.880 |

## 3. Human consensus (majority vote) vs LLM judges

Consensus over 50 items (ties dropped: 0); consensus appropriate-uncertainty rate **0.540** (n=50).

| judge | n | raw agreement | Cohen's κ |
|---|---|---|---|
| GPT-5.5 | 50 | 0.660 | 0.281 |
| Opus 4.8 | 50 | 0.620 | 0.202 |
| Grok 4.3 | 50 | 0.720 | 0.425 |
| Gemini 3.5 Flash | 50 | 0.700 | 0.378 |
