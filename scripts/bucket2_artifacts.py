#!/usr/bin/env python
"""Reviewer-facing artifacts from EXISTING data (no new model calls):

  1. Forest plot of MCQ inappropriate-confident rates (remove_answer / remove_context)
     with Wilson 95% CIs  -> runs/final/forest_mcq_abstention.png
  2. Raw-count appendix table (k/n per model x condition)  -> runs/final/raw_counts.md
  3. Judge-vs-human confusion matrices (false-lenient vs false-strict)
     -> runs/human_eval/confusion_matrices.md

MCQ cell size is n=100 (canonical runs/final/cells.csv; rates are exact /100).
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

MODELS = ["opus-4_8-high", "gpt-5_5-high", "grok-4_3", "gemini-3_5-flash"]
SHORT = {"opus-4_8-high": "Opus 4.8", "gpt-5_5-high": "GPT-5.5", "grok-4_3": "Grok 4.3",
         "gemini-3_5-flash": "Gemini 3.5 Flash"}
PROV_ORDER = ["openai", "anthropic", "xai", "google"]
PROV_SHORT = {"openai": "GPT-5.5", "anthropic": "Opus 4.8", "xai": "Grok 4.3", "google": "Gemini 3.5 Flash"}
N_MCQ = 100


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float, float]:
    if n == 0:
        return (float("nan"),) * 3
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return p, center - half, center + half


def load_cells(path: str) -> dict[tuple[str, str], float]:
    cells = {}
    with open(path) as fh:
        for row in csv.DictReader(fh):
            cells[(row["model"], row["condition"])] = float(row["mean_reward"])
    return cells


def forest_and_counts(cells, outdir: Path) -> None:
    # inappropriate-confident = 1 - reward for the two removal conditions
    conds = [("remove_answer", "Answer removed"), ("remove_context", "Context removed")]
    fig, ax = plt.subplots(figsize=(8, 5))
    yticks, ylabels = [], []
    y = 0
    colors = {"remove_answer": "#c0392b", "remove_context": "#2980b9"}
    for m in MODELS:
        for cond, _ in conds:
            reward = cells[(m, cond)]
            k = round((1 - reward) * N_MCQ)
            p, lo, hi = wilson(k, N_MCQ)
            ax.errorbar(p, y, xerr=[[p - lo], [hi - p]], fmt="o", color=colors[cond],
                        capsize=3, markersize=6)
            yticks.append(y)
            ylabels.append(f"{SHORT[m]} — {dict(conds)[cond].lower()}")
            y += 1
        y += 0.6
    ax.set_yticks(yticks)
    ax.set_yticklabels(ylabels, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("Inappropriate-confident rate (1 − appropriate abstention), Wilson 95% CI")
    ax.set_title(f"MCQ failure-to-abstain with confidence intervals (MedQA, n={N_MCQ})")
    ax.set_xlim(0, max(0.4, ax.get_xlim()[1]))
    ax.grid(axis="x", alpha=0.3)
    from matplotlib.lines import Line2D
    ax.legend(handles=[Line2D([0], [0], marker="o", color=colors["remove_answer"], ls="", label="Answer removed"),
                       Line2D([0], [0], marker="o", color=colors["remove_context"], ls="", label="Context removed")],
              fontsize=8, loc="lower right")
    fig.tight_layout()
    fig.savefig(outdir / "forest_mcq_abstention.png", dpi=150)
    plt.close(fig)

    # raw counts table
    lines = ["# Appendix C. Raw counts (MedQA, n=100 per cell)\n",
             "Integer counts behind every MCQ rate, so CIs can be recomputed. For "
             "`none`/`shuffle`, count = correct answers. For the removal conditions, "
             "`abstain` = correct abstentions and `inappropriate` = confident wrong answers "
             "(abstain + inappropriate = n).\n",
             "| model | correct (none) | correct (shuffle) | abstain (ans) | inappropriate (ans) | abstain (ctx) | inappropriate (ctx) |",
             "|---|---|---|---|---|---|---|"]
    for m in MODELS:
        none_k = round(cells[(m, "none")] * N_MCQ)
        shuf_k = round(cells[(m, "shuffle")] * N_MCQ)
        ra_ab = round(cells[(m, "remove_answer")] * N_MCQ)
        rc_ab = round(cells[(m, "remove_context")] * N_MCQ)
        lines.append(f"| {SHORT[m]} | {none_k}/{N_MCQ} | {shuf_k}/{N_MCQ} | {ra_ab}/{N_MCQ} | "
                     f"{N_MCQ-ra_ab}/{N_MCQ} | {rc_ab}/{N_MCQ} | {N_MCQ-rc_ab}/{N_MCQ} |")
    (outdir / "raw_counts.md").write_text("\n".join(lines) + "\n")


def confusion(votes_path: str, human_dir: Path) -> None:
    key = json.loads((human_dir / "key.json").read_text())
    human = {}
    with open(human_dir / "human_labels.csv") as fh:
        for row in csv.DictReader(fh):
            v = (row.get("human_label") or "").strip()
            if v in ("0", "1"):
                human[row["annotation_id"]] = int(v)
    votes = {}
    for line in open(votes_path):
        r = json.loads(line)
        votes[(r["subject_model"], r["item"])] = r["votes"]

    # For each judge: 2x2 vs human. human/judge 1 = appropriate-uncertainty met.
    lines = ["# Judge-vs-human confusion matrices (blinded 50-item subsample)\n",
             "Cells: counts of items. **false-lenient** = judge says appropriate-uncertainty "
             "but human says confident/inappropriate (judge too soft); **false-strict** = "
             "judge says inappropriate but human says appropriate. The asymmetry is the key "
             "finding: judges err lenient far more than strict.\n"]
    summary = ["| judge | both-appropriate | both-inappropriate | false-lenient (J=1,H=0) | false-strict (J=0,H=1) |",
               "|---|---|---|---|---|"]
    for p in PROV_ORDER:
        a = b = fl = fs = 0
        for ann_id, h in human.items():
            meta = key.get(ann_id)
            if not meta:
                continue
            v = votes.get((meta["subject_model"], meta["item"]))
            if not v or v.get(p) is None:
                continue
            j = 1 if v[p] else 0
            if j == 1 and h == 1:
                a += 1
            elif j == 0 and h == 0:
                b += 1
            elif j == 1 and h == 0:
                fl += 1
            else:
                fs += 1
        summary.append(f"| {PROV_SHORT[p]} | {a} | {b} | **{fl}** | {fs} |")
    lines += summary
    (human_dir / "confusion_matrices.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def main() -> None:
    final = Path("runs/final")
    cells = load_cells(str(final / "cells.csv"))
    forest_and_counts(cells, final)
    confusion("runs/judge_panel/votes.jsonl", Path("runs/human_eval"))
    print(f"\nWrote {final/'forest_mcq_abstention.png'}, {final/'raw_counts.md'}, "
          f"runs/human_eval/confusion_matrices.md")


if __name__ == "__main__":
    main()
