# Robustness study

- MedQA n per cell: 1
- datasets: medqa
- models: opus-4_8-high, gpt-5_5-high, gemini-3_5-flash

## MCQ robustness (MedQA/MedMCQA)

Reward: accuracy for `none`/`shuffle`; appropriate-abstention rate for `remove_answer`/`remove_context`.

| dataset | model | acc | acc(shuf) | Δacc(shuf) | abstain(ans) | inappr(ans) | abstain(ctx) | inappr(ctx) |
|---|---|---|---|---|---|---|---|---|
| medqa | opus-4_8-high | 1.000 | — | — | — | — | — | — |
| medqa | gpt-5_5-high | 1.000 | — | — | — | — | — | — |
| medqa | gemini-3_5-flash | 1.000 | — | — | — | — | — | — |
