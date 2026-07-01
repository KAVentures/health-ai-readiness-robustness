# Robustness study

- MedQA n per cell: 200
- datasets: medmcqa
- models: gpt-5_5-high

## MCQ robustness (MedQA/MedMCQA)

Reward: accuracy for `none`/`shuffle`; appropriate-abstention rate for `remove_answer`/`remove_context`.

| dataset | model | acc | acc(shuf) | Δacc(shuf) | abstain(ans) | inappr(ans) | abstain(ctx) | inappr(ctx) |
|---|---|---|---|---|---|---|---|---|
| medmcqa | gpt-5_5-high | — | — | — | — | — | 0.100 | 0.900 |
