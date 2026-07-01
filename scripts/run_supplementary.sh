#!/usr/bin/env bash
# Supplementary runs: larger-n MedQA, MedMCQA second benchmark, rollout variance.
# Sequential to avoid cross-provider rate-limit collisions. Continues on per-job failure.
set -u
cd "$(dirname "$0")/.."
export PATH="$HOME/.local/bin:$PATH"
source .venv/bin/activate
set -a; . ./.env; set +a

MODELS="opus-4_8-high gpt-5_5-high grok-4_3 gemini-3_5-flash"
LOG=runs/supplementary.log
mkdir -p runs
echo "=== supplementary runs started $(date) ===" | tee "$LOG"

echo ">>> [1/3] Larger-n MedQA (n=300)" | tee -a "$LOG"
python3 scripts/run_robustness_study.py --models $MODELS \
  --datasets medqa --perturbations none shuffle remove_answer remove_context \
  -n 300 --out runs/study_largeN_medqa >>"$LOG" 2>&1 \
  && echo ">>> [1/3] done" | tee -a "$LOG" || echo ">>> [1/3] FAILED" | tee -a "$LOG"

echo ">>> [2/3] MedMCQA second benchmark (n=200)" | tee -a "$LOG"
python3 scripts/run_robustness_study.py --models $MODELS \
  --datasets medmcqa --perturbations none shuffle remove_answer remove_context \
  -n 200 --out runs/study_medmcqa >>"$LOG" 2>&1 \
  && echo ">>> [2/3] done" | tee -a "$LOG" || echo ">>> [2/3] FAILED" | tee -a "$LOG"

echo ">>> [3/3] Rollout variance (k=5, n=50)" | tee -a "$LOG"
python3 scripts/rollout_variance.py --models $MODELS -n 50 -k 5 \
  --out runs/rollout_var >>"$LOG" 2>&1 \
  && echo ">>> [3/3] done" | tee -a "$LOG" || echo ">>> [3/3] FAILED" | tee -a "$LOG"

echo "=== supplementary runs finished $(date) ===" | tee -a "$LOG"
