# Within-model sampling variance (MedQA abstention cells)

Each cell re-run 5x at n=50, single rollout each, fixed items. Rate = inappropriate-confident (1 - appropriate-abstention).

| model | condition | mean | SD | min | max | range |
|---|---|---|---|---|---|---|
| gemini-3_5-flash | remove_answer | 0.088 | 0.010 | 0.080 | 0.100 | 0.020 |
| gemini-3_5-flash | remove_context | 0.124 | 0.023 | 0.080 | 0.140 | 0.060 |
