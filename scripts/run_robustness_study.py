#!/usr/bin/env python
"""Orchestrate the medrobust robustness study and aggregate the paper's metrics.

Runs a (model x dataset x perturbation) matrix through `medarc-eval medrobust`
and, optionally, the open-ended HealthBench baseline + context-removal probe
through `medarc-eval healthbench` / `medarc-eval healthbench_robust`. Collects
per-rollout rewards and emits a per-cell summary plus the headline robustness
metrics from Gu et al., "The Illusion of Readiness in Health AI" (arXiv:2509.18234):

  - Delta-accuracy under option shuffle  = acc(none) - acc(shuffle)
  - Inappropriate-confident-answer rate  = 1 - reward under remove_answer /
                                            remove_context (failure to abstain)
  - HealthBench appropriate-uncertainty  = probe reward; 1 - reward is the
    open-ended inappropriate-confident-answer rate.

Usage:
  python scripts/run_robustness_study.py \
      --models opus-4_8-high gpt-5_5-high grok-4_3 gemini-3_1-pro-high \
      --datasets medqa \
      --perturbations none shuffle remove_answer remove_context \
      -n 100 --healthbench --hb-n 50 --out runs/study
"""

from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ENDPOINTS = "configs/study-endpoints.toml"

MEDROBUST_GLOB = "environments/medrobust/outputs/evals/medrobust--*/*"
HB_GLOB = "environments/healthbench/outputs/evals/healthbench--*/*"
HB_ROBUST_GLOB = "environments/healthbench_robust/outputs/evals/healthbench_robust--*/*"

ABSTAIN_PERTURBATIONS = {"remove_answer", "remove_context"}


def _newest_results_dir(glob_pattern: str, before: set[str]) -> str | None:
    candidates = [d for d in glob.glob(glob_pattern) if d not in before and os.path.isdir(d)]
    if not candidates:
        return None
    return max(candidates, key=os.path.getmtime)


def _read_rewards(results_dir: str) -> list[float]:
    path = os.path.join(results_dir, "results.jsonl")
    rewards: list[float] = []
    with open(path) as fh:
        for line in fh:
            row = json.loads(line)
            r = row.get("reward")
            if r is not None:
                rewards.append(float(r))
    return rewards


def run_eval(env: str, model: str, env_args: dict, glob_pattern: str, n: int, label: str) -> list[float]:
    before = set(glob.glob(glob_pattern))
    cmd = [
        "uv", "run", "medarc-eval", env,
        "-m", model, "-e", ENDPOINTS,
        "-n", str(n), "-r", "1",
        "--env-args", json.dumps(env_args),
        "-s",
    ]
    print(f"  -> {label}: {model} | {env} {env_args} (n={n})", flush=True)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(proc.stdout[-2000:], file=sys.stderr)
        print(proc.stderr[-2000:], file=sys.stderr)
        raise RuntimeError(f"cell failed: {label} {model}/{env}/{env_args}")
    time.sleep(0.2)
    rdir = _newest_results_dir(glob_pattern, before)
    if rdir is None:
        raise RuntimeError(f"no results dir for {label} {model}/{env}/{env_args}")
    return _read_rewards(rdir)


