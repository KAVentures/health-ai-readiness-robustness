# Within-model sampling variance (MedQA abstention cells)

Each cell re-run 5x at n=50, single rollout each, fixed items. Rate = inappropriate-confident (1 - appropriate-abstention).

| model | condition | mean | SD | min | max | range |
|---|---|---|---|---|---|---|
| opus-4_8-high | remove_answer | 0.268 | 0.010 | 0.260 | 0.280 | 0.020 |
| opus-4_8-high | remove_context | 0.164 | 0.015 | 0.140 | 0.180 | 0.040 |
| gpt-5_5-high | remove_answer | 1.000 | 0.000 | 1.000 | 1.000 | 0.000 |
| gpt-5_5-high | remove_context | 1.000 | 0.000 | 1.000 | 1.000 | 0.000 |
| grok-4_3 | remove_answer | 0.184 | 0.020 | 0.160 | 0.220 | 0.060 |
| grok-4_3 | remove_context | 0.076 | 0.008 | 0.060 | 0.080 | 0.020 |
| gemini-3_5-flash | remove_answer | 1.000 | 0.000 | 1.000 | 1.000 | 0.000 |
| gemini-3_5-flash | remove_context | 1.000 | 0.000 | 1.000 | 1.000 | 0.000 |
