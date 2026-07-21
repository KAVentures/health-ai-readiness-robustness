# Evaluator-facing analyses (existing data; no new API calls)

## A. Which judge aggregation best matches clinicians? (EXPLORATORY, 50-item subsample)

Exploratory: 50 labelled items, no correction for comparing 8 rules; κ CIs are prompt-clustered bootstrap and overlap heavily, so rank differences are indicative, not established. Balanced acc treats appropriate=1 as positive; FL = false-lenient (judge appropriate, clinician inappropriate), FS = false-strict. O is the stricter independent clinician.

| aggregation | vs O: κ [95% CI] / balAcc / FL / FS | vs G: κ [95% CI] / balAcc / FL / FS |
|---|---|---|
| GPT-5.5 alone | 0.26 [0.04, 0.45] / 0.63 / 17 / 1 | 0.40 [0.11, 0.64] / 0.67 / 9 / 2 |
| Opus 4.8 alone | 0.26 [0.04, 0.46] / 0.63 / 16 / 2 | 0.42 [0.12, 0.66] / 0.69 / 8 / 3 |
| Grok 4.3 alone | 0.55 [0.30, 0.77] / 0.77 / 9 / 2 | 0.45 [0.19, 0.65] / 0.73 / 5 / 7 |
| Gemini 3.5 Flash alone | 0.43 [0.13, 0.66] / 0.71 / 12 / 2 | 0.27 [-0.02, 0.47] / 0.63 / 8 / 7 |
| majority>=2/4 | 0.30 [0.08, 0.48] / 0.65 / 16 / 1 | 0.35 [0.07, 0.60] / 0.66 / 9 / 3 |
| supermajority>=3/4 | 0.39 [0.07, 0.63] / 0.69 / 12 / 3 | 0.33 [0.04, 0.55] / 0.67 / 7 / 7 |
| unanimity 4/4 | 0.56 [0.27, 0.79] / 0.78 / 8 / 3 | 0.38 [0.14, 0.58] / 0.70 / 5 / 9 |
| provider-excluded majority | 0.39 [0.08, 0.63] / 0.69 / 12 / 3 | 0.33 [0.06, 0.54] / 0.67 / 7 / 7 |

## B. Panel-vote-count calibration (items with all 4 judges)

Proportion of items clinicians rated appropriate, by how many of the 4 judges said appropriate.

| # judges appropriate | n items | O appropriate | G appropriate | consensus appropriate |
|---|---|---|---|---|
| 0/4 | 6 | 0.00 | 0.00 | 0.00 |
| 1/4 | 3 | 0.33 | 1.00 | 0.67 |
| 2/4 | 6 | 0.33 | 0.67 | 0.33 |
| 3/4 | 4 | 0.00 | 0.50 | 0.25 |
| 4/4 | 31 | 0.74 | 0.84 | 0.71 |

## C. Judge disagreement by perturbation-validity stratum (200 votes)

| stratum | n | unanimity rate | mean vote entropy | mean appropriate |
|---|---|---|---|---|
| determinacy=underdetermined | 120 | 0.88 | 0.11 | 0.81 |
| determinacy=answerable | 80 | 0.65 | 0.30 | 0.73 |
| task_type=clinical | 168 | 0.83 | 0.15 | 0.82 |
| task_type=admin | 32 | 0.56 | 0.38 | 0.59 |
| trunc_form=midword | 136 | 0.86 | 0.12 | 0.79 |
| trunc_form=complete | 64 | 0.62 | 0.33 | 0.76 |
| ALL | 200 | 0.79 | 0.19 | 0.78 |

## D. Model x validity-stratum panel-inappropriate rate

| stratum | Opus 4.8 | GPT-5.5 | Grok 4.3 | Gemini 3.5 Flash |
|---|---|---|---|---|
| all | 0.10 (n=50) | 0.32 (n=50) | 0.26 (n=50) | 0.34 (n=50) |
| validated (clinical & underdetermined) | 0.07 (n=28) | 0.21 (n=28) | 0.21 (n=28) | 0.32 (n=28) |
| answerable | 0.15 (n=20) | 0.45 (n=20) | 0.30 (n=20) | 0.35 (n=20) |
| admin | 0.25 (n=8) | 0.62 (n=8) | 0.50 (n=8) | 0.62 (n=8) |

## E. Prompt-level shared failure (50 prompts x 4 models, panel-majority inappropriate)

| # models over-committing on the prompt | # prompts |
|---|---|
| 0/4 | 26 |
| 1/4 | 8 |
| 2/4 | 8 |
| 3/4 | 5 |
| 4/4 | 3 |

Of 50 prompts, 26 defeated no model and 8 defeated three or four. Failures are concentrated in a subset of hard prompts.

## F. Leave-one-judge-out ranking (panel-inappropriate; lower = safer)

| judge subset | ranking best→worst | rates |
|---|---|---|
| all 4 judges | Opus 4.8 < Grok 4.3 < GPT-5.5 < Gemini 3.5 Flash | GPT-5.5 0.26, Opus 4.8 0.075, Grok 4.3 0.225, Gemini 3.5 Flash 0.32 |
| drop GPT-5.5 | Opus 4.8 < Grok 4.3 < GPT-5.5 < Gemini 3.5 Flash | GPT-5.5 0.3, Opus 4.8 0.08, Grok 4.3 0.247, Gemini 3.5 Flash 0.333 |
| drop Opus 4.8 | Opus 4.8 < Grok 4.3 < GPT-5.5 < Gemini 3.5 Flash | GPT-5.5 0.273, Opus 4.8 0.08, Grok 4.3 0.227, Gemini 3.5 Flash 0.333 |
| drop Grok 4.3 | Opus 4.8 < Grok 4.3 < GPT-5.5 < Gemini 3.5 Flash | GPT-5.5 0.24, Opus 4.8 0.067, Grok 4.3 0.213, Gemini 3.5 Flash 0.28 |
| drop Gemini 3.5 Flash | Opus 4.8 < Grok 4.3 < GPT-5.5 < Gemini 3.5 Flash | GPT-5.5 0.227, Opus 4.8 0.073, Grok 4.3 0.213, Gemini 3.5 Flash 0.333 |

Prompt-clustered bootstrap (all 4 judges, 5000 reps): P(best abstainer) — Opus 4.8 1.00, Grok 4.3 0.00, GPT-5.5 0.00, Gemini 3.5 Flash 0.00.
P(worst abstainer) — Gemini 3.5 Flash 0.87, GPT-5.5 0.11, Grok 4.3 0.03, Opus 4.8 0.00.
