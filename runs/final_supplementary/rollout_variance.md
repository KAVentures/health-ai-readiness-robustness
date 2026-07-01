# Within-model sampling variance (MedQA abstention cells)

Each cell re-run 5× at n=50, single rollout each, fixed items. Rate = inappropriate-confident (1 − appropriate-abstention). Quota-blocked (all-error) repetitions are excluded.

| model | condition | mean | SD | min | max | range | k |
|---|---|---|---|---|---|---|---|
| Opus 4.8 | remove_answer | 0.268 | 0.010 | 0.260 | 0.280 | 0.020 | 5 |
| Opus 4.8 | remove_context | 0.164 | 0.015 | 0.140 | 0.180 | 0.040 | 5 |
| GPT-5.5 | remove_answer | 0.172 | 0.010 | 0.160 | 0.180 | 0.020 | 5 |
| GPT-5.5 | remove_context | 0.144 | 0.008 | 0.140 | 0.160 | 0.020 | 5 |
| Grok 4.3 | remove_answer | 0.184 | 0.020 | 0.160 | 0.220 | 0.060 | 5 |
| Grok 4.3 | remove_context | 0.076 | 0.008 | 0.060 | 0.080 | 0.020 | 5 |
| Gemini 3.5 Flash | remove_answer | 0.088 | 0.010 | 0.080 | 0.100 | 0.020 | 5 |
| Gemini 3.5 Flash | remove_context | 0.124 | 0.023 | 0.080 | 0.140 | 0.060 | 5 |
