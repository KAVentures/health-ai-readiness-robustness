#!/usr/bin/env python
"""Build the final 4-model supplementary tables from ONLY error-free runs.

The 2026-06-30 supplementary run was partly quota/credit-blocked; errored items
score reward=0.0 and would masquerade as data. This consolidator scans every
medrobust results dir, discards any cell that contains a single API error, and for
each (model, perturbation, n) keeps the NEWEST fully-clean run. n disambiguates the
studies: n=300 -> larger-n MedQA, n=200 -> MedMCQA. Rollout variance is merged from
the per-study rollout_variance.json files (also clean-only).

Outputs (runs/final_supplementary/):
  medqa_n300.md / .csv      - 4-model MedQA n=300 robustness table
  medmcqa_n200.md / .csv    - 4-model MedMCQA n=200 robustness table
  rollout_variance.md       - merged within-model sampling-variance table
  STATUS.md                 - per-cell validity (valid / still-missing) audit
"""
from __future__ import annotations

import csv
import glob
import json
import math
import os
from pathlib import Path

EVAL_GLOB = "environments/medrobust/outputs/evals/medrobust--*/*"
MODEL_ORDER = ["claude-opus-4-8", "gpt-5.5", "grok-4.3", "gemini-3.5-flash"]
SHORT = {"claude-opus-4-8": "Opus 4.8", "gpt-5.5": "GPT-5.5", "grok-4.3": "Grok 4.3",
         "gemini-3.5-flash": "Gemini 3.5 Flash"}
PERTS = ["none", "shuffle", "remove_answer", "remove_context"]
OUT = Path("runs/final_supplementary")

# rollout JSONs: original (Opus+Grok valid) + per-provider reruns. Later paths win
# on key collision; degenerate quota artifacts (mean==1.0 & sd==0.0) are dropped.
ROLLOUT_JSONS = ["runs/rollout_var/rollout_variance.json",
                 "runs/rerun/rollout_gpt_gemini/rollout_variance.json",
                 "runs/rerun/rollout_gpt/rollout_variance.json",
                 "runs/rerun/rollout_gemini/rollout_variance.json"]


def wilson(k: int, n: int, z: float = 1.96):
    if n == 0:
        return (float("nan"),) * 3
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, c - h, c + h


def scan_cells():
    """Return {(model_short, n, pert): {'mean','n_valid','mtime','n_err'}} for clean dirs."""
    best: dict[tuple, dict] = {}
    for d in glob.glob(EVAL_GLOB):
        f = os.path.join(d, "results.jsonl")
        if not os.path.isdir(d) or not os.path.exists(f):
            continue
        model = d.split("medrobust--")[1].split("/")[0]
        if model not in SHORT:
            continue
        recs = [json.loads(l) for l in open(f)]
        if not recs:
            continue
        n = len(recs)
        if n not in (300, 200):  # only the supplementary MCQ studies
            continue
        pert = (recs[0].get("info") or {}).get("perturbation")
        n_err = sum(1 for r in recs if (r.get("error") or r.get("stop_condition") == "has_error"))
        if n_err > 0:  # never use a cell with any API error
            continue
        rewards = [r.get("reward") for r in recs if r.get("reward") is not None]
        mean = sum(rewards) / len(rewards) if rewards else float("nan")
        key = (SHORT[model], n, pert)
        mt = os.path.getmtime(f)
        if key not in best or mt > best[key]["mtime"]:
            best[key] = {"mean": mean, "n_valid": len(rewards), "mtime": mt}
    return best


