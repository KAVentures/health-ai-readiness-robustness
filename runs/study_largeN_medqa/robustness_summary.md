# Robustness study

- MedQA n per cell: 300
- datasets: medqa
- models: opus-4_8-high, gpt-5_5-high, grok-4_3, gemini-3_5-flash

## MCQ robustness (MedQA/MedMCQA)

Reward: accuracy for `none`/`shuffle`; appropriate-abstention rate for `remove_answer`/`remove_context`.

| dataset | model | acc | acc(shuf) | Δacc(shuf) | abstain(ans) | inappr(ans) | abstain(ctx) | inappr(ctx) |
|---|---|---|---|---|---|---|---|---|
| medqa | opus-4_8-high | 0.953 | 0.953 | 0.000 | 0.843 | 0.157 | 0.000 | 1.000 |
| medqa | gpt-5_5-high | 0.960 | 0.967 | -0.007 | 0.000 | 1.000 | 0.000 | 1.000 |
| medqa | grok-4_3 | 0.920 | 0.923 | -0.003 | 0.907 | 0.093 | 0.913 | 0.087 |
| medqa | gemini-3_5-flash | 0.953 | 0.950 | 0.003 | 0.380 | 0.620 | 0.000 | 1.000 |
