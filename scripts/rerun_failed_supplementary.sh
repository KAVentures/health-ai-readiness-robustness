#!/usr/bin/env bash
# Re-run ONLY the supplementary cells that quota/credit-errored on the 2026-06-30
# run. Grok was fully valid (untouched). Opus needs 1 MedQA cell (rest valid).
# GPT-5.5 + Gemini need their post-exhaustion cells. Run after billing restored.
# Continues on per-job failure; results land in the env outputs/evals dirs and are
# picked up by scripts/consolidate_supplementary.py (newest error-free wins).
set -u
cd "$(dirname "$0")/.."
export PATH="$HOME/.local/bin:$PATH"
source .venv/bin/activate
set -a; . ./.env; set +a

LOG=runs/rerun_failed.log
mkdir -p runs
echo "=== failed-cell re-run started $(date) ===" | tee "$LOG"

run() { echo ">>> $*" | tee -a "$LOG"; python3 scripts/run_robustness_study.py "$@" >>"$LOG" 2>&1 \
        && echo ">>> done" | tee -a "$LOG" || echo ">>> FAILED (continuing)" | tee -a "$LOG"; }

# --- MedQA n=300 failed cells ---
echo "### MedQA n=300" | tee -a "$LOG"
run --models opus-4_8-high            --datasets medqa --perturbations remove_context              -n 300 --out runs/rerun/medqa_opus
run --models gpt-5_5-high gemini-3_5-flash --datasets medqa --perturbations remove_answer remove_context -n 300 --out runs/rerun/medqa_gpt_gemini

# --- MedMCQA n=200 failed cells (GPT-5.5 + Gemini, all 4 conditions) ---
echo "### MedMCQA n=200" | tee -a "$LOG"
run --models gpt-5_5-high gemini-3_5-flash --datasets medmcqa \
    --perturbations none shuffle remove_answer remove_context -n 200 --out runs/rerun/medmcqa_gpt_gemini

# --- Rollout variance k=5 n=50 (GPT-5.5 + Gemini) ---
echo "### Rollout variance (GPT-5.5 + Gemini)" | tee -a "$LOG"
echo ">>> rollout gpt+gemini" | tee -a "$LOG"
python3 scripts/rollout_variance.py --models gpt-5_5-high gemini-3_5-flash \
  --perturbations remove_answer remove_context -n 50 -k 5 --out runs/rerun/rollout_gpt_gemini >>"$LOG" 2>&1 \
  && echo ">>> done" | tee -a "$LOG" || echo ">>> FAILED (continuing)" | tee -a "$LOG"

echo "=== failed-cell re-run finished $(date) ===" | tee -a "$LOG"
