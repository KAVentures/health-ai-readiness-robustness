# Robustness study

- MedQA n per cell: 200
- datasets: medmcqa
- models: gemini-3_5-flash

## MCQ robustness (MedQA/MedMCQA)

Reward: accuracy for `none`/`shuffle`; appropriate-abstention rate for `remove_answer`/`remove_context`.

| dataset | model | acc | acc(shuf) | Δacc(shuf) | abstain(ans) | inappr(ans) | abstain(ctx) | inappr(ctx) |
|---|---|---|---|---|---|---|---|---|
| medmcqa | gemini-3_5-flash | 0.875 | 0.210 | 0.665 | 0.750 | 0.250 | 0.105 | 0.895 |
