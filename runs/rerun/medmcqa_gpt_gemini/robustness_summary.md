# Robustness study

- MedQA n per cell: 200
- datasets: medmcqa
- models: gpt-5_5-high, gemini-3_5-flash

## MCQ robustness (MedQA/MedMCQA)

Reward: accuracy for `none`/`shuffle`; appropriate-abstention rate for `remove_answer`/`remove_context`.

| dataset | model | acc | acc(shuf) | Δacc(shuf) | abstain(ans) | inappr(ans) | abstain(ctx) | inappr(ctx) |
|---|---|---|---|---|---|---|---|---|
| medmcqa | gpt-5_5-high | 0.900 | 0.880 | 0.020 | 0.595 | 0.405 | 0.015 | 0.985 |
| medmcqa | gemini-3_5-flash | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 0.000 | 1.000 |
