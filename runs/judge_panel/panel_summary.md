# Cross-provider judge panel — open-ended context-removal probe

Items judged: 200 (4 subject models x 50). GPT-5.5 votes from the saved run; Opus/Grok/Gemini called fresh on identical inputs.

Metric: appropriate-uncertainty rate (fraction of items each judge marks the criterion met).


## Inter-rater reliability

- Fleiss' kappa (4 judges, 198 complete items): **0.649**
- Mean pairwise agreement: **0.879**
- Judge parse/call errors: Grok 4.3=2

## Appropriate-uncertainty rate by judge (rows = subject model, cols = judge)

| subject \ judge | GPT-5.5 | Opus 4.8 | Grok 4.3 | Gemini 3.5 Flash |
|---|---|---|---|---|
| Opus 4.8 | 0.940 | 0.940 | 0.900 | 0.920 |
| GPT-5.5 | 0.860 | 0.780 | 0.673 | 0.640 |
| Grok 4.3 | 0.840 | 0.780 | 0.735 | 0.740 |
| Gemini 3.5 Flash | 0.720 | 0.720 | 0.560 | 0.720 |
| **all subjects** | 0.840 | 0.805 | 0.717 | 0.755 |

## Self-preference (leave-one-provider-out)

For each subject model: its own-provider judge's rate minus the mean of the other three judges' rates on the same items. Positive = own judge credits more appropriate-uncertainty than peers.

| subject model | own provider | own-judge rate | peer-mean rate | delta (self - peer) |
|---|---|---|---|---|
| Opus 4.8 | Opus 4.8 | 0.940 | 0.920 | 0.020 |
| GPT-5.5 | GPT-5.5 | 0.860 | 0.698 | 0.162 |
| Grok 4.3 | Grok 4.3 | 0.735 | 0.787 | -0.052 |
| Gemini 3.5 Flash | Gemini 3.5 Flash | 0.720 | 0.667 | 0.053 |
