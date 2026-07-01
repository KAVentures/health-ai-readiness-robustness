#!/usr/bin/env python
"""Figures for the judge-panel analysis (reads runs/judge_panel/panel_summary.json)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

SHORT = {"opus-4_8-high": "Opus 4.8", "gpt-5_5-high": "GPT-5.5", "grok-4_3": "Grok 4.3", "gemini-3_5-flash": "Gemini 3.5 Flash"}
ORDER = ["opus-4_8-high", "gpt-5_5-high", "grok-4_3", "gemini-3_5-flash"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", default="runs/judge_panel/panel_summary.json")
    ap.add_argument("--out", default="runs/judge_panel")
    args = ap.parse_args()
    d = json.load(open(args.summary))
    out = Path(args.out)

    per_subj = d["per_subject_per_judge"]
    sp = d["self_preference"]

    # Single-judge (GPT-5.5) vs leave-own-provider-out inappropriate-confident rate.
    single = [1 - per_subj[m]["openai"]["rate"] for m in ORDER]
    loo = [1 - sp[m]["peer_mean_rate"] for m in ORDER]

    x = np.arange(len(ORDER))
    w = 0.38
    fig, ax = plt.subplots(figsize=(8, 4.5))
    b1 = ax.bar(x - w / 2, single, w, label="Single judge (GPT-5.5)", color="#bbbbbb")
    b2 = ax.bar(x + w / 2, loo, w, label="Leave-own-provider-out (panel)", color="#c0392b")
    for b in (b1, b2):
        ax.bar_label(b, fmt="%.2f", fontsize=8, padding=2)
    ax.set_xticks(x)
    ax.set_xticklabels([SHORT[m] for m in ORDER], rotation=12, ha="right")
    ax.set_ylabel("Inappropriate-confident rate (1 - appropriate uncertainty)")
    ax.set_title("Open-ended over-confidence: single judge vs self-preference-corrected panel")
    ax.set_ylim(0, max(max(single), max(loo)) * 1.3)
    ax.legend(fontsize=9)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout(); fig.savefig(out / "panel_single_vs_loo.png", dpi=150); plt.close(fig)

    # Self-preference delta per provider's own model.
    deltas = [sp[m]["delta_self_minus_peer"] for m in ORDER]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    colors = ["#c0392b" if v > 0 else "#2980b9" for v in deltas]
    bars = ax.bar([SHORT[m] for m in ORDER], deltas, color=colors)
    ax.bar_label(bars, fmt="%+.2f", fontsize=9, padding=2)
    ax.axhline(0, color="k", linewidth=0.8)
    ax.set_ylabel("Δ (own-provider judge − peer mean)")
    ax.set_title("Judge self-preference on the appropriate-uncertainty criterion")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout(); fig.savefig(out / "panel_self_preference.png", dpi=150); plt.close(fig)

    print(f"Wrote {out/'panel_single_vs_loo.png'} and {out/'panel_self_preference.png'}")


if __name__ == "__main__":
    main()
