# Within-model sampling variance (MedQA abstention cells)

Each cell re-run 5x at n=50, single rollout each, fixed items. Rate = inappropriate-confident (1 - appropriate-abstention).

| model | condition | mean | SD | min | max | range |
|---|---|---|---|---|---|---|
| gpt-5_5-high | remove_answer | 1.000 | 0.000 | 1.000 | 1.000 | 0.000 |
| gpt-5_5-high | remove_context | 1.000 | 0.000 | 1.000 | 1.000 | 0.000 |
| gemini-3_5-flash | remove_answer | 1.000 | 0.000 | 1.000 | 1.000 | 0.000 |
| gemini-3_5-flash | remove_context | 1.000 | 0.000 | 1.000 | 1.000 | 0.000 |
