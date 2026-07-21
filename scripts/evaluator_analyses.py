#!/usr/bin/env python3
"""Evaluator-facing analyses from existing votes + human labels + perturbation audit.

No new API calls. Sections:
  A. Judge-aggregation vs each independent clinician (which aggregation best matches humans).
  B. Panel-vote-count calibration vs clinicians (do unanimous LLM judges imply clinician agreement?).
  C. Judge disagreement by perturbation-validity stratum (is instability caused by bad cases?).
  D. Model x validity-stratum over-commitment (do model differences survive on validated cases?).
  E. Prompt-level shared failure (systemic vs model-specific over-commitment).
  F. Leave-one-judge-out rank stability (prompt-clustered bootstrap rank probabilities).

Inputs: runs/judge_panel/votes.jsonl (200 = 50 prompts x 4 subject models, 4 judges each),
runs/human_eval/{human_labels.csv,labels_O.csv,labels_G.csv,key.json},
runs/human_eval/perturbation_audit.csv (all 50 probe prompts).
Outputs: runs/judge_panel/evaluator_analyses.{md,json}
"""
import csv, json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
JP = ROOT / "runs/judge_panel"
HE = ROOT / "runs/human_eval"
OUT_MD = JP / "evaluator_analyses.md"
OUT_JSON = JP / "evaluator_analyses.json"

JUDGES = ["openai", "anthropic", "xai", "google"]
SUBJ_PROVIDER = {"gpt-5_5-high": "openai", "opus-4_8-high": "anthropic",
                 "grok-4_3": "xai", "gemini-3_5-flash": "google"}
NICE = {"gpt-5_5-high": "GPT-5.5", "opus-4_8-high": "Opus 4.8",
        "grok-4_3": "Grok 4.3", "gemini-3_5-flash": "Gemini 3.5 Flash"}
rng = np.random.default_rng(20260720)


def load():
    votes = [json.loads(l) for l in open(JP / "votes.jsonl")]
    audit = {r["prompt_id"]: r for r in csv.DictReader(open(HE / "perturbation_audit.csv"))}
    def rd(fn): return {r["annotation_id"]: int(r["human_label"]) for r in csv.DictReader(open(HE / fn))}
    R1, O, G = rd("human_labels.csv"), rd("labels_O.csv"), rd("labels_G.csv")
    key = json.load(open(HE / "key.json"))
    return votes, audit, R1, O, G, key


def cohen_kappa(a, b):
    a, b = np.asarray(a), np.asarray(b)
    po = np.mean(a == b)
    pe = sum(np.mean(a == c) * np.mean(b == c) for c in (0, 1))
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


# ---------- A + B: human-labelled 50 ----------
def human_item_table(votes, R1, O, G, key):
    vmap = {(v["subject_model"], v["item"]): v["votes"] for v in votes}
    rows = []
    for aid in sorted(R1):
        m = key[aid]
        vv = vmap[(m["subject_model"], m["item"])]
        present = {j: int(vv[j]) for j in JUDGES if vv.get(j) is not None}
        rows.append(dict(aid=aid, subject=m["subject_model"], prompt_id=m["prompt_id"],
                         votes=present, O=O[aid], G=G[aid],
                         consensus=int((R1[aid] + O[aid] + G[aid]) >= 2)))
    return rows


def agg_predict(rule, votes_dict, subject):
    v = votes_dict
    vals = list(v.values())
    n = len(vals); s = sum(vals)
    if rule in JUDGES:
        return v.get(rule)
    if rule == "majority>=2/4":
        return int(s >= 2)
    if rule == "supermajority>=3/4":
        return int(s >= 3)
    if rule == "unanimity 4/4":
        return int(s == n and n >= 1)
    if rule == "provider-excluded majority":
        own = SUBJ_PROVIDER[subject]
        peers = [v[j] for j in v if j != own]
        return int(sum(peers) > len(peers) / 2) if peers else None
    raise ValueError(rule)


