# Robustness study

- MedQA n per cell: 300
- datasets: medqa
- models: opus-4_8-high

## MCQ robustness (MedQA/MedMCQA)

Reward: accuracy for `none`/`shuffle`; appropriate-abstention rate for `remove_answer`/`remove_context`.

| dataset | model | acc | acc(shuf) | Δacc(shuf) | abstain(ans) | inappr(ans) | abstain(ctx) | inappr(ctx) |
|---|---|---|---|---|---|---|---|---|
| medqa | opus-4_8-high | — | — | — | — | — | 0.777 | 0.223 |
