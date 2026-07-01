# Robustness study

- MedQA n per cell: 300
- datasets: medqa
- models: gemini-3_5-flash

## MCQ robustness (MedQA/MedMCQA)

Reward: accuracy for `none`/`shuffle`; appropriate-abstention rate for `remove_answer`/`remove_context`.

| dataset | model | acc | acc(shuf) | Δacc(shuf) | abstain(ans) | inappr(ans) | abstain(ctx) | inappr(ctx) |
|---|---|---|---|---|---|---|---|---|
| medqa | gemini-3_5-flash | — | — | — | 0.923 | 0.077 | 0.873 | 0.127 |