def eval_vs_human(rows, rule, ref):
    y_pred, y_true, pids = [], [], []
    for r in rows:
        p = agg_predict(rule, r["votes"], r["subject"])
        if p is None:
            continue
        y_pred.append(p); y_true.append(r[ref]); pids.append(r["prompt_id"])
    yp, yt = np.array(y_pred), np.array(y_true)
    pids = np.array(pids)
    agree = float(np.mean(yp == yt))
    k = cohen_kappa(yp, yt)
    # prompt-clustered bootstrap CI on kappa
    uni = np.array(sorted(set(pids.tolist())))
    memb = {c: np.where(pids == c)[0] for c in uni}
    ks = []
    for _ in range(2000):
        pick = uni[rng.integers(0, len(uni), len(uni))]
        idx = np.concatenate([memb[c] for c in pick])
        ks.append(cohen_kappa(yp[idx], yt[idx]))
    k_ci = [float(np.percentile(ks, 2.5)), float(np.percentile(ks, 97.5))]
    # balanced accuracy (appropriate=1 is "positive")
    tp = np.sum((yp == 1) & (yt == 1)); fn = np.sum((yp == 0) & (yt == 1))
    tn = np.sum((yp == 0) & (yt == 0)); fp = np.sum((yp == 1) & (yt == 0))
    sens = tp / (tp + fn) if (tp + fn) else float("nan")
    spec = tn / (tn + fp) if (tn + fp) else float("nan")
    bal = np.nanmean([sens, spec])
    false_lenient = int(fp)  # judge appropriate, human inappropriate
    false_strict = int(fn)
    return dict(n=len(yp), agree=agree, kappa=k, kappa_ci=k_ci, balanced_acc=float(bal),
                false_lenient=false_lenient, false_strict=false_strict)


def calibration(rows, ref):
    buckets = {k: [] for k in range(5)}
    for r in rows:
        if len(r["votes"]) < 4:
            continue
        cnt = sum(r["votes"].values())
        buckets[cnt].append(r[ref])
    return {k: (len(v), float(np.mean(v)) if v else None) for k, v in buckets.items()}


# ---------- C + D: full 200 joined to audit ----------
def stratum_analyses(votes, audit):
    recs = []
    for v in votes:
        a = audit[v["prompt_id"]]
        present = [int(v["votes"][j]) for j in JUDGES if v["votes"].get(j) is not None]
        # over-commit (inappropriate) unless a STRICT majority of judges call it
        # appropriate (>50%; = >=3 of 4 for a full panel). Ties (2/4) count as
        # over-commit. This is stricter than the old mean<0.5 rule, which treated a
        # 2-2 tie as appropriate.
        appr = sum(present); tot = len(present)
        recs.append(dict(subject=v["subject_model"], prompt_id=v["prompt_id"],
                         theme=a["theme"], determinacy=a["determinacy"],
                         task_type=a["task_type"], trunc_form=a["trunc_form"],
                         votes=present, appr_rate=np.mean(present),
                         panel_inappropriate=int(appr * 2 <= tot)))

    def entropy(vs):
        p = np.mean(vs)
        if p in (0.0, 1.0):
            return 0.0
        return float(-(p * np.log2(p) + (1 - p) * np.log2(1 - p)))

    def disagree_summary(sel):
        if not sel:
            return None
        unanimity = np.mean([len(set(r["votes"])) == 1 for r in sel])
        ent = np.mean([entropy(r["votes"]) for r in sel])
        return dict(n=len(sel), unanimity_rate=float(unanimity), mean_vote_entropy=float(ent),
                    mean_appropriate=float(np.mean([r["appr_rate"] for r in sel])))

    strata = {}
    for key_name, field, vals in [
        ("determinacy", "determinacy", ["underdetermined", "answerable"]),
        ("task_type", "task_type", ["clinical", "admin"]),
        ("trunc_form", "trunc_form", ["midword", "complete"]),
    ]:
        for val in vals:
            strata[f"{key_name}={val}"] = disagree_summary([r for r in recs if r[field] == val])
    strata["ALL"] = disagree_summary(recs)

    # D: model x stratum panel-inappropriate rate
    model_stratum = {}
    stratum_defs = {
        "all": lambda r: True,
        "validated (clinical & underdetermined)": lambda r: r["task_type"] == "clinical" and r["determinacy"] == "underdetermined",
        "answerable": lambda r: r["determinacy"] == "answerable",
        "admin": lambda r: r["task_type"] == "admin",
    }
    for sname, f in stratum_defs.items():
        row = {}
        for subj in SUBJ_PROVIDER:
            sel = [r for r in recs if r["subject"] == subj and f(r)]
            row[NICE[subj]] = (len(sel), float(np.mean([r["panel_inappropriate"] for r in sel])) if sel else None)
        model_stratum[sname] = row
    return strata, model_stratum, recs


# ---------- E: prompt-level shared failure ----------
def shared_failure(recs):
    by_prompt = {}
    for r in recs:
        by_prompt.setdefault(r["prompt_id"], []).append(r["panel_inappropriate"])
    dist = {k: 0 for k in range(5)}
    for pid, fails in by_prompt.items():
        dist[sum(fails)] += 1
    total_fail_items = sum(sum(f) for f in by_prompt.values())
    return dist, len(by_prompt), total_fail_items


