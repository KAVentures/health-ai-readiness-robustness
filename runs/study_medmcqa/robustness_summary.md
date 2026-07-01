# Robustness study

- MedQA n per cell: 200
- datasets: medmcqa
- models: opus-4_8-high, gpt-5_5-high, grok-4_3, gemini-3_5-flash

## MCQ robustness (MedQA/MedMCQA)

Reward: accuracy for `none`/`shuffle`; appropriate-abstention rate for `remove_answer`/`remove_context`.

| dataset | model | acc | acc(shuf) | Δacc(shuf) | abstain(ans) | inappr(ans) | abstain(ctx) | inappr(ctx) |
|---|---|---|---|---|---|---|---|---|
| medmcqa | opus-4_8-high | 0.820 | 0.805 | 0.015 | 0.625 | 0.375 | 0.085 | 0.915 |
| medmcqa | gpt-5_5-high | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 0.000 | 1.000 |
| medmcqa | grok-4_3 | 0.865 | 0.840 | 0.025 | 0.695 | 0.305 | 0.145 | 0.855 |
| medmcqa | gemini-3_5-flash | 0.010 | 0.005 | 0.005 | 0.000 | 1.000 | 0.000 | 1.000 |
