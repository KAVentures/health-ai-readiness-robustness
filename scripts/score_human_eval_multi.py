#!/usr/bin/env python
"""Generalized N-annotator validity + inter-rater scoring for the abstention probe.

Extends score_human_eval.py from one human to any number. Given several filled label
files (one per human rater), all labeling the SAME blinded items (key.json), it reports:

  1. Per-annotator vs each LLM judge     — raw agreement + Cohen's κ (validity, as before).
  2. Human inter-rater reliability       — pairwise raw agreement + pairwise Cohen's κ,
                                            and Fleiss' κ across all humans (items every
                                            human labeled). This is the estimate the
                                            single-annotator check could NOT provide.
  3. Human CONSENSUS (majority) vs judge  — raw agreement + Cohen's κ. Ties (even rater
                                            count) are dropped and counted.
  4. Appropriate-uncertainty rate per annotator and for the consensus.

It fabricates nothing: annotators with no filled labels are skipped, and if fewer than
two humans are present the inter-rater section is reported as unavailable.

Label-file discovery (any of, deduped by resolved path):
  - runs/human_eval/human_labels.csv                  -> annotator id "R1" (legacy)
  - runs/human_eval/labels_*.csv                      -> id from filename suffix
  - runs/human_eval/packets/<id>/labels_<id>.csv      -> id = <id>
Override with --labels id=path [id=path ...].
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import os
from itertools import combinations
from pathlib import Path

PROV_SHORT = {"openai": "GPT-5.5", "anthropic": "Opus 4.8", "xai": "Grok 4.3", "google": "Gemini 3.5 Flash"}
PROV_ORDER = ["openai", "anthropic", "xai", "google"]


def cohen_kappa(a: list[int], b: list[int]) -> float | None:
    n = len(a)
    if n == 0:
        return None
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    pa1, pb1 = sum(a) / n, sum(b) / n
    pe = pa1 * pb1 + (1 - pa1) * (1 - pb1)
    return 1.0 if pe >= 1.0 else (po - pe) / (1 - pe)


def fleiss_kappa(rows: list[list[int]]) -> float | None:
    """rows[i] = [count_cat0, count_cat1] for item i; every item rated by the same n."""
    if not rows:
        return None
    n = sum(rows[0])
    if n < 2 or any(sum(r) != n for r in rows):
        return None
    N = len(rows)
    p_j = [sum(r[c] for r in rows) / (N * n) for c in (0, 1)]
    P_i = [(sum(x * x for x in r) - n) / (n * (n - 1)) for r in rows]
    P_bar = sum(P_i) / N
    P_e = sum(p * p for p in p_j)
    return 1.0 if P_e >= 1.0 else (P_bar - P_e) / (1 - P_e)


def load_labels(path: str) -> dict[str, int]:
    out: dict[str, int] = {}
    with open(path) as fh:
        for row in csv.DictReader(fh):
            v = (row.get("human_label") or "").strip()
            if v in ("0", "1"):
                out[row["annotation_id"]] = int(v)
    return out


def discover(human_dir: Path) -> dict[str, str]:
    found: dict[str, str] = {}
    legacy = human_dir / "human_labels.csv"
    if legacy.exists():
        found["R1"] = str(legacy)
    for p in glob.glob(str(human_dir / "labels_*.csv")):
        aid = Path(p).stem.replace("labels_", "")
        found[aid] = p
    # packet stubs are usually blank; never let them clobber a filled top-level file
    for p in glob.glob(str(human_dir / "packets" / "*" / "labels_*.csv")):
        aid = Path(p).parent.name
        found.setdefault(aid, p)
    return found


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--human-dir", default="runs/human_eval")
    ap.add_argument("--votes", default="runs/judge_panel/votes.jsonl")
    ap.add_argument("--labels", nargs="*", default=None,
                    help="explicit id=path pairs; overrides auto-discovery")
    ap.add_argument("--out", default="runs/human_eval")
    args = ap.parse_args()

    hd = Path(args.human_dir)
    key = json.loads((hd / "key.json").read_text())

    if args.labels:
        srcs = {}
        for spec in args.labels:
            aid, path = spec.split("=", 1)
            srcs[aid] = path
    else:
        srcs = discover(hd)

    # dedupe by resolved path, keep non-empty
    seen_paths, annotators = set(), {}
    for aid, path in sorted(srcs.items()):
        rp = os.path.realpath(path)
        if rp in seen_paths:
            continue
        labels = load_labels(path)
        if labels:
            annotators[aid] = labels
            seen_paths.add(rp)
    if not annotators:
        raise SystemExit("No filled label files found. Fill at least one labels CSV with 0/1.")

    # judge votes keyed by (subject_model, item)
    votes = {}
    for line in open(args.votes):
        r = json.loads(line)
        votes[(r["subject_model"], r["item"])] = r["votes"]

    def judges_for(ann_id):
        meta = key.get(ann_id)
        if not meta:
            return None
        v = votes.get((meta["subject_model"], meta["item"]))
        if not v:
            return None
        jv = {p: v.get(p) for p in PROV_ORDER}
        if any(jv[p] is None for p in PROV_ORDER):
            return None
        return {p: (1 if jv[p] else 0) for p in PROV_ORDER}

    ids = list(annotators.keys())

    # ---- 1. per-annotator vs judges ----
    per_ann = {}
    for aid, labels in annotators.items():
        jvecs = {p: [] for p in PROV_ORDER}
        hvec = []
        for ann_id, h in labels.items():
            jv = judges_for(ann_id)
            if jv is None:
                continue
            hvec.append(h)
            for p in PROV_ORDER:
                jvecs[p].append(jv[p])
        per_ann[aid] = {
            "n": len(hvec),
            "rate": (sum(hvec) / len(hvec)) if hvec else None,
            "judges": {p: {"raw": (sum(1 for x, y in zip(jvecs[p], hvec) if x == y) / len(hvec)) if hvec else None,
                           "kappa": cohen_kappa(jvecs[p], hvec)} for p in PROV_ORDER},
        }

    # ---- 2. human inter-rater ----
    common = set(annotators[ids[0]])
    for aid in ids[1:]:
        common &= set(annotators[aid])
    common = sorted(common)
    pairwise, fleiss = [], None
    if len(ids) >= 2:
        for a, b in combinations(ids, 2):
            va = [annotators[a][i] for i in common]
            vb = [annotators[b][i] for i in common]
            raw = (sum(1 for x, y in zip(va, vb) if x == y) / len(va)) if va else None
            pairwise.append((a, b, len(va), raw, cohen_kappa(va, vb)))
        rows = [[sum(1 for aid in ids if annotators[aid][i] == c) for c in (0, 1)] for i in common]
        fleiss = fleiss_kappa(rows)

    # ---- 3. consensus (majority) vs judges ----
    consensus, ties = {}, 0
    for i in common:
        s = sum(annotators[aid][i] for aid in ids)
        if 2 * s == len(ids):  # tie
            ties += 1
            continue
        consensus[i] = 1 if 2 * s > len(ids) else 0
    cons_judges = {}
    if consensus:
        jvecs = {p: [] for p in PROV_ORDER}
        cvec = []
        for i, c in consensus.items():
            jv = judges_for(i)
            if jv is None:
                continue
            cvec.append(c)
            for p in PROV_ORDER:
                jvecs[p].append(jv[p])
        cons_rate = (sum(cvec) / len(cvec)) if cvec else None
        cons_n = len(cvec)
        cons_judges = {p: {"raw": (sum(1 for x, y in zip(jvecs[p], cvec) if x == y) / len(cvec)) if cvec else None,
                           "kappa": cohen_kappa(jvecs[p], cvec)} for p in PROV_ORDER}
    else:
        cons_rate, cons_n = None, 0

    # ---- render ----
    def f(x):
        return "—" if x is None else f"{x:.3f}"

    L = ["# Multi-annotator validity + inter-rater reliability\n",
         f"Annotators: **{', '.join(ids)}** ({len(ids)} humans). Common items labeled by "
         f"all: **{len(common)}**.\n"]

    L.append("\n## 1. Each annotator vs LLM judges (validity)\n")
    L.append("Cohen's κ of each human annotator against each judge (raw agreement in JSON).\n")
    L.append("| annotator | n | human rate | vs GPT-5.5 (κ) | vs Opus (κ) | vs Grok (κ) | vs Gemini (κ) |")
    L.append("|---|---|---|---|---|---|---|")
    for aid in ids:
        r = per_ann[aid]
        cells = " | ".join(f(r["judges"][p]["kappa"]) for p in PROV_ORDER)
        L.append(f"| {aid} | {r['n']} | {f(r['rate'])} | {cells} |")

    L.append("\n## 2. Human inter-rater reliability\n")
    if len(ids) < 2:
        L.append("_Only one annotator present — inter-rater reliability is not defined. "
                 "Hand out additional packets (scripts/make_annotator_packets.py) to "
                 "distinct clinicians and re-run._\n")
    else:
        L.append(f"**Fleiss' κ across all {len(ids)} humans (n={len(common)} common items): "
                 f"{f(fleiss)}.**\n")
        L.append("| pair | n | raw agreement | Cohen's κ |")
        L.append("|---|---|---|---|")
        for a, b, n, raw, k in pairwise:
            L.append(f"| {a} ↔ {b} | {n} | {f(raw)} | {f(k)} |")

    L.append("\n## 3. Human consensus (majority vote) vs LLM judges\n")
    if len(ids) < 2:
        L.append("_Needs ≥2 annotators._\n")
    else:
        L.append(f"Consensus over {len(consensus)} items (ties dropped: {ties}); consensus "
                 f"appropriate-uncertainty rate **{f(cons_rate)}** (n={cons_n}).\n")
        L.append("| judge | n | raw agreement | Cohen's κ |")
        L.append("|---|---|---|---|")
        for p in PROV_ORDER:
            d = cons_judges.get(p, {"raw": None, "kappa": None})
            L.append(f"| {PROV_SHORT[p]} | {cons_n} | {f(d['raw'])} | {f(d['kappa'])} |")

    out = Path(args.out)
    (out / "human_validity_multi.md").write_text("\n".join(L) + "\n")
    (out / "human_validity_multi.json").write_text(json.dumps({
        "annotators": ids,
        "n_common": len(common),
        "per_annotator": per_ann,
        "fleiss_kappa": fleiss,
        "pairwise": [{"a": a, "b": b, "n": n, "raw": raw, "kappa": k} for a, b, n, raw, k in pairwise],
        "consensus": {"n": cons_n, "rate": cons_rate, "ties_dropped": ties, "judges": cons_judges},
    }, indent=2))
    print("\n".join(L))
    print(f"\nWrote {out/'human_validity_multi.md'} and .json")


if __name__ == "__main__":
    main()
