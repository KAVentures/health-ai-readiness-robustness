# Robustness study

- MedQA n per cell: 100
- datasets: medqa
- models: opus-4_8-high, gpt-5_5-high, grok-4_3, gemini-3_1-pro-high
- HealthBench: difficulty=consensus, n=50, judge=gpt-4.1-mini

## MCQ robustness (MedQA/MedMCQA)

Reward: accuracy for `none`/`shuffle`; appropriate-abstention rate for `remove_answer`/`remove_context`.

| dataset | model | acc | acc(shuf) | Δacc(shuf) | abstain(ans) | inappr(ans) | abstain(ctx) | inappr(ctx) |
|---|---|---|---|---|---|---|---|---|
| medqa | opus-4_8-high | 0.920 | 0.920 | 0.000 | 0.820 | 0.180 | 0.800 | 0.200 |
| medqa | gpt-5_5-high | 0.940 | 0.980 | -0.040 | 0.880 | 0.120 | 0.830 | 0.170 |
| medqa | grok-4_3 | 0.960 | 0.950 | 0.010 | 0.890 | 0.110 | 0.900 | 0.100 |
| medqa | gemini-3_1-pro-high | 0.110 | 0.000 | 0.110 | 0.000 | 1.000 | 0.000 | 1.000 |

## HealthBench open-ended robustness

Baseline = standard HealthBench rubric score. Probe = appropriate-uncertainty rate after context removal; `inappr` = 1 - probe.

| model | hb_baseline | appropriate_uncertainty | inappropriate_confident |
|---|---|---|---|
| opus-4_8-high | 0.967 | 0.920 | 0.080 |
| gpt-5_5-high | 0.967 | 0.720 | 0.280 |
| grok-4_3 | 0.903 | 0.800 | 0.200 |
| gemini-3_1-pro-high | 0.113 | 0.180 | 0.820 |
