# Appendix C. Raw counts (MedQA, n=100 per cell)

Integer counts behind every MCQ rate, so CIs can be recomputed. For `none`/`shuffle`, count = correct answers. For the removal conditions, `abstain` = correct abstentions and `inappropriate` = confident wrong answers (abstain + inappropriate = n).

| model | correct (none) | correct (shuffle) | abstain (ans) | inappropriate (ans) | abstain (ctx) | inappropriate (ctx) |
|---|---|---|---|---|---|---|
| Opus 4.8 | 92/100 | 92/100 | 82/100 | 18/100 | 80/100 | 20/100 |
| GPT-5.5 | 94/100 | 98/100 | 88/100 | 12/100 | 83/100 | 17/100 |
| Grok 4.3 | 96/100 | 95/100 | 89/100 | 11/100 | 90/100 | 10/100 |
| Gemini 3.5 Flash | 96/100 | 96/100 | 94/100 | 6/100 | 85/100 | 15/100 |
