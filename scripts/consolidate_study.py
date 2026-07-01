#!/usr/bin/env python
"""Merge the robustness study's scattered run dirs into one final dataset + figures.

The full study was produced across three orchestrator runs:
  - MCQ matrix for opus/gpt-5.5/grok        -> runs/study/cells.csv
  - MCQ matrix for gemini-3.5-flash         -> runs/study_gemini/cells.csv
  - HealthBench baseline(gpt-4.1-mini) +
    context probe(gpt-5.5) for all 4 models -> runs/study_hb_final/healthbench_summary.csv

This script consolidates them into --out (default runs/final): a unified cells.csv,
robustness_summary.csv, healthbench_summary.csv, final_study.md, and figures.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

SHORT = {
    "opus-4_8-high": "Opus 4.8",
    "gpt-5_5-high": "GPT-5.5",
    "grok-4_3": "Grok 4.3",
    "gemini-3_5-flash": "Gemini 3.5 Flash",
}
MODEL_ORDER = ["opus-4_8-high", "gpt-5_5-high", "grok-4_3", "gemini-3_5-flash"]
CONDITIONS = ["none", "shuffle", "remove_answer", "remove_context"]


def read_mcq_cells(path: Path) -> dict[tuple[str, str, str], float]:
    """Return {(dataset, model, condition): mean_reward} for family==medqa rows."""
    out: dict[tuple[str, str, str], float] = {}
    if not path.exists():
        return out
    with open(path) as fh:
        for row in csv.DictReader(fh):
            if row.get("family") and row["family"] != "medqa":
                continue
            out[(row["dataset"], row["model"], row["condition"])] = float(row["mean_reward"])
    return out


def read_hb(path: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    if not path.exists():
        return out
    with open(path) as fh:
        for row in csv.DictReader(fh):
            out[row["model"]] = {
                "baseline": float(row["hb_baseline_score"]) if row["hb_baseline_score"] else None,
                "appropriate_uncertainty": float(row["hb_probe_appropriate_uncertainty"]) if row["hb_probe_appropriate_uncertainty"] else None,
                "inappropriate_confident": float(row["hb_inappropriate_confident_rate"]) if row["hb_inappropriate_confident_rate"] else None,
            }
    return out


def grouped_bars(ax, models, series, title, ylabel):
    x = np.arange(len(models))
    width = 0.8 / max(1, len(series))
    for i, (label, vals) in enumerate(series.items()):
        bars = ax.bar(x + i * width, vals, width, label=label)
        ax.bar_label(bars, fmt="%.2f", fontsize=8, padding=2)
    ax.set_xticks(x + width * (len(series) - 1) / 2)
    ax.set_xticklabels([SHORT.get(m, m) for m in models], rotation=12, ha="right")
    ax.set_ylim(0, 1.08)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend(fontsize=9)
    ax.grid(axis="y", alpha=0.3)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mcq-main", default="runs/study/cells.csv")
    ap.add_argument("--mcq-gemini", default="runs/study_gemini/cells.csv")
    ap.add_argument("--hb", default="runs/study_hb_final/healthbench_summary.csv")
    ap.add_argument("--out", default="runs/final")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    cells = read_mcq_cells(Path(args.mcq_main))
    cells.update(read_mcq_cells(Path(args.mcq_gemini)))
    hb = read_hb(Path(args.hb))

    datasets = sorted({k[0] for k in cells}) or ["medqa"]
    models = [m for m in MODEL_ORDER if any(k[1] == m for k in cells) or m in hb]

    # ---- unified cells.csv ----
    with open(out / "cells.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["dataset", "model", "condition", "mean_reward"])
        for ds in datasets:
            for m in models:
                for c in CONDITIONS:
                    if (ds, m, c) in cells:
                        w.writerow([ds, m, c, f"{cells[(ds, m, c)]:.4f}"])

    # ---- robustness_summary.csv ----
    summ_fields = ["dataset", "model", "acc_baseline", "acc_shuffle", "delta_acc_shuffle",
                   "inappropriate_rate_remove_answer", "inappropriate_rate_remove_context"]
    summ_rows = []
    for ds in datasets:
        for m in models:
            base = cells.get((ds, m, "none"))
            shuf = cells.get((ds, m, "shuffle"))
            ra = cells.get((ds, m, "remove_answer"))
            rc = cells.get((ds, m, "remove_context"))
            summ_rows.append({
                "dataset": ds, "model": m,
                "acc_baseline": base, "acc_shuffle": shuf,
                "delta_acc_shuffle": (base - shuf) if (base is not None and shuf is not None) else None,
                "inappropriate_rate_remove_answer": (1 - ra) if ra is not None else None,
                "inappropriate_rate_remove_context": (1 - rc) if rc is not None else None,
            })
    with open(out / "robustness_summary.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=summ_fields)
        w.writeheader()
        for r in summ_rows:
            w.writerow({k: ("" if r[k] is None else (f"{r[k]:.4f}" if isinstance(r[k], float) else r[k])) for k in summ_fields})

    # ---- healthbench_summary.csv (passthrough, ordered) ----
    with open(out / "healthbench_summary.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["model", "hb_baseline_score", "hb_probe_appropriate_uncertainty", "hb_inappropriate_confident_rate"])
        for m in models:
            if m in hb:
                d = hb[m]
                w.writerow([m,
                            "" if d["baseline"] is None else f"{d['baseline']:.4f}",
                            "" if d["appropriate_uncertainty"] is None else f"{d['appropriate_uncertainty']:.4f}",
                            "" if d["inappropriate_confident"] is None else f"{d['inappropriate_confident']:.4f}"])

    # ---- figures ----
    def fmt(x):
        return float("nan") if x is None else x

    for ds in datasets:
        mds = [m for m in models if (ds, m, "none") in cells]
        fig, ax = plt.subplots(figsize=(8, 4.5))
        grouped_bars(ax, mds, {
            "Baseline": [fmt(cells.get((ds, m, "none"))) for m in mds],
            "Options shuffled": [fmt(cells.get((ds, m, "shuffle"))) for m in mds],
        }, f"MedQA accuracy under option shuffle ({ds})", "Accuracy")
        fig.tight_layout(); fig.savefig(out / f"accuracy_{ds}.png", dpi=150); plt.close(fig)

        fig, ax = plt.subplots(figsize=(8, 4.5))
        grouped_bars(ax, mds, {
            "Correct answer removed": [fmt(1 - cells[(ds, m, "remove_answer")]) if (ds, m, "remove_answer") in cells else float("nan") for m in mds],
            "Context removed": [fmt(1 - cells[(ds, m, "remove_context")]) if (ds, m, "remove_context") in cells else float("nan") for m in mds],
        }, f"MedQA inappropriate-confident-answer rate ({ds})", "Inappropriate-answer rate (1 - abstention)")
        fig.tight_layout(); fig.savefig(out / f"false_confidence_{ds}.png", dpi=150); plt.close(fig)

    if hb:
        hmds = [m for m in models if m in hb]
        fig, ax = plt.subplots(figsize=(8, 4.5))
        grouped_bars(ax, hmds, {
            "Appropriate uncertainty": [fmt(hb[m]["appropriate_uncertainty"]) for m in hmds],
            "Inappropriate confident": [fmt(hb[m]["inappropriate_confident"]) for m in hmds],
        }, "HealthBench: behavior after context removal", "Rate")
        fig.tight_layout(); fig.savefig(out / "healthbench_robustness.png", dpi=150); plt.close(fig)

    # ---- final markdown ----
    def f(x):
        return "—" if x is None else f"{x:.3f}"

    with open(out / "final_study.md", "w") as fh:
        fh.write("# Robustness & readiness study — final results\n\n")
        fh.write("MedQA n=100/cell; HealthBench (consensus) n=50. Models at high reasoning effort.\n")
        fh.write("HealthBench baseline judged by gpt-4.1-mini; context-removal probe judged by gpt-5.5.\n\n")
        fh.write("## MCQ robustness (MedQA)\n\n")
        fh.write("| model | acc | acc(shuffle) | Δacc(shuffle) | inappr-confident (answer removed) | inappr-confident (context removed) |\n")
        fh.write("|---|---|---|---|---|---|\n")
        for r in summ_rows:
            fh.write(f"| {SHORT.get(r['model'], r['model'])} | {f(r['acc_baseline'])} | {f(r['acc_shuffle'])} | "
                     f"{f(r['delta_acc_shuffle'])} | {f(r['inappropriate_rate_remove_answer'])} | "
                     f"{f(r['inappropriate_rate_remove_context'])} |\n")
        fh.write("\n## HealthBench open-ended robustness\n\n")
        fh.write("| model | baseline rubric | appropriate uncertainty | inappropriate confident |\n")
        fh.write("|---|---|---|---|\n")
        for m in models:
            if m in hb:
                d = hb[m]
                fh.write(f"| {SHORT.get(m, m)} | {f(d['baseline'])} | {f(d['appropriate_uncertainty'])} | {f(d['inappropriate_confident'])} |\n")

    print(f"Wrote consolidated outputs to {out}/")
    print((out / "final_study.md").read_text())


if __name__ == "__main__":
    main()
