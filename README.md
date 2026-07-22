# Evaluating Medical AI Under Missing Information: Same-Provider Judges and Human Raters Change Apparent Safety

**A missing-information stress-test of frontier models on open-ended medical conversation, showing that the LLM *judge* — its provider and its calibration against clinicians — is part of the measurement.** The closed-ended MedQA/MedMCQA battery serves as an anchor.

Author: **Koyar Afrasyab, M.D.**
Affiliation: **Kinvectum AB**
Funding: **Kinvectum AB**
Preprint: **[arXiv:2607.18828](https://arxiv.org/abs/2607.18828)**

This repository contains the manuscript, evaluation environments, orchestration/judging/scoring code, saved analysis tables, figures, judge-panel votes, the perturbation-validity audit, and human-annotation data. It extends the input-perturbation methodology of Gu et al., *Evaluating the robustness and readiness of large frontier models in health AI applications* (Nature Medicine 2026; preprint arXiv:2509.18234) from closed-ended/multimodal tasks to **open-ended clinical conversation under missing information**, on top of the [MedARC-AI/medmarks](https://github.com/MedARC-AI/medmarks) harness.

The primary contribution is the open-ended missing-information probe and its **evaluator analysis**: a four-provider LLM-judge panel (with the same-provider association separated from general judge severity), a clinician-anchored validity check (two independent clinicians co-primary, plus the author), and a perturbation-validity audit. Two evaluator-facing findings: **judge choice materially changes apparent safety**, and **LLM judges are more permissive than the stricter clinician**. The closed-ended MedQA/MedMCQA results (with paired/equivalence statistics) anchor that accuracy is high and the safety gap is about calibration, not knowledge.

## Quick Links

- [**Preprint on arXiv (2607.18828)**](https://arxiv.org/abs/2607.18828)
- [Manuscript (Markdown)](PAPER.md)
- [Headline results table (MedQA n=100 + HealthBench)](runs/final/final_study.md)
- [Larger-n MedQA (n=300)](runs/final_supplementary/medqa_n300.md)
- [Second benchmark — MedMCQA (n=200)](runs/final_supplementary/medmcqa_n200.md)
- [Cross-provider judge-panel summary](runs/judge_panel/panel_summary.md)
- [Human validity — 3 clinicians](runs/human_eval/human_validity_multi.md)
- [Raw per-item completion dumps (v1.0.0 release)](https://github.com/KAVentures/health-ai-readiness-robustness/releases/tag/v1.0.0)
- [Gu et al., *Nature Medicine* 2026 (preprint arXiv:2509.18234)](https://arxiv.org/abs/2509.18234)

## Study Question

Readiness stress-testing of medical AI has concentrated on closed-ended and multimodal benchmarks. This study extends it to **open-ended clinical conversation under missing information** and treats the *evaluator* as part of the measurement:

> When key clinical information is removed from an open-ended medical conversation, do frontier models recognize the gap and qualify, clarify, or otherwise avoid over-committing — or do they answer confidently as if nothing were missing? And because that behavior is scored by an LLM judge, does the *choice and calibration* of that judge change the safety conclusion? The closed-ended MedQA/MedMCQA battery is an anchor showing the gap is about calibration, not knowledge.

## Model Panel

All models evaluated at **high reasoning effort**.

| Model | Provider route | Configured identifier | Reasoning setting |
|---|---|---|---|
| GPT-5.5 | OpenAI Responses API | `gpt-5.5` | high |
| Claude Opus 4.8 | Anthropic Messages API | `claude-opus-4-8` | high / adaptive thinking (16k budget) |
| Grok 4.3 | xAI OpenAI-compatible API | `grok-4.3` | high |
| Gemini 3.5 Flash | Google Gemini (OpenAI-compatible) | `gemini-3.5-flash` | high |

An exploratory Gemini 3.1 Pro run was quota-limited and is retained only as archived exploratory output (in the raw-completions release); it is not part of the primary model panel. Gemini is represented at Flash tier, not a Pro flagship, due to API quota.

## Benchmarks and Perturbations

| Benchmark | n per cell | Task type | Perturbations applied |
|---|---:|---|---|
| MedQA-USMLE | 100 (headline), 300 (supplementary) | 4-option MCQ | option shuffle · correct-answer removal · context removal |
| MedMCQA | 200 (supplementary) | 4-option MCQ | option shuffle · correct-answer removal · context removal |
| HealthBench | 50 | open-ended clinical dialogue | final-user-turn deletion (missing-information probe) |

Removal conditions insert an explicit abstention target ("none of the other answers is correct" / "there is not enough information to answer"); the metric is the **inappropriate-confident rate** = 1 − appropriate-abstention rate.

## Main Results

### MCQ robustness — MedQA (n = 300, Wilson 95% CIs)

| Model | acc (clean) | acc (shuffled) | Δacc | inappropriate-confident (answer removed) | inappropriate-confident (context removed) |
|---|---:|---:|---:|---:|---:|
| Claude Opus 4.8 | 0.953 | 0.953 | +0.000 | 0.157 | 0.223 |
| GPT-5.5 | 0.960 | 0.967 | −0.007 | 0.143 | 0.177 |
| Grok 4.3 | 0.920 | 0.923 | −0.003 | 0.093 | 0.087 |
| Gemini 3.5 Flash | 0.953 | 0.950 | +0.003 | 0.077 | 0.127 |

Accuracy is near-ceiling; option shuffling is **equivalent within a ±5-point region** (post hoc paired-bootstrap check, 90% CI) for three of four models (GPT-5.5 is the exception — shuffling *helped* it by ~4pp). Yet every model still answers confidently on a meaningful fraction of items where the needed information was removed.

### Open-ended missing-information probe — HealthBench (n = 50)

Appropriate-response rate (higher = safer); single as-run judge (GPT-5.5) for the probe.

| Model | baseline rubric | appropriate response | inappropriate confident |
|---|---:|---:|---:|
| Claude Opus 4.8 | 0.913 | 0.940 | 0.060 |
| GPT-5.5 | 0.983 | 0.860 | 0.140 |
| Grok 4.3 | 0.927 | 0.840 | 0.160 |
| Gemini 3.5 Flash | 0.973 | 0.720 | 0.280 |

Under a **same-provider-excluded sensitivity analysis** (leave-one-provider-out), GPT-5.5's inappropriate-confident rate roughly doubles (0.14 → 0.30), moving it from second-best to near-worst; Opus stays lowest (≈0.08). This is an evaluator-dependence result, not a common-scale correction.

### Judge trustworthiness and human validity

- **Judge-panel reliability:** four-provider panel Fleiss' κ = **0.649** (198 complete items); judge choice shifts a score by up to ~0.20.
- **Same-provider association (severity-adjusted):** the raw own-minus-peer gap for GPT-5.5 is +0.16, but that conflates the GPT-5.5 judge's *general* leniency with any preference for its own provider. After separating the two (a vote-level logistic regression with subject-model and judge fixed effects), a positive same-provider association remains — GPT-5.5 ≈ **+0.10** on the probability scale; shared same-provider effect exact permutation **p = 0.04** (over all 24 bijections) — smaller than the raw gap and, for GPT-5.5 alone, not individually significant at n=50. With one subject and one judge per provider, provider identity cannot be separated from exact-model/style familiarity.
- **Human validity:** a three-rater panel — **two independent clinicians** (co-primary; no ties to the providers or to Kinvectum) plus the **author (a physician)** — labeled the blinded 50-item subsample; inter-rater Fleiss' κ = **0.64** (prompt-clustered CI [0.47, 0.79]). Against the stricter independent clinician (0.52), **all four LLM judges are significantly more lenient** (judges 0.66–0.84; paired CIs exclude zero); three of four are also significantly more lenient than the consensus (0.54), while Grok's difference is directionally positive but its CI crosses zero; against the more lenient clinician (0.70) only GPT-5.5 clearly separates. LLM-judged safety rates here are therefore **more permissive than the clinician reference**, not a universal upper bound. The author's participation is a disclosed conflict of interest and the consensus is author-influenced (author ↔ clinician O agree 47/50); the leniency direction holds on the two independent clinicians alone. See *Competing Interests* and §3.4.

![MCQ failure-to-abstain with Wilson 95% confidence intervals (MedQA, n=100)](runs/final/forest_mcq_abstention.png)

## Key Conclusions

- **Accuracy ≠ readiness.** Near-ceiling MCQ accuracy (option-shuffle equivalent within ±5pp for three of four models) coexists with imperfect handling of missing information: models over-commit when the information needed to answer safely is absent (MedQA inappropriate-confident 0.08–0.22; HealthBench 0.06–0.28).
- **Judge choice changes apparent safety.** Inter-judge reliability is only moderate (Fleiss' κ = 0.65), and a positive same-provider association survives adjustment for general judge severity (GPT-5.5 ≈ +0.10; shared-effect exact permutation p = 0.04) — large enough that the apparent open-ended ordering changes when a model's own-provider judge is excluded.
- **LLM judges are more permissive than clinicians.** All four judges over-credit appropriate uncertainty relative to the stricter clinician (judges 0.66–0.84 vs 0.52); three of four also relative to the consensus (0.54); against the most lenient clinician (0.70) the effect is weaker. The direction holds on the two independent clinicians' labels alone and on the author-audited clinical-underdetermined items.
- **More judges is not more valid (exploratory).** In this 50-item sample a tie-positive rule (≥2/4, 2-2 ties scored appropriate) aligned with the stricter clinician no better than the worst single judge (κ ≈ 0.30 point estimate); a conservative rule (unanimity, or the single judge Grok) had the highest point estimates (κ ≈ 0.55) — though the κ CIs overlap heavily, so this is indicative, not established. Even 4/4 unanimous LLM agreement left the stricter clinician disagreeing on ~1 in 4 items. Judge disagreement also concentrates in ill-posed perturbations (unanimity 0.88 on audited clinical-underdetermined items vs 0.56 on administrative).
- **Perturbations are not portable across benchmarks.** MedMCQA context-removal inappropriate rates jump to 0.86–0.92 — a benchmark artifact (items answerable from the stem alone); a perturbation-validity audit shows the open-ended signal concentrates in genuinely underdetermined clinical items.
- **No single model dominates.** On MCQ, most pairwise differences fall within overlapping intervals. On open-ended over-commitment, after excluding own-provider judges, Opus 4.8 has the lowest point estimate and Gemini 3.5 Flash the highest — an upper-bound ordering on n=50 with a tier confound (Gemini is Flash-tier).

## Limitations

- **Statistical power.** Headline cells are n = 100 (MCQ) / n = 50 (HealthBench); a supplementary n = 300 MedQA run tightens intervals to ≈ ±0.03–0.05 but the three flagship models remain non-separable. Most pairwise model differences are not statistically distinguishable.
- **LLM-judge dependence (open-ended).** The open-ended metric is judge-defined; validated against a three-rater human panel (κ = 0.64) on only 50 items in one batch, so κ estimates carry wide uncertainty. One rater is the author (a disclosed conflict of interest) and the majority consensus is author-influenced; the leniency direction is confirmed on the two independent clinicians alone. A larger, fully external clinician panel is the primary follow-up.
- **Mixed judges.** The HealthBench baseline was judged by GPT-4.1-mini and the probe by GPT-5.5 (provider moderation forced this); the two columns are not a matched pair.
- **Model substitution.** Gemini is Flash tier, not a Pro flagship, due to quota.
- **Single rollout (bounded).** Headline cells score each item once; five-fold resampling bounds within-model variance at SD 0.008–0.023.
- **Cued abstention.** The MCQ setting explicitly offered an abstention option, so these are optimistic estimates relative to naturalistic deployment.

## Repository Contents

| Path | Contents |
|---|---|
| `PAPER.md` | Full manuscript (abstract, methods, results, discussion, limitations, appendices, references) |
| `environments/medrobust/` | MCQ perturbation environment (shuffle / answer-removal / context-removal) |
| `environments/healthbench_robust/` | Open-ended missing-information probe (final-user-turn deletion) |
| `scripts/` | Study orchestration, cross-provider judging, human-eval scoring, cost estimation, and figure generation |
| `configs/study-endpoints.toml` | Endpoint registry (env-var names only; no secrets) |
| `patches/judge_helpers.patch` | Small patch to upstream medmarks (sampling defaults for the newer model names) |
| `runs/final/`, `runs/final_supplementary/` | Curated result tables, CSVs, and figures |
| `runs/judge_panel/` | Four-provider judge votes and panel summary |
| `runs/human_eval/` | Blinded annotation sheet, packets, de-identified clinician labels, and validity reports |
| `runs/rollout_var/`, `runs/rerun/`, `runs/study*/` | Rollout-variance and supplementary/rerun outputs |

## Reproducing the Study

This repo is the **study layer**, overlaid on the medmarks harness at the pinned base commit.

```bash
# 1. Clone the harness at the pinned base commit
git clone https://github.com/MedARC-AI/medmarks.git
cd medmarks
git checkout 154710b            # medarc_verifiers 0.14.0 (upstream PR #131)

# 2. Apply the one upstream change this study needs
git apply /path/to/this-repo/patches/judge_helpers.patch

# 3. Overlay the study environments, scripts, and configs
cp -r /path/to/this-repo/environments/medrobust environments/
cp -r /path/to/this-repo/environments/healthbench_robust environments/
cp /path/to/this-repo/scripts/*.py /path/to/this-repo/scripts/*.sh scripts/
cp /path/to/this-repo/configs/study-endpoints.toml configs/

# 4. Set up the environment (per medmarks' own instructions)
uv venv --python 3.12 && source .venv/bin/activate
uv pip install -e .
vf-install medrobust && vf-install healthbench_robust

# 5. Provide API keys via environment (never commit these)
cp .env.example .env   # then edit: OPENAI_API_KEY, ANTHROPIC_API_KEY, XAI_API_KEY, GOOGLE_API_KEY

# 6. Run the study, judging, scoring, and figures
python scripts/run_robustness_study.py
python scripts/panel_rejudge.py
python scripts/score_human_eval_multi.py
python scripts/plot_robustness_study.py
```

See the docstring at the top of each script for its exact arguments and outputs. Analysis tables and figures in `runs/` can be regenerated from saved outputs without rerunning paid inference. Runtime credentials and `.env` files are intentionally excluded.

## Raw Completions

**Raw per-item completion dumps** (full model inputs/outputs for every eval cell) are attached to the [v1.0.0 release](https://github.com/KAVentures/health-ai-readiness-robustness/releases/tag/v1.0.0) as `raw_completions.tar.gz` (9.5 MB compressed, ~70 MB uncompressed; 202 JSON + 202 JSONL, logs and secrets excluded). Download and `tar xzf raw_completions.tar.gz` inside a medmarks checkout for bit-level reproducibility.

## Data and Human Labels

- Benchmark items are from public research datasets (MedQA, MedMCQA, HealthBench) — no real patient data.
- Human labels (`runs/human_eval/`) come from a three-rater panel who each independently labeled the same blinded 50 items: `R1` = the **author** (a physician), and `O`, `G` = **two independent clinicians** with no ties to the evaluated providers or to Kinvectum. Raters are de-identified by initial. The author's participation is a disclosed conflict of interest and the majority consensus is author-influenced (`R1`↔`O` agree 47/50); the paper's leniency conclusion is shown to hold on `O` and `G` alone. See `runs/human_eval/PROVENANCE.md`, the paper's *Competing Interests* section, and §3.4. Ethics: the project was assessed by the research principal as falling outside mandatory review under the Swedish Ethical Review Act (2003:460); see [`manuscript/ethics_self_assessment.md`](manuscript/ethics_self_assessment.md).

## Attribution

This work builds on the methodology and research question of:

- Gu, Y., Fu, J., Liu, X., Valanarasu, J.M.J., Codella, N.C.F., Tan, R., Liu, Q., Jin, Y., Zhang, S., et al. **Evaluating the robustness and readiness of large frontier models in health AI applications.** *Nature Medicine*, 2026. doi:10.1038/s41591-026-04501-8 (preprint: *The Illusion of Readiness in Health AI*, arXiv:2509.18234).

and the evaluation harness:

- **[MedARC-AI/medmarks](https://github.com/MedARC-AI/medmarks)** (`medarc_verifiers`), itself built on the **[verifiers](https://github.com/willccbb/verifiers)** framework. The `medarc_verifiers` package is **not** redistributed here; only a small patch (`patches/`) is included.

Benchmark sources: MedQA (Jin et al., 2021), MedMCQA (Pal et al., 2022), and HealthBench (Arora et al., OpenAI, 2025). Full references are in [`PAPER.md`](PAPER.md#references).

## Citation

If you use this work, please cite the preprint (and, where relevant, the Gu et al. study it builds on).

```bibtex
@article{afrasyab2026missinginfo,
  title         = {Evaluating Medical AI Under Missing Information: Same-Provider Judges and Human Raters Change Apparent Safety},
  author        = {Afrasyab, Koyar},
  year          = {2026},
  eprint        = {2607.18828},
  archivePrefix = {arXiv},
  primaryClass  = {cs.AI},
  url           = {https://arxiv.org/abs/2607.18828}
}
```

## Funding and Competing Interests

This project was funded by Kinvectum AB. Koyar Afrasyab, M.D. is the founder of Kinvectum AB. The funder had no role in study design, analysis, or the decision to publish.

## License

- **Code** (`environments/`, `scripts/`, `configs/`, `patches/`): [MIT](LICENSE).
- **Paper and data** (`PAPER.md`, `runs/`): [CC-BY-4.0](LICENSE-CC-BY-4.0.md).

Subject to the licensing terms of upstream datasets, the medmarks/verifiers harness, and third-party source materials.
