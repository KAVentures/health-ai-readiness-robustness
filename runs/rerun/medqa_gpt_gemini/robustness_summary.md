# Robustness study

- MedQA n per cell: 300
- datasets: medqa
- models: gpt-5_5-high, gemini-3_5-flash

## MCQ robustness (MedQA/MedMCQA)

Reward: accuracy for `none`/`shuffle`; appropriate-abstention rate for `remove_answer`/`remove_context`.

| dataset | model | acc | acc(shuf) | Δacc(shuf) | abstain(ans) | inappr(ans) | abstain(ctx) | inappr(ctx) |
|---|---|---|---|---|---|---|---|---|
| medqa | gpt-5_5-high | — | — | — | 0.857 | 0.143 | 0.823 | 0.177 |
| medqa | gemini-3_5-flash | — | — | — | 0.010 | 0.990 | 0.000 | 1.000 |
