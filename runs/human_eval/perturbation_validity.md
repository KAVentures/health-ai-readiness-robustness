# Perturbation-validity audit and sensitivity analysis

33 unique perturbed prompts underlie the 50 annotation items. Author audit (disclosed COI). Counts of unique prompts by (truncation, determinacy, task):

- grammatically complete cut: 9/33; mid-word cut: 24/33
- genuinely underdetermined: 19/33; still answerable: 14/33
- clinical-decision task: 26/33; rewriting/administrative: 7/33

## Headline quantities by stratum (50-item annotation level)

Judge inappropriate = 1 - mean panel appropriate-uncertainty rate. Consensus/O/G = human appropriate-uncertainty rates.

| stratum | n | judge inappropriate | consensus appropriate | O | G | judge − consensus |
|---|---|---|---|---|---|---|
| ALL (50 items) | 50 | 0.24 | 0.54 | 0.52 | 0.70 | +0.21 |
| VALIDATED: clinical & underdetermined | 28 | 0.21 | 0.50 | 0.46 | 0.68 | +0.29 |
| clinical only | 42 | 0.23 | 0.52 | 0.48 | 0.71 | +0.25 |
| admin/rewriting only | 8 | 0.34 | 0.62 | 0.75 | 0.62 | +0.03 |
| underdetermined only | 30 | 0.20 | 0.53 | 0.50 | 0.70 | +0.27 |
| answerable only | 20 | 0.31 | 0.55 | 0.55 | 0.70 | +0.14 |
| midword truncation | 38 | 0.26 | 0.47 | 0.42 | 0.68 | +0.27 |
| grammatically complete | 12 | 0.21 | 0.75 | 0.83 | 0.75 | +0.04 |

**Reading.** On the validated subset (n=28: a clinical task with clinically relevant information genuinely removed), the judge-reported inappropriate-confident rate is 0.21 vs 0.24 on all 50, and the judge-minus-human leniency gap is +0.29 vs +0.21. The over-commitment finding and the judge-leniency finding both persist — and strengthen — once ill-posed (answerable or administrative) items are removed, which is the direction that supports validity rather than undermining it.