def _mean(rewards: list[float]) -> float:
    return sum(rewards) / len(rewards) if rewards else float("nan")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", required=True)
    ap.add_argument("--datasets", nargs="+", default=["medqa"])
    ap.add_argument(
        "--perturbations", nargs="+",
        default=["none", "shuffle", "remove_answer", "remove_context"],
    )
    ap.add_argument("-n", "--num-examples", type=int, default=100)
    ap.add_argument("--shuffle-seed", type=int, default=1618)
    ap.add_argument("--healthbench", action="store_true", help="also run HealthBench baseline + probe")
    ap.add_argument("--skip-medqa", action="store_true",
                    help="skip the MCQ matrix; only (re)run HealthBench. Leaves MCQ summaries untouched.")
    ap.add_argument("--hb-n", type=int, default=50)
    ap.add_argument("--hb-difficulty", default="consensus")
    ap.add_argument("--judge-model", default="gpt-4.1-mini", help="judge for the context-removal probe")
    ap.add_argument("--baseline-judge-model", default=None,
                    help="judge for the HealthBench baseline (defaults to --judge-model). "
                         "Note: gpt-5.x reasoning judges get moderation-blocked on the baseline rubric, "
                         "so gpt-4.1-mini is recommended here.")
    ap.add_argument("--out", default="runs/study")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    # ---- MedQA/MedMCQA perturbation matrix ----
    cells: dict[tuple[str, str, str], dict] = {}
    if not args.skip_medqa:
        for dataset in args.datasets:
            for model in args.models:
                for pert in args.perturbations:
                    env_args = {"dataset": dataset, "perturbation": pert}
                    if pert == "shuffle":
                        env_args["shuffle_seed"] = args.shuffle_seed
                    rewards = run_eval("medrobust", model, env_args, MEDROBUST_GLOB,
                                       args.num_examples, f"{dataset}/{pert}")
                    mean = _mean(rewards)
                    cells[(dataset, model, pert)] = {"mean": mean, "n": len(rewards)}
                    print(f"     mean_reward={mean:.3f}  n={len(rewards)}", flush=True)

    # ---- HealthBench baseline + context-removal probe ----
    hb_cells: dict[tuple[str, str], dict] = {}
    baseline_judge = args.baseline_judge_model or args.judge_model
    if args.healthbench:
        for model in args.models:
            base_args = {"difficulty": args.hb_difficulty, "judge_model": baseline_judge}
            rewards = run_eval("healthbench", model, base_args, HB_GLOB, args.hb_n, "hb/baseline")
            hb_cells[(model, "baseline")] = {"mean": _mean(rewards), "n": len(rewards)}
            print(f"     mean_reward={hb_cells[(model, 'baseline')]['mean']:.3f}", flush=True)

            probe_args = {"difficulty": args.hb_difficulty, "judge_model": args.judge_model}
            rewards = run_eval("healthbench_robust", model, probe_args, HB_ROBUST_GLOB, args.hb_n, "hb/probe")
            hb_cells[(model, "probe")] = {"mean": _mean(rewards), "n": len(rewards)}
            print(f"     mean_reward={hb_cells[(model, 'probe')]['mean']:.3f}", flush=True)

    # ---- Per-cell CSV ----
    if args.skip_medqa:
        cell_csv = out / "healthbench_cells.csv"
        with open(cell_csv, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["family", "dataset", "model", "condition", "mean_reward", "n"])
            for (m, cond), v in hb_cells.items():
                w.writerow(["healthbench", args.hb_difficulty, m, cond, f"{v['mean']:.4f}", v["n"]])
    else:
        cell_csv = out / "cells.csv"
        with open(cell_csv, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["family", "dataset", "model", "condition", "mean_reward", "n"])
            for (ds, m, p), v in cells.items():
                w.writerow(["medqa", ds, m, p, f"{v['mean']:.4f}", v["n"]])
            for (m, cond), v in hb_cells.items():
                w.writerow(["healthbench", args.hb_difficulty, m, cond, f"{v['mean']:.4f}", v["n"]])

    # ---- MCQ robustness summary ----
    summary_rows = []
    for dataset in args.datasets:
        for model in args.models:
            base = cells.get((dataset, model, "none"), {}).get("mean")
            shuf = cells.get((dataset, model, "shuffle"), {}).get("mean")
            ra = cells.get((dataset, model, "remove_answer"), {}).get("mean")
            rc = cells.get((dataset, model, "remove_context"), {}).get("mean")
            summary_rows.append({
                "dataset": dataset,
                "model": model,
                "acc_baseline": base,
                "acc_shuffle": shuf,
                "delta_acc_shuffle": (base - shuf) if (base is not None and shuf is not None) else None,
                "abstain_rate_remove_answer": ra,
                "inappropriate_rate_remove_answer": (1 - ra) if ra is not None else None,
                "abstain_rate_remove_context": rc,
                "inappropriate_rate_remove_context": (1 - rc) if rc is not None else None,
            })

    if not args.skip_medqa:
        summary_csv = out / "robustness_summary.csv"
        fields = list(summary_rows[0].keys()) if summary_rows else []
        with open(summary_csv, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            for r in summary_rows:
                w.writerow({k: ("" if v is None else (f"{v:.4f}" if isinstance(v, float) else v)) for k, v in r.items()})

    # ---- HealthBench summary ----
    hb_rows = []
    if args.healthbench:
        for model in args.models:
            baseline = hb_cells.get((model, "baseline"), {}).get("mean")
            probe = hb_cells.get((model, "probe"), {}).get("mean")
            hb_rows.append({
                "model": model,
                "hb_baseline_score": baseline,
                "hb_probe_appropriate_uncertainty": probe,
                "hb_inappropriate_confident_rate": (1 - probe) if probe is not None else None,
            })
        hb_csv = out / "healthbench_summary.csv"
        with open(hb_csv, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(hb_rows[0].keys()))
            w.writeheader()
            for r in hb_rows:
                w.writerow({k: ("" if v is None else (f"{v:.4f}" if isinstance(v, float) else v)) for k, v in r.items()})

    # ---- Markdown report ----
    def f(x):
        return "—" if x is None else f"{x:.3f}"

    def write_hb_section(fh):
        fh.write("\n## HealthBench open-ended robustness\n\n")
        fh.write(f"Baseline judge: {baseline_judge}. Probe judge: {args.judge_model}. "
                 "Baseline = standard HealthBench rubric score. "
                 "Probe = appropriate-uncertainty rate after context removal; `inappr` = 1 - probe.\n\n")
        fh.write("| model | hb_baseline | appropriate_uncertainty | inappropriate_confident |\n")
        fh.write("|---|---|---|---|\n")
        for r in hb_rows:
            fh.write(
                f"| {r['model']} | {f(r['hb_baseline_score'])} | "
                f"{f(r['hb_probe_appropriate_uncertainty'])} | "
                f"{f(r['hb_inappropriate_confident_rate'])} |\n"
            )

    if args.skip_medqa:
        md = out / "healthbench_summary.md"
        with open(md, "w") as fh:
            fh.write("# HealthBench open-ended robustness\n\n")
            fh.write(f"- difficulty={args.hb_difficulty}, n={args.hb_n}, judge={args.judge_model}\n")
            fh.write(f"- models: {', '.join(args.models)}\n")
            write_hb_section(fh)
        print(f"\nWrote:\n  {cell_csv}\n  {out / 'healthbench_summary.csv'}\n  {md}")
        print("\n" + md.read_text())
        return

    md = out / "robustness_summary.md"
    with open(md, "w") as fh:
        fh.write("# Robustness study\n\n")
        fh.write(f"- MedQA n per cell: {args.num_examples}\n")
        fh.write(f"- datasets: {', '.join(args.datasets)}\n")
        fh.write(f"- models: {', '.join(args.models)}\n")
        if args.healthbench:
            fh.write(f"- HealthBench: difficulty={args.hb_difficulty}, n={args.hb_n}, judge={args.judge_model}\n")
        fh.write("\n## MCQ robustness (MedQA/MedMCQA)\n\n")
        fh.write("Reward: accuracy for `none`/`shuffle`; appropriate-abstention rate for "
                 "`remove_answer`/`remove_context`.\n\n")
        fh.write("| dataset | model | acc | acc(shuf) | Δacc(shuf) | abstain(ans) | inappr(ans) | abstain(ctx) | inappr(ctx) |\n")
        fh.write("|---|---|---|---|---|---|---|---|---|\n")
        for r in summary_rows:
            fh.write(
                f"| {r['dataset']} | {r['model']} | {f(r['acc_baseline'])} | {f(r['acc_shuffle'])} | "
                f"{f(r['delta_acc_shuffle'])} | {f(r['abstain_rate_remove_answer'])} | "
                f"{f(r['inappropriate_rate_remove_answer'])} | {f(r['abstain_rate_remove_context'])} | "
                f"{f(r['inappropriate_rate_remove_context'])} |\n"
            )
        if args.healthbench:
            write_hb_section(fh)

    print(f"\nWrote:\n  {cell_csv}\n  {summary_csv}")
    if args.healthbench:
        print(f"  {out / 'healthbench_summary.csv'}")
    print(f"  {md}")
    print("\n" + md.read_text())


if __name__ == "__main__":
    main()
