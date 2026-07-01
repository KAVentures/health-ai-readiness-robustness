#!/usr/bin/env python
"""Estimate within-model sampling variance by re-running the same MCQ cell K times.

For each (model, abstention condition) we run a fixed n-item MedQA cell K separate
times (each a fresh single-rollout eval) and record the cell-level
inappropriate-confident rate (1 - mean_reward) for each repetition. The spread
across repetitions (SD, min-max) is the sampling-variance estimate the paper's §5
flagged as missing. Items are held fixed (same first-n), so the only variation is
the models' own stochastic decoding at high reasoning effort.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path

ENDPOINTS = "configs/study-endpoints.toml"
GLOB = "environments/medrobust/outputs/evals/medrobust--*/*"


def _newest(before: set[str]) -> str | None:
    cands = [d for d in glob.glob(GLOB) if d not in before and os.path.isdir(d)]
    return max(cands, key=os.path.getmtime) if cands else None


def _rewards(rdir: str) -> list[float]:
    out = []
    with open(os.path.join(rdir, "results.jsonl")) as fh:
        for line in fh:
            r = json.loads(line).get("reward")
            if r is not None:
                out.append(float(r))
    return out


def run_cell(model: str, pert: str, n: int) -> float | None:
    before = set(glob.glob(GLOB))
    cmd = ["uv", "run", "medarc-eval", "medrobust", "-m", model, "-e", ENDPOINTS,
           "-n", str(n), "-r", "1",
           "--env-args", json.dumps({"dataset": "medqa", "perturbation": pert}), "-s"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(proc.stderr[-1500:], file=sys.stderr)
        return None
    time.sleep(0.2)
    rdir = _newest(before)
    if not rdir:
        return None
    rw = _rewards(rdir)
    return (sum(rw) / len(rw)) if rw else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+",
                    default=["opus-4_8-high", "gpt-5_5-high", "grok-4_3", "gemini-3_5-flash"])
    ap.add_argument("--perturbations", nargs="+", default=["remove_answer", "remove_context"])
    ap.add_argument("-n", type=int, default=50)
    ap.add_argument("-k", "--reps", type=int, default=5)
    ap.add_argument("--out", default="runs/rollout_var")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    results: dict[str, dict[str, dict]] = {}

    for model in args.models:
        results[model] = {}
        for pert in args.perturbations:
            rates = []
            for rep in range(args.reps):
                m = run_cell(model, pert, args.n)
                if m is not None:
                    rates.append(1 - m)  # inappropriate-confident rate
                print(f"  {model} {pert} rep{rep+1}/{args.reps}: "
                      f"inappropriate={1-m:.3f}" if m is not None else f"  {model} {pert} rep{rep+1} FAILED",
                      flush=True)
            if rates:
                results[model][pert] = {
                    "rates": rates, "mean": statistics.mean(rates),
                    "sd": statistics.pstdev(rates) if len(rates) > 1 else 0.0,
                    "min": min(rates), "max": max(rates), "k": len(rates), "n": args.n,
                }
            (out / "rollout_variance.json").write_text(json.dumps(results, indent=2))

    # Markdown
    lines = ["# Within-model sampling variance (MedQA abstention cells)\n",
             f"Each cell re-run {args.reps}x at n={args.n}, single rollout each, fixed items. "
             "Rate = inappropriate-confident (1 - appropriate-abstention).\n",
             "| model | condition | mean | SD | min | max | range |",
             "|---|---|---|---|---|---|---|"]
    for model, perts in results.items():
        for pert, d in perts.items():
            lines.append(f"| {model} | {pert} | {d['mean']:.3f} | {d['sd']:.3f} | "
                         f"{d['min']:.3f} | {d['max']:.3f} | {d['max']-d['min']:.3f} |")
    (out / "rollout_variance.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
