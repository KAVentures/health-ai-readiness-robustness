# MedRobust robustness study

- n per cell: 20
- datasets: medqa
- models: opus-4_8-high, gpt-5_5-high, grok-4_3, gemini-3_1-pro-high

Reward semantics: accuracy for `none`/`shuffle`; appropriate-abstention rate for `remove_answer`/`remove_context`.

| dataset | model | acc | acc(shuf) | Δacc(shuf) | abstain(ans) | inappr(ans) | abstain(ctx) | inappr(ctx) |
|---|---|---|---|---|---|---|---|---|
| medqa | opus-4_8-high | 0.900 | 0.900 | 0.000 | 0.750 | 0.250 | 0.900 | 0.100 |
| medqa | gpt-5_5-high | 0.950 | 0.950 | 0.000 | 0.800 | 0.200 | 0.850 | 0.150 |
| medqa | grok-4_3 | 0.900 | 0.900 | 0.000 | 0.850 | 0.150 | 0.950 | 0.050 |
| medqa | gemini-3_1-pro-high | 0.900 | 0.900 | 0.000 | 0.950 | 0.050 | 0.950 | 0.050 |
