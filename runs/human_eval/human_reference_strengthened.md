# Strengthened human-reference analysis (50 items, raters R1/O/G)

All bootstrap CIs are **prompt-clustered** (resampling the 33 unique perturbed prompts underlying the 50 annotation items), which is more conservative than resampling items independently.

Rater appropriate-uncertainty rates: R1 (author) 0.54, O 0.52, G 0.70. Author-influenced majority consensus 0.54.

## Pairwise agreement (Cohen's kappa + Gwet's AC1, prompt-clustered bootstrap 95% CI)

| pair | raw | Cohen kappa [95% CI] | Gwet AC1 [95% CI] |
|---|---|---|---|
| R1-O | 0.94 | 0.88 [0.71, 1.00] | 0.88 [0.73, 1.00] |
| R1-G | 0.80 | 0.59 [0.37, 0.79] | 0.62 [0.39, 0.83] |
| O-G | 0.74 | 0.47 [0.24, 0.68] | 0.50 [0.25, 0.74] |

Fleiss' kappa (3 raters): 0.64 [0.47, 0.79]. Note Gwet's AC1 exceeds kappa for the O-G pair, i.e. the modest O-G kappa is partly a high-prevalence artifact, not raw disagreement.

## Judge minus human appropriate-uncertainty rate (same items, paired 95% CI)

Positive = judge credits appropriate uncertainty MORE often than the human reference (i.e. judge more lenient). O and G are the independent (co-primary) references; the author-influenced consensus is secondary.

| judge | judge rate | vs O | vs G | vs author-consensus |
|---|---|---|---|---|
| GPT-5.5 | 0.84 | +0.32 [+0.18, +0.46] | +0.14 [+0.04, +0.26] | +0.30 [+0.17, +0.44] |
| Opus 4.8 | 0.80 | +0.28 [+0.13, +0.42] | +0.10 [-0.02, +0.22] | +0.26 [+0.10, +0.41] |
| Grok 4.3 | 0.66 | +0.14 [+0.02, +0.27] | -0.04 [-0.18, +0.09] | +0.12 [-0.02, +0.27] |
| Gemini 3.5 Flash | 0.72 | +0.20 [+0.06, +0.35] | +0.02 [-0.13, +0.18] | +0.18 [+0.04, +0.34] |

All four judges are significantly more lenient than the stricter clinician O (paired CIs exclude zero). Three of four (GPT-5.5, Opus, Gemini) are also significantly more lenient than the author-influenced consensus; Grok's difference vs the consensus is directionally positive (+0.12) but its CI crosses zero ([-0.02, +0.27]). Against the more lenient clinician G the gap shrinks further: only GPT-5.5 clearly separates, and Grok is directionally stricter than G (-0.04, CI crosses zero). The leniency conclusion holds firmly against the stricter clinician, is weaker against the consensus and the more lenient clinician, and does not depend on the author's labels.
