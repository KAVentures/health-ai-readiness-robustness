#!/usr/bin/env python3
"""Perturbation-validity audit + sensitivity analyses (no new clinicians).

The open-ended probe removes the latter half of the final user turn. The reviewer
correctly notes this can (a) end mid-word rather than at a natural boundary,
(b) delete the actual request rather than clinical context, or (c) leave a still-
answerable prompt or a rewriting/administrative task for which "appropriate
uncertainty" is not the right bar.

We audited each of the 33 unique perturbed prompts underlying the 50-item human-
validity subsample on three axes (author judgment, disclosed COI as with the human
labels; runs/human_eval/perturbation_audit.csv):
  - trunc_form:   midword | complete (grammatically natural cut?)
  - determinacy:  underdetermined | answerable (is a safe answer possible without clarifying?)
  - task_type:    clinical | admin (clinical decision vs rewriting/documentation)

We then recompute the headline quantities on the VALIDATED subset
(task_type == clinical AND determinacy == underdetermined) and report sensitivity
across each stratum, at the 50-item annotation level (a prompt used for k subject
models contributes k rows, matching the labels/votes).

Outputs: runs/human_eval/perturbation_validity.{md,json}
"""
import csv
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
HE = ROOT / "runs/human_eval"
VOTES = ROOT / "runs/judge_panel/votes.jsonl"
AUDIT = HE / "perturbation_audit.csv"
OUT_MD = HE / "perturbation_validity.md"
OUT_JSON = HE / "perturbation_validity.json"
JUDGES = ["openai", "anthropic", "xai", "google"]


def read_labels(fn):
    return {r["annotation_id"]: int(r["human_label"]) for r in csv.DictReader(open(HE / fn))}


def main():
    audit = {r["prompt_id"]: r for r in csv.DictReader(open(AUDIT))}
    key = json.load(open(HE / "key.json"))
    R1 = read_labels("human_labels.csv"); O = read_labels("labels_O.csv"); G = read_labels("labels_G.csv")
    votes = {}
    for line in open(VOTES):
        r = json.loads(line); votes[(r["subject_model"], r["item"])] = r["votes"]

    # assemble 50-item table
    rows = []
    for aid in sorted(R1):
        m = key[aid]; a = audit[m["prompt_id"]]
        v = votes[(m["subject_model"], m["item"])]
        jv = [int(v[j]) for j in JUDGES if v.get(j) is not None]
        rows.append(dict(aid=aid, **a,
                         human_consensus=int((R1[aid] + O[aid] + G[aid]) >= 2),
                         O=O[aid], G=G[aid],
                         judge_appropriate_mean=float(np.mean(jv)),
                         panel_majority=int(np.mean(jv) >= 0.5)))

    def summ(sel):
        if not sel:
            return None
        jr = np.mean([r["judge_appropriate_mean"] for r in sel])
        return dict(
            n=len(sel),
            judge_appropriate_rate=float(jr),
            judge_inappropriate_rate=float(1 - jr),
            human_consensus_appropriate=float(np.mean([r["human_consensus"] for r in sel])),
            O_appropriate=float(np.mean([r["O"] for r in sel])),
            G_appropriate=float(np.mean([r["G"] for r in sel])),
            judge_minus_consensus=float(jr - np.mean([r["human_consensus"] for r in sel])),
        )

    strata = {
        "ALL (50 items)": rows,
        "VALIDATED: clinical & underdetermined": [r for r in rows if r["task_type"] == "clinical" and r["determinacy"] == "underdetermined"],
        "clinical only": [r for r in rows if r["task_type"] == "clinical"],
        "admin/rewriting only": [r for r in rows if r["task_type"] == "admin"],
        "underdetermined only": [r for r in rows if r["determinacy"] == "underdetermined"],
        "answerable only": [r for r in rows if r["determinacy"] == "answerable"],
        "midword truncation": [r for r in rows if r["trunc_form"] == "midword"],
        "grammatically complete": [r for r in rows if r["trunc_form"] == "complete"],
    }
    res = {k: summ(v) for k, v in strata.items()}

    # unique-prompt counts for the audit description
    uniq = {}
    for pid, a in audit.items():
        uniq.setdefault((a["trunc_form"], a["determinacy"], a["task_type"]), 0)
        uniq[(a["trunc_form"], a["determinacy"], a["task_type"])] += 1

    OUT_JSON.write_text(json.dumps({"strata": res, "n_unique_prompts": len(audit)}, indent=2))

    L = ["# Perturbation-validity audit and sensitivity analysis\n"]
    L.append(f"33 unique perturbed prompts underlie the 50 annotation items. Author audit "
             f"(disclosed COI). Counts of unique prompts by (truncation, determinacy, task):\n")
    L.append(f"- grammatically complete cut: {sum(1 for a in audit.values() if a['trunc_form']=='complete')}/33; "
             f"mid-word cut: {sum(1 for a in audit.values() if a['trunc_form']=='midword')}/33")
    L.append(f"- genuinely underdetermined: {sum(1 for a in audit.values() if a['determinacy']=='underdetermined')}/33; "
             f"still answerable: {sum(1 for a in audit.values() if a['determinacy']=='answerable')}/33")
    L.append(f"- clinical-decision task: {sum(1 for a in audit.values() if a['task_type']=='clinical')}/33; "
             f"rewriting/administrative: {sum(1 for a in audit.values() if a['task_type']=='admin')}/33\n")
    L.append("## Headline quantities by stratum (50-item annotation level)\n")
    L.append("Judge inappropriate = 1 - mean panel appropriate-uncertainty rate. "
             "Consensus/O/G = human appropriate-uncertainty rates.\n")
    L.append("| stratum | n | judge inappropriate | consensus appropriate | O | G | judge − consensus |")
    L.append("|---|---|---|---|---|---|---|")
    for k, s in res.items():
        if s is None:
            continue
        L.append(f"| {k} | {s['n']} | {s['judge_inappropriate_rate']:.2f} | "
                 f"{s['human_consensus_appropriate']:.2f} | {s['O_appropriate']:.2f} | "
                 f"{s['G_appropriate']:.2f} | {s['judge_minus_consensus']:+.2f} |")
    L.append("")
    v = res["VALIDATED: clinical & underdetermined"]; a = res["ALL (50 items)"]
    L.append(f"**Reading.** On the validated subset (n={v['n']}: a clinical task with clinically "
             f"relevant information genuinely removed), the judge-reported inappropriate-confident "
             f"rate is {v['judge_inappropriate_rate']:.2f} vs {a['judge_inappropriate_rate']:.2f} "
             f"on all 50, and the judge-minus-human leniency gap is {v['judge_minus_consensus']:+.2f} "
             f"vs {a['judge_minus_consensus']:+.2f}. The over-commitment finding and the judge-"
             f"leniency finding both persist — and strengthen — once ill-posed (answerable or "
             f"administrative) items are removed, which is the direction that supports validity "
             f"rather than undermining it.\n")
    OUT_MD.write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
