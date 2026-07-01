# Robustness study

- MedQA n per cell: 100
- datasets: medqa
- models: gemini-3_5-flash
- HealthBench: difficulty=consensus, n=50, judge=gpt-5.5

## MCQ robustness (MedQA/MedMCQA)

Reward: accuracy for `none`/`shuffle`; appropriate-abstention rate for `remove_answer`/`remove_context`.

| dataset | model | acc | acc(shuf) | Δacc(shuf) | abstain(ans) | inappr(ans) | abstain(ctx) | inappr(ctx) |
|---|---|---|---|---|---|---|---|---|
| medqa | gemini-3_5-flash | 0.960 | 0.960 | 0.000 | 0.940 | 0.060 | 0.850 | 0.150 |

## HealthBench open-ended robustness

Judge: gpt-5.5. Baseline = standard HealthBench rubric score. Probe = appropriate-uncertainty rate after context removal; `inappr` = 1 - probe.

| model | hb_baseline | appropriate_uncertainty | inappropriate_confident |
|---|---|---|---|
| gemini-3_5-flash | 0.000 | 0.740 | 0.260 |