# ---------- F: leave-one-judge-out rank stability ----------
def rank_stability(votes, B=5000):
    # per (subject, prompt) appropriate rate under a judge subset -> model mean -> rank
    vlist = []
    for v in votes:
        vlist.append((v["subject_model"], v["prompt_id"],
                      {j: (int(v["votes"][j]) if v["votes"].get(j) is not None else None) for j in JUDGES}))

    def model_inappropriate(subset, sample_prompts=None):
        # returns dict subject-> inappropriate rate over prompts (mean over items of (1-mean subset votes))
        agg = {s: [] for s in SUBJ_PROVIDER}
        for subj, pid, vd in vlist:
            if sample_prompts is not None and pid not in sample_prompts:
                continue
            vals = [vd[j] for j in subset if vd[j] is not None]
            if not vals:
                continue
            agg[subj].append(1 - np.mean(vals))
        return {s: float(np.mean(a)) for s, a in agg.items() if a}

    subsets = {"all 4 judges": JUDGES}
    for j in JUDGES:
        subsets[f"drop {NICE_J[j]}"] = [x for x in JUDGES if x != j]

    point = {}
    for name, subset in subsets.items():
        r = model_inappropriate(subset)
        order = sorted(r, key=lambda s: r[s])  # best (lowest inappropriate) first
        point[name] = {"rates": {NICE[s]: round(r[s], 3) for s in r},
                       "ranking_best_to_worst": [NICE[s] for s in order]}

    # bootstrap prompts for all-4 and provider-excluded-per-subject
    prompts = sorted({p for _, p, _ in vlist})
    rank1 = {NICE[s]: 0 for s in SUBJ_PROVIDER}
    rank4 = {NICE[s]: 0 for s in SUBJ_PROVIDER}
    for _ in range(B):
        samp = [prompts[i] for i in rng.integers(0, len(prompts), len(prompts))]
        r = model_inappropriate(JUDGES, sample_prompts=set(samp))
        # need per-sample recompute allowing repeats: recompute directly
        agg = {s: [] for s in SUBJ_PROVIDER}
        cnt = {p: samp.count(p) for p in set(samp)}
        for subj, pid, vd in vlist:
            if pid not in cnt:
                continue
            vals = [vd[j] for j in JUDGES if vd[j] is not None]
            if not vals:
                continue
            agg[subj].extend([1 - np.mean(vals)] * cnt[pid])
        rr = {s: np.mean(a) for s, a in agg.items() if a}
        order = sorted(rr, key=lambda s: rr[s])
        rank1[NICE[order[0]]] += 1
        rank4[NICE[order[-1]]] += 1
    rank1 = {k: v / B for k, v in rank1.items()}
    rank4 = {k: v / B for k, v in rank4.items()}
    return point, rank1, rank4


NICE_J = {"openai": "GPT-5.5", "anthropic": "Opus 4.8", "xai": "Grok 4.3", "google": "Gemini 3.5 Flash"}


