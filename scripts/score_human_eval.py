#!/usr/bin/env python
"""Score judge-vs-human agreement once human_labels.csv is filled.

Joins the human labels (runs/human_eval/human_labels.csv) to key.json and the
panel votes (runs/judge_panel/votes.jsonl), then reports, for each judge, raw
agreement and Cohen's kappa against the human labels. This is the validity check:
does the LLM judge match expert human judgment of "appropriate uncertainty"?
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

PROV_SHORT = {"openai": "GPT-5.5", "anthropic": "Opus 4.8", "xai": "Grok 4.3", "google": "Gemini 3.5 Flash"}
PROV_ORDER = ["openai", "anthropic", "xai", "google"]


def cohen_kappa(a: list[int], b: list[int]) -> float | None:
    n = len(a)
    if n == 0:
        return None
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    pa1 = sum(a) / n
    pb1 = sum(b) / n
    pe = pa1 * pb1 + (1 - pa1) * (1 - pb1)
    if pe >= 1.0:
        return 1.0
    return (po - pe) / (1 - pe)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--human-dir", default="runs/human_eval")
    ap.add_argument("--votes", default="runs/judge_panel/votes.jsonl")
    ap.add_argument("--out", default="runs/human_eval")
    args = ap.parse_args()

    hd = Path(args.human_dir)
    key = json.loads((hd / "key.json").read_text())

    human = {}
    with open(hd / "human_labels.csv") as fh:
        for row in csv.DictReader(fh):
            v = (row.get("human_label") or "").strip()
            if v in ("0", "1"):
                human[row["annotation_id"]] = int(v)

    if not human:
        raise SystemExit("No human labels found in human_labels.csv (fill the human_label column with 0/1).")

    # votes keyed by (subject_model, item)
    votes = {}
    for line in open(args.votes):
        r = json.loads(line)
        votes[(r["subject_model"], r["item"])] = r["votes"]

    # Assemble aligned vectors per judge over labeled items.
    judge_vecs = {p: [] for p in PROV_ORDER}
    human_vec = []
    used = 0
    for ann_id, h in human.items():
        meta = key.get(ann_id)
        if not meta:
            continue
        v = votes.get((meta["subject_model"], meta["item"]))
        if not v:
            continue
        # require all judges present for an apples-to-apples comparison
        jv = {p: v.get(p) for p in PROV_ORDER}
        if any(jv[p] is None for p in PROV_ORDER):
            continue
        human_vec.append(h)
        for p in PROV_ORDER:
            judge_vecs[p].append(1 if jv[p] else 0)
        used += 1

    results = {}
    for p in PROV_ORDER:
        a, b = judge_vecs[p], human_vec
        agree = sum(1 for x, y in zip(a, b) if x == y) / len(b) if b else None
        results[p] = {"n": len(b), "raw_agreement": agree, "cohen_kappa": cohen_kappa(a, b)}

    def f(x):
        return "—" if x is None else f"{x:.3f}"

    lines = ["# Judge-vs-human validity check\n"]
    lines.append(f"Human-labeled items used (all judges present): **{used}** of {len(human)} labeled.\n")
    lines.append("Agreement of each judge with the human annotator on the appropriate-uncertainty criterion.\n")
    lines.append("| judge | n | raw agreement | Cohen's kappa |")
    lines.append("|---|---|---|---|")
    for p in PROV_ORDER:
        r = results[p]
        lines.append(f"| {PROV_SHORT[p]} | {r['n']} | {f(r['raw_agreement'])} | {f(r['cohen_kappa'])} |")
    human_rate = sum(human_vec) / len(human_vec) if human_vec else None
    lines.append(f"\nHuman appropriate-uncertainty rate on this subsample: **{f(human_rate)}** (n={len(human_vec)}).")

    (Path(args.out) / "human_validity.md").write_text("\n".join(lines) + "\n")
    (Path(args.out) / "human_validity.json").write_text(json.dumps({"results": results, "human_rate": human_rate, "n_used": used}, indent=2))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
