#!/usr/bin/env python
"""Render figures for the medrobust robustness study from cells.csv.

Produces, per dataset:
  - accuracy_<dataset>.png        : baseline vs shuffled accuracy by model
  - abstention_<dataset>.png      : appropriate-abstention rate under
                                    remove_answer / remove_context by model

Usage:
  python scripts/plot_robustness_study.py --study runs/study_pilot
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

SHORT = {
    "opus-4_8-high": "Opus 4.8",
    "gpt-5_5-high": "GPT-5.5",
    "grok-4_3": "Grok 4.3",
    "gemini-3_1-pro-high": "Gemini 3.1 Pro",
}


def load_cells(study: Path) -> dict:
    cells: dict = {}
    with open(study / "cells.csv") as fh:
        for row in csv.DictReader(fh):
            cells[(row["dataset"], row["model"], row["perturbation"])] = float(row["mean_reward"])
    return cells


def _grouped_bars(ax, models, series: dict[str, list[float]], title, ylabel):
    import numpy as np

    x = np.arange(len(models))
    width = 0.8 / max(1, len(series))
    for i, (label, vals) in enumerate(series.items()):
        ax.bar(x + i * width, vals, width, label=label)
    ax.set_xticks(x + width * (len(series) - 1) / 2)
    ax.set_xticklabels([SHORT.get(m, m) for m in models], rotation=15, ha="right")
    ax.set_ylim(0, 1)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend()
    ax.grid(axis="y", alpha=0.3)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--study", default="runs/study_pilot")
    args = ap.parse_args()
    study = Path(args.study)
    cells = load_cells(study)

    datasets = sorted({k[0] for k in cells})
    models_in = sorted({k[1] for k in cells})
    order = [m for m in SHORT if m in models_in] + [m for m in models_in if m not in SHORT]

    for ds in datasets:
        # Accuracy: baseline vs shuffle
        fig, ax = plt.subplots(figsize=(8, 4.5))
        series = {
            "Baseline": [cells.get((ds, m, "none"), float("nan")) for m in order],
            "Shuffled options": [cells.get((ds, m, "shuffle"), float("nan")) for m in order],
        }
        _grouped_bars(ax, order, series, f"Accuracy under option shuffle — {ds}", "Accuracy")
        fig.tight_layout()
        fig.savefig(study / f"accuracy_{ds}.png", dpi=150)
        plt.close(fig)

        # Abstention behavior
        fig, ax = plt.subplots(figsize=(8, 4.5))
        series = {
            "Correct answer removed": [cells.get((ds, m, "remove_answer"), float("nan")) for m in order],
            "Context removed": [cells.get((ds, m, "remove_context"), float("nan")) for m in order],
        }
        _grouped_bars(ax, order, series, f"Appropriate abstention rate — {ds}", "Abstention rate")
        fig.tight_layout()
        fig.savefig(study / f"abstention_{ds}.png", dpi=150)
        plt.close(fig)
        print(f"wrote accuracy_{ds}.png and abstention_{ds}.png to {study}")


if __name__ == "__main__":
    main()
