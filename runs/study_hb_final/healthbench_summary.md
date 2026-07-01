# HealthBench open-ended robustness

- difficulty=consensus, n=50, judge=gpt-5.5
- models: opus-4_8-high, gpt-5_5-high, grok-4_3, gemini-3_5-flash

## HealthBench open-ended robustness

Baseline judge: gpt-4.1-mini. Probe judge: gpt-5.5. Baseline = standard HealthBench rubric score. Probe = appropriate-uncertainty rate after context removal; `inappr` = 1 - probe.

| model | hb_baseline | appropriate_uncertainty | inappropriate_confident |
|---|---|---|---|
| opus-4_8-high | 0.913 | 0.940 | 0.060 |
| gpt-5_5-high | 0.983 | 0.860 | 0.140 |
| grok-4_3 | 0.927 | 0.840 | 0.160 |
| gemini-3_5-flash | 0.973 | 0.720 | 0.280 |