def write_mcq_table(best, n, dataset_label, fname):
    rows = []
    status = []
    for m in MODEL_ORDER:
        s = SHORT[m]
        cell = {p: best.get((s, n, p)) for p in PERTS}
        present = {p: (cell[p]["mean"] if cell[p] else None) for p in PERTS}
        rows.append((s, present))
        for p in PERTS:
            status.append((dataset_label, s, p, "valid" if cell[p] else "MISSING"))
    # CSV
    with open(OUT / (fname + ".csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["model", "acc_none", "acc_shuffle", "delta_shuffle",
                    "abstain_remove_answer", "inappr_remove_answer",
                    "abstain_remove_context", "inappr_remove_context", "n"])
        for s, pr in rows:
            none, shuf = pr["none"], pr["shuffle"]
            ra, rc = pr["remove_answer"], pr["remove_context"]
            w.writerow([s,
                        "" if none is None else f"{none:.4f}",
                        "" if shuf is None else f"{shuf:.4f}",
                        "" if (none is None or shuf is None) else f"{none - shuf:.4f}",
                        "" if ra is None else f"{ra:.4f}",
                        "" if ra is None else f"{1 - ra:.4f}",
                        "" if rc is None else f"{rc:.4f}",
                        "" if rc is None else f"{1 - rc:.4f}", n])

    def ci(rate, nn):
        if rate is None:
            return "—"
        k = round(rate * nn)
        p, lo, hi = wilson(k, nn)
        return f"{p:.3f} [{lo:.2f}, {hi:.2f}]"

    lines = [f"# {dataset_label} (n = {n} per cell)\n",
             "Accuracy for `none`/`shuffle`; inappropriate-confident rate (1 − appropriate "
             "abstention) for the removal conditions. Wilson 95% CIs. Only error-free runs "
             "are included.\n",
             "| model | acc (none) | acc (shuffle) | Δacc | inappropriate — answer removed | inappropriate — context removed |",
             "|---|---|---|---|---|---|"]
    for s, pr in rows:
        none, shuf = pr["none"], pr["shuffle"]
        ra, rc = pr["remove_answer"], pr["remove_context"]
        d = "—" if (none is None or shuf is None) else f"{none - shuf:+.3f}"
        lines.append(f"| {s} | {'' if none is None else f'{none:.3f}'} | "
                     f"{'' if shuf is None else f'{shuf:.3f}'} | {d} | "
                     f"{ci(None if ra is None else 1 - ra, n)} | {ci(None if rc is None else 1 - rc, n)} |")
    (OUT / (fname + ".md")).write_text("\n".join(lines) + "\n")
    return status


def merge_rollout():
    merged: dict[str, dict] = {}
    for path in ROLLOUT_JSONS:
        if not os.path.exists(path):
            continue
        data = json.loads(open(path).read())
        for model, perts in data.items():
            # skip cells that are degenerate quota artifacts (mean==1.0 & sd==0 -> all reward 0)
            for pert, d in perts.items():
                if d.get("mean") == 1.0 and d.get("sd") == 0.0:
                    continue
                merged.setdefault(model, {})[pert] = d
    lines = ["# Within-model sampling variance (MedQA abstention cells)\n",
             "Each cell re-run 5× at n=50, single rollout each, fixed items. "
             "Rate = inappropriate-confident (1 − appropriate-abstention). Quota-blocked "
             "(all-error) repetitions are excluded.\n",
             "| model | condition | mean | SD | min | max | range | k |",
             "|---|---|---|---|---|---|---|---|"]
    label = {"opus-4_8-high": "Opus 4.8", "gpt-5_5-high": "GPT-5.5",
             "grok-4_3": "Grok 4.3", "gemini-3_5-flash": "Gemini 3.5 Flash"}
    for model in ["opus-4_8-high", "gpt-5_5-high", "grok-4_3", "gemini-3_5-flash"]:
        for pert in ["remove_answer", "remove_context"]:
            d = merged.get(model, {}).get(pert)
            if not d:
                lines.append(f"| {label.get(model, model)} | {pert} | — | — | — | — | — | 0 |")
                continue
            lines.append(f"| {label.get(model, model)} | {pert} | {d['mean']:.3f} | {d['sd']:.3f} | "
                         f"{d['min']:.3f} | {d['max']:.3f} | {d['max'] - d['min']:.3f} | {d['k']} |")
    (OUT / "rollout_variance.md").write_text("\n".join(lines) + "\n")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    best = scan_cells()
    st1 = write_mcq_table(best, 300, "Larger-n MedQA", "medqa_n300")
    st2 = write_mcq_table(best, 200, "MedMCQA (second benchmark)", "medmcqa_n200")
    merge_rollout()
    status = st1 + st2
    slines = ["# Supplementary consolidation status\n",
              "Per-cell validity after consolidation (error-free runs only).\n",
              "| study | model | condition | status |", "|---|---|---|---|"]
    for ds, m, p, s in status:
        mark = s if s == "valid" else f"**{s}**"
        slines.append(f"| {ds} | {m} | {p} | {mark} |")
    missing = [x for x in status if x[3] != "valid"]
    slines.append(f"\n**{len(status) - len(missing)}/{len(status)} MCQ cells valid; "
                  f"{len(missing)} still missing.**")
    (OUT / "STATUS.md").write_text("\n".join(slines) + "\n")
    print("\n".join(slines))
    print(f"\nWrote tables to {OUT}/")


if __name__ == "__main__":
    main()
