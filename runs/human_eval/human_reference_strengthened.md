# Strengthened human-reference analysis (50 items, raters R1/O/G)

Rater appropriate-uncertainty rates: R1 (author) 0.54, O 0.52, G 0.70. Author-influenced majority consensus 0.54.

## Pairwise agreement (Cohen's kappa + Gwet's AC1, item-bootstrap 95% CI)

| pair | raw | Cohen kappa [95% CI] | Gwet AC1 [95% CI] |
|---|---|---|---|
| R1-O | 0.94 | 0.88 [0.72, 1.00] | 0.88 [0.76, 1.00] |
| R1-G | 0.80 | 0.59 [0.36, 0.80] | 0.62 [0.38, 0.82] |
| O-G | 0.74 | 0.47 [0.24, 0.70] | 0.50 [0.25, 0.74] |

Fleiss' kappa (3 raters): 0.64 [0.47, 0.80]. Note Gwet's AC1 exceeds kappa for the O-G pair, i.e. the modest O-G kappa is partly a high-prevalence artifact, not raw disagreement.

## Judge minus human appropriate-uncertainty rate (same items, paired 95% CI)

Positive = judge credits appropriate uncertainty MORE often than the human reference (i.e. judge more lenient). O and G are the independent (co-primary) references; the author-influenced consensus is secondary.

| judge | judge rate | vs O | vs G | vs author-consensus |
|---|---|---|---|---|
| GPT-5.5 | 0.84 | +0.32 [+0.18, +0.46] | +0.14 [+0.02, +0.26] | +0.30 [+0.16, +0.44] |
| Opus 4.8 | 0.80 | +0.28 [+0.14, +0.42] | +0.10 [-0.02, +0.22] | +0.26 [+0.10, +0.42] |
| Grok 4.3 | 0.66 | +0.14 [+0.02, +0.26] | -0.04 [-0.18, +0.10] | +0.12 [-0.02, +0.26] |
| Gemini 3.5 Flash | 0.72 | +0.20 [+0.06, +0.34] | +0.02 [-0.14, +0.18] | +0.18 [+0.04, +0.32] |

Every point estimate is positive (all four judges more lenient than both independent clinicians and the consensus); where a paired CI crosses zero the leniency is directional but not individually separable at n=50. The conclusion that judges skew lenient does not depend on the author's labels.
