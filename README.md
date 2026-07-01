# Accuracy is not readiness: a robustness stress-test of frontier models on medical QA

**Author:** Koyar Afrasyab, M.D. — [Kinvectum AB](https://www.kinvectum.com)
**Status:** Preprint + open data/code release.

This repository contains the paper, evaluation code, and data for an open-source
robustness stress-test of four frontier LLMs (Claude Opus 4.8, GPT-5.5, Grok 4.3,
Gemini 3.5 Flash) on medical question answering. It **re-implements and extends** the
input-perturbation methodology of Gu et al., *The Illusion of Readiness in Health AI*
(arXiv:2509.18234, 2025), as a benchmark-agnostic evaluation layer on top of the
[MedARC-AI/medmarks](https://github.com/MedARC-AI/medmarks) harness.

The full write-up is in **[`PAPER.md`](PAPER.md)**.

## What this study does

- **MCQ stress tests (MedQA, MedMCQA):** option shuffling, correct-answer removal
  (with an explicit "none of the above" abstention target), and context removal.
- **Open-ended abstention probe (HealthBench):** truncate the final user turn and
  measure whether the model flags the missing information instead of answering
  confidently.
- **Judge trustworthiness:** a four-provider LLM judge panel (OpenAI, Anthropic, xAI,
  Google) with Fleiss' κ reliability, a self-preference test, and leave-one-provider-out
  scoring.
- **Human validity:** a blinded 50-item subsample labeled independently by **three
  clinicians** (inter-rater Fleiss' κ = 0.64), used to validate the LLM judges.
- **Robustness checks:** larger-n MedQA (n = 300), a second benchmark (MedMCQA,
  n = 200), and five-fold rollout-variance estimation.

### Headline finding
Near-ceiling accuracy coexists with imperfect abstention: models answer confidently
when the information needed to answer safely has been removed. Every LLM judge is
systematically more lenient than the clinician consensus, so LLM-judged safety rates
should be read as **upper bounds**.

## Repository layout

```
PAPER.md                     The paper (Markdown).
environments/
  medrobust/                 MCQ perturbation environment (shuffle / answer- / context-removal).
  healthbench_robust/        Open-ended context-removal abstention probe.
scripts/                     Study orchestration, judging, scoring, and figures.
configs/
  study-endpoints.toml       Endpoint registry used for the runs (no secrets; keys via env).
patches/
  judge_helpers.patch        Small patch to upstream medmarks (adds sampling defaults
                             for the newer model names used here).
runs/                        Curated results, judge votes, human labels, and figures
                             referenced by the paper.
```

`runs/` includes the processed evaluation outputs, the four-provider judge votes
(`runs/judge_panel/`), the blinded human annotation packets and labels
(`runs/human_eval/`), and all figures.

**Raw per-item completion dumps** (full model inputs/outputs for every eval cell) are
kept out of the main tree for size and attached to the
[v1.0.0 release](https://github.com/KAVentures/health-ai-readiness-robustness/releases/tag/v1.0.0)
as `raw_completions.tar.gz` (9.5 MB compressed, ~70 MB uncompressed). Download and
`tar xzf raw_completions.tar.gz` inside a medmarks checkout for bit-level
reproducibility, or regenerate them with the scripts below.

## Reproducing the study

This repo is the **study layer**, not a full harness fork. To run it you overlay it on
the medmarks harness at the exact base commit used here.

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
cp .env.example .env   # then edit: OPENAI_API_KEY, ANTHROPIC_API_KEY, XAI_API_KEY, GOOGLE_API_KEY, ...

# 6. Run the study, judging, scoring, and figures
python scripts/run_robustness_study.py
python scripts/panel_rejudge.py
python scripts/score_human_eval_multi.py
python scripts/plot_robustness_study.py
```

See the docstring at the top of each script for its exact arguments and outputs.

## Data and human labels

- Benchmark items are from public research datasets (MedQA, MedMCQA, HealthBench) — no
  real patient data.
- The human labels (`runs/human_eval/`) come from three clinicians who each labeled the
  same blinded 50 items independently; annotators are de-identified (`R1`, `O`, `G`).

## Attribution and acknowledgements

This work stands on several open contributions:

- **Gu et al., *The Illusion of Readiness in Health AI*** (arXiv:2509.18234, 2025) — the
  source of the input-perturbation / stress-test methodology this study re-implements
  and extends.
- **[MedARC-AI/medmarks](https://github.com/MedARC-AI/medmarks)** — the medical-eval
  harness (`medarc_verifiers`) this study is built on, itself built on the
  **[verifiers](https://github.com/willccbb/verifiers)** framework. The `medarc_verifiers`
  package is **not** redistributed here; only a small patch (`patches/`) is included.
- **Benchmarks:** MedQA (Jin et al., 2021), MedMCQA (Pal et al., 2022), and
  **HealthBench** (Arora et al., OpenAI, 2025).
- **Model providers:** Anthropic, OpenAI, xAI, and Google, whose frontier models are
  evaluated here.

Full references are in [`PAPER.md`](PAPER.md#references).

## Funding
Funded by [Kinvectum AB](https://www.kinvectum.com). The funder had no role in study
design, analysis, or the decision to publish.

## License

- **Code** (`environments/`, `scripts/`, `configs/`, `patches/`): [MIT](LICENSE).
- **Paper and data** (`PAPER.md`, `runs/`): [CC-BY-4.0](LICENSE-CC-BY-4.0.md) — reuse is
  welcome with attribution.

## Citation

If you use this work, please cite it (see [`CITATION.cff`](CITATION.cff)):

> Afrasyab, K. *Accuracy is not readiness: a robustness stress-test of frontier models
> on medical question answering.* Kinvectum AB, 2026.

and the original methodology:

> Gu, Y., et al. *The Illusion of Readiness in Health AI.* arXiv:2509.18234, 2025.
