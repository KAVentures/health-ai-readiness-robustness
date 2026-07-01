# Accuracy Is Not Readiness: A Robustness Stress-Test of Frontier Models on Medical QA

**A benchmark-agnostic re-implementation and text-modality extension of the Health-AI input-perturbation methodology, applied to four current frontier reasoning models.**

Author: **Koyar Afrasyab, M.D.**
Affiliation: **Kinvectum AB**
Funding: **Kinvectum AB**

This repository contains the manuscript, evaluation environments, orchestration/judging/scoring code, saved analysis tables, figures, judge-panel votes, and human-annotation data for a robustness study of frontier LLMs on medical question answering. It **re-implements and extends** the input-perturbation methodology of Gu et al., *The Illusion of Readiness in Health AI* (arXiv:2509.18234, 2025), as an open-source evaluation layer on top of the [MedARC-AI/medmarks](https://github.com/MedARC-AI/medmarks) harness.

This is a **methodology re-implementation and model update on text-modality benchmarks**, not a full reproduction of the original multimodal study: it re-uses the original's perturbation logic (option shuffling, answer removal, context removal) and adds an open-ended abstention probe, a four-provider LLM judge panel, and a three-clinician human-validity check, while deliberately excluding the original study's image-based components.

## Quick Links

- [Manuscript (Markdown)](PAPER.md)
- [Headline results table (MedQA n=100 + HealthBench)](runs/final/final_study.md)
- [Larger-n MedQA (n=300)](runs/final_supplementary/medqa_n300.md)
- [Second benchmark — MedMCQA (n=200)](runs/final_supplementary/medmcqa_n200.md)
- [Cross-provider judge-panel summary](runs/judge_panel/panel_summary.md)
- [Human validity — 3 clinicians](runs/human_eval/human_validity_multi.md)
- [Raw per-item completion dumps (v1.0.0 release)](https://github.com/KAVentures/health-ai-readiness-robustness/releases/tag/v1.0.0)
- [Original Gu et al. paper (arXiv:2509.18234)](https://arxiv.org/abs/2509.18234)

## Study Question

The original Health-AI-Readiness study asked whether strong frontier-model performance on medical benchmarks translates into robust, deployment-ready behavior. This study asks a focused, text-modality version:

> When the information needed to answer a medical question is degraded or removed, do frontier models recognize the gap and abstain — or do they answer confidently as if nothing were missing? And can automated (LLM-judge) scoring of that behavior be trusted against clinicians?

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
| HealthBench | 50 | open-ended clinical dialogue | final-user-turn context truncation (abstention probe) |

Removal conditions insert an explicit abstention target ("none of the other answers is correct" / "there is not enough information to answer"); the metric is the **inappropriate-confident rate** = 1 − appropriate-abstention rate.

## Main Results

### MCQ robustness — MedQA (n = 300, Wilson 95% CIs)

| Model | acc (clean) | acc (shuffled) | Δacc | inappropriate-confident (answer removed) | inappropriate-confident (context removed) |
|---|---:|---:|---:|---:|---:|
| Claude Opus 4.8 | 0.953 | 0.953 | +0.000 | 0.157 | 0.223 |
| GPT-5.5 | 0.960 | 0.967 | −0.007 | 0.143 | 0.177 |
| Grok 4.3 | 0.920 | 0.923 | −0.003 | 0.093 | 0.087 |
| Gemini 3.5 Flash | 0.953 | 0.950 | +0.003 | 0.077 | 0.127 |

Accuracy is near-ceiling and **positionally robust** (|Δacc| ≤ 0.007 for all models), yet every model still answers confidently on a meaningful fraction of items where the needed information was removed.

### Open-ended abstention — HealthBench (n = 50)

Appropriate-uncertainty rate (higher = safer); single canonical judge (GPT-5.5) for the probe.

| Model | baseline rubric | appropriate uncertainty | inappropriate confident |
|---|---:|---:|---:|
| Claude Opus 4.8 | 0.913 | 0.940 | 0.060 |
| GPT-5.5 | 0.983 | 0.860 | 0.140 |
| Grok 4.3 | 0.927 | 0.840 | 0.160 |
| Gemini 3.5 Flash | 0.973 | 0.720 | 0.280 |

After **self-preference correction** (leave-one-provider-out), GPT-5.5's inappropriate-confident rate roughly doubles (0.14 → 0.30), moving it from second-best to near-worst; Opus remains best (≈0.08).

### Judge trustworthiness and human validity

- **Judge-panel reliability:** four-provider panel Fleiss' κ = **0.649** (198 complete items); judge choice shifts a score by up to ~0.20.
- **Self-preference:** GPT-5.5 credits its own provider **+0.16** vs peers (largest of the four).
- **Human validity:** three independent clinicians labeled the blinded 50-item subsample; inter-rater Fleiss' κ = **0.64**. All LLM judges are systematically more lenient than the clinician consensus (consensus appropriate-uncertainty **0.54** vs judges **0.66–0.84**), and judge-vs-consensus agreement is only fair-to-moderate (Cohen's κ **0.20–0.43**). LLM-judged safety rates should therefore be read as **upper bounds**.

![MCQ failure-to-abstain with Wilson 95% confidence intervals (MedQA, n=100)](runs/final/forest_mcq_abstention.png)

## Key Conclusions

- **Accuracy ≠ readiness.** Near-ceiling, positionally robust MCQ accuracy coexists with imperfect abstention: models over-commit when the information needed to answer safely is absent (MedQA inappropriate-confident 0.08–0.22; HealthBench 0.06–0.28).
- **LLM judges are systematically lenient.** Against three clinicians (who agree at κ = 0.64), every judge over-credits appropriate uncertainty; the over-confidence problem is *worse* than any LLM judge reports.
- **Self-preference is a first-order confound.** GPT-5.5 favors its own provider by +0.16; correcting for it reverses the open-ended ranking.
- **Perturbations are not portable across benchmarks.** MedMCQA context-removal inappropriate rates jump to 0.86–0.92 — a benchmark artifact (items are answerable from the stem alone), a caution that automated context removal is only meaningful on vignette-style items.
- **No single model dominates.** On MCQ, most pairwise differences fall within overlapping confidence intervals; the robust signal is the qualitative accuracy-vs-abstention dissociation. On open-ended calibrated abstention, Opus 4.8 is best and Gemini 3.5 Flash worst.

## Limitations

- **Statistical power.** Headline cells are n = 100 (MCQ) / n = 50 (HealthBench); a supplementary n = 300 MedQA run tightens intervals to ≈ ±0.03–0.05 but the three flagship models remain non-separable. Most pairwise model differences are not statistically distinguishable.
- **LLM-judge dependence (open-ended).** The open-ended metric is judge-defined; validated against three clinicians (human-human κ = 0.64), but on only 50 items, so κ estimates carry wide uncertainty.
- **Mixed judges.** The HealthBench baseline was judged by GPT-4.1-mini and the probe by GPT-5.5 (provider moderation forced this); the two columns are not a matched pair.
- **Model substitution.** Gemini is Flash tier, not a Pro flagship, due to quota.
- **Single rollout (bounded).** Headline cells score each item once; five-fold resampling bounds within-model variance at SD 0.008–0.023.
- **Cued abstention.** The MCQ setting explicitly offered an abstention option, so these are optimistic estimates relative to naturalistic deployment.

## Repository Contents

| Path | Contents |
|---|---|
| `PAPER.md` | Full manuscript (abstract, methods, results, discussion, limitations, appendices, references) |
| `environments/medrobust/` | MCQ perturbation environment (shuffle / answer-removal / context-removal) |
| `environments/healthbench_robust/` | Open-ended context-removal abstention probe |
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
- Human labels (`runs/human_eval/`) come from three clinicians who each independently labeled the same blinded 50 items; annotators are de-identified (`R1`, `O`, `G`).

## Attribution

This work builds on the methodology and research question of:

- Gu, Y., Fu, J., Liu, X., Valanarasu, J.M.J., Codella, N.C.F., Tan, R., Liu, Q., Jin, Y., Zhang, S., et al. **The Illusion of Readiness in Health AI.** arXiv:2509.18234, 2025.

and the evaluation harness:

- **[MedARC-AI/medmarks](https://github.com/MedARC-AI/medmarks)** (`medarc_verifiers`), itself built on the **[verifiers](https://github.com/willccbb/verifiers)** framework. The `medarc_verifiers` package is **not** redistributed here; only a small patch (`patches/`) is included.

Benchmark sources: MedQA (Jin et al., 2021), MedMCQA (Pal et al., 2022), and HealthBench (Arora et al., OpenAI, 2025). Full references are in [`PAPER.md`](PAPER.md#references).

## Citation

If you use this work, please cite both this repository and the original Gu et al. study it re-implements.

```bibtex
@misc{afrasyab2026accuracynotreadiness,
  title  = {Accuracy Is Not Readiness: A Robustness Stress-Test of Frontier Models on Medical Question Answering},
  author = {Afrasyab, Koyar},
  year   = {2026},
  howpublished = {GitHub repository},
  url    = {https://github.com/KAVentures/health-ai-readiness-robustness}
}
```

## Funding and Competing Interests

This project was funded by Kinvectum AB. Koyar Afrasyab, M.D. is the founder of Kinvectum AB. The funder had no role in study design, analysis, or the decision to publish.

## License

- **Code** (`environments/`, `scripts/`, `configs/`, `patches/`): [MIT](LICENSE).
- **Paper and data** (`PAPER.md`, `runs/`): [CC-BY-4.0](LICENSE-CC-BY-4.0.md).

Subject to the licensing terms of upstream datasets, the medmarks/verifiers harness, and third-party source materials.