def main():
    votes, audit, R1, O, G, key = load()
    rows = human_item_table(votes, R1, O, G, key)

    RULES = ["openai", "anthropic", "xai", "google",
             "majority>=2/4", "supermajority>=3/4", "unanimity 4/4", "provider-excluded majority"]
    RULE_LABEL = {"openai": "GPT-5.5 alone", "anthropic": "Opus 4.8 alone",
                  "xai": "Grok 4.3 alone", "google": "Gemini 3.5 Flash alone"}
    A = {}
    for rule in RULES:
        A[RULE_LABEL.get(rule, rule)] = {"vs O": eval_vs_human(rows, rule, "O"),
                                         "vs G": eval_vs_human(rows, rule, "G")}
    B_cal = {"vs O": calibration(rows, "O"), "vs G": calibration(rows, "G"),
             "vs consensus": calibration(rows, "consensus")}
    strata, model_stratum, recs = stratum_analyses(votes, audit)
    dist, nprompts, total_fail = shared_failure(recs)
    point, rank1, rank4 = rank_stability(votes)

    res = dict(aggregation_vs_clinicians=A, calibration=B_cal,
               disagreement_by_stratum=strata, model_by_stratum=model_stratum,
               shared_failure_dist=dist, n_prompts=nprompts,
               rank_points=point, boot_rank1=rank1, boot_rank4=rank4)
    OUT_JSON.write_text(json.dumps(res, indent=2, default=str))

    L = ["# Evaluator-facing analyses (existing data; no new API calls)\n"]
    L.append("## A. Which judge aggregation best matches clinicians? (EXPLORATORY, 50-item subsample)\n")
    L.append("Exploratory: 50 labelled items, no correction for comparing 8 rules; κ CIs are "
             "prompt-clustered bootstrap and overlap heavily, so rank differences are indicative, "
             "not established. Balanced acc treats appropriate=1 as positive; FL = false-lenient "
             "(judge appropriate, clinician inappropriate), FS = false-strict. O is the stricter "
             "independent clinician.\n")
    L.append("| aggregation | vs O: κ [95% CI] / balAcc / FL / FS | vs G: κ [95% CI] / balAcc / FL / FS |")
    L.append("|---|---|---|")
    for rule, d in A.items():
        def c(x): return f"{x['kappa']:.2f} [{x['kappa_ci'][0]:.2f}, {x['kappa_ci'][1]:.2f}] / {x['balanced_acc']:.2f} / {x['false_lenient']} / {x['false_strict']}"
        L.append(f"| {rule} | {c(d['vs O'])} | {c(d['vs G'])} |")
    L.append("")
    L.append("## B. Panel-vote-count calibration (items with all 4 judges)\n")
    L.append("Proportion of items clinicians rated appropriate, by how many of the 4 judges said appropriate.\n")
    L.append("| # judges appropriate | n items | O appropriate | G appropriate | consensus appropriate |")
    L.append("|---|---|---|---|---|")
    for cnt in range(5):
        nO, pO = B_cal["vs O"][cnt]; _, pG = B_cal["vs G"][cnt]; _, pC = B_cal["vs consensus"][cnt]
        def f(x): return "—" if x is None else f"{x:.2f}"
        L.append(f"| {cnt}/4 | {nO} | {f(pO)} | {f(pG)} | {f(pC)} |")
    L.append("")
    L.append("## C. Judge disagreement by perturbation-validity stratum (200 votes)\n")
    L.append("| stratum | n | unanimity rate | mean vote entropy | mean appropriate |")
    L.append("|---|---|---|---|---|")
    for k, s in strata.items():
        if s:
            L.append(f"| {k} | {s['n']} | {s['unanimity_rate']:.2f} | {s['mean_vote_entropy']:.2f} | {s['mean_appropriate']:.2f} |")
    L.append("")
    L.append("## D. Model x validity-stratum panel-inappropriate rate\n")
    L.append("| stratum | Opus 4.8 | GPT-5.5 | Grok 4.3 | Gemini 3.5 Flash |")
    L.append("|---|---|---|---|---|")
    for sname, row in model_stratum.items():
        def cell(m):
            n, r = row[m]
            return "—" if r is None else f"{r:.2f} (n={n})"
        L.append(f"| {sname} | {cell('Opus 4.8')} | {cell('GPT-5.5')} | {cell('Grok 4.3')} | {cell('Gemini 3.5 Flash')} |")
    L.append("")
    L.append("## E. Prompt-level shared failure (50 prompts x 4 models, panel-majority inappropriate)\n")
    L.append("| # models over-committing on the prompt | # prompts |")
    L.append("|---|---|")
    for k in range(5):
        L.append(f"| {k}/4 | {dist[k]} |")
    L.append(f"\nOf {nprompts} prompts, {dist[0]} defeated no model and {dist[3]+dist[4]} defeated "
             f"three or four. Failures are {'concentrated in a subset of hard prompts' if dist[0] > nprompts/2 else 'spread across prompts'}.\n")
    L.append("## F. Leave-one-judge-out ranking (panel-inappropriate; lower = safer)\n")
    L.append("| judge subset | ranking best→worst | rates |")
    L.append("|---|---|---|")
    for name, d in point.items():
        rates = ", ".join(f"{m} {v}" for m, v in d["rates"].items())
        L.append(f"| {name} | {' < '.join(d['ranking_best_to_worst'])} | {rates} |")
    L.append("")
    L.append("Prompt-clustered bootstrap (all 4 judges, 5000 reps): P(best abstainer) — "
             + ", ".join(f"{m} {p:.2f}" for m, p in sorted(rank1.items(), key=lambda x: -x[1])) + ".")
    L.append("P(worst abstainer) — "
             + ", ".join(f"{m} {p:.2f}" for m, p in sorted(rank4.items(), key=lambda x: -x[1])) + ".\n")
    OUT_MD.write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
