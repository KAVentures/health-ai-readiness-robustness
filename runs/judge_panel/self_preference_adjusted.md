# Judge-severity-adjusted self-preference

Votes analysed: 798 (800 minus 2 xAI-judge moderation drops).

## 1. Descriptive difference-in-differences (probability scale)

Raw = own judge on self − peer judges on self (the paper's original statistic).
DiD additionally nets out the own judge's general leniency on *other* subjects:
DiD = (own on self − own on others) − (peers on self − peers on others).

| subject | own judge on self | own judge on others | peers on self | peers on others | raw self-pref | severity-adjusted DiD |
|---|---|---|---|---|---|---|
| GPT-5.5 | 0.860 | 0.833 | 0.698 | 0.779 | +0.162 | +0.108 |
| Opus 4.8 | 0.940 | 0.760 | 0.920 | 0.721 | +0.020 | -0.019 |
| Grok 4.3 | 0.735 | 0.711 | 0.787 | 0.804 | -0.052 | +0.041 |
| Gemini 3.5 Flash | 0.720 | 0.767 | 0.667 | 0.828 | +0.053 | +0.114 |

## 2. Fixed-effects logistic regression (subject FE + judge FE + same-provider)

- Shared same-provider coefficient: **+0.350 log-odds** (95% item-clustered bootstrap CI [+0.159, +0.562])
- GPT-5.5-specific same-provider coefficient: **+0.515 log-odds** (95% CI [-0.101, +1.348])
- Same-provider coefficient for the other three subjects: +0.297 (95% CI [+0.104, +0.557])
- GPT-5.5 effect on the probability scale at its peer-judged baseline (0.70): +0.096

## 3. Permutation test (own-judge assignment permuted per subject, 2000 reps)

- Observed shared coefficient +0.350, two-sided p = 0.0400

Interpretation: the raw +0.16 for GPT-5.5 conflates the GPT-5.5 judge's general leniency with genuine self-preference; the DiD and regression isolate the latter. Report the adjusted values as primary and the raw gap as descriptive.
