# Within-model sampling variance (MedQA abstention cells)

Each cell re-run 5x at n=50, single rollout each, fixed items. Rate = inappropriate-confident (1 - appropriate-abstention).

| model | condition | mean | SD | min | max | range |
|---|---|---|---|---|---|---|
| gpt-5_5-high | remove_answer | 0.172 | 0.010 | 0.160 | 0.180 | 0.020 |
| gpt-5_5-high | remove_context | 0.144 | 0.008 | 0.140 | 0.160 | 0.020 |
