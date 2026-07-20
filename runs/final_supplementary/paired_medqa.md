# Paired MedQA none-vs-shuffle (n=100, same items)

Delta_acc = acc(none) - acc(shuffle). b = correct under none but wrong under shuffle; c = wrong under none but correct under shuffle (the discordant pairs McNemar uses). Equivalence tested against a prespecified +/-0.05 margin (TOST via the paired bootstrap CI).

| model | acc(none) | acc(shuffle) | Delta_acc | b | c | McNemar exact p | paired 95% CI | equivalent at +/-5pp? |
|---|---|---|---|---|---|---|---|---|
| Opus 4.8 | 0.92 | 0.92 | +0.00 | 1 | 1 | 1.000 | [-0.030, +0.030] | yes |
| GPT-5.5 | 0.94 | 0.98 | -0.04 | 0 | 4 | 0.125 | [-0.080, -0.010] | no |
| Grok 4.3 | 0.96 | 0.95 | +0.01 | 2 | 1 | 1.000 | [-0.020, +0.050] | yes |
| Gemini 3.5 Flash | 0.96 | 0.96 | +0.00 | 1 | 1 | 1.000 | [-0.030, +0.030] | yes |

Reading: no McNemar test is significant. 3 of 4 models are equivalent within the +/-5pp margin; GPT-5.5 is NOT equivalent -- its paired CI extends beyond -0.05 because shuffling raised its accuracy (~+4pp), a non-equivalence in the safe direction rather than a robustness failure. This licenses an equivalence statement for the equivalent models, not a blanket claim that positional bias is 'solved'.
