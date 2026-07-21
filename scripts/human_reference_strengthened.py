#!/usr/bin/env python3
"""Strengthened human-reference analysis (no new clinicians).

Addresses the review points that are achievable with the existing 50-item, 3-rater
panel (author R1 + independent clinicians O, G):

  1. Make the two INDEPENDENT clinicians co-primary; treat the author-influenced
     majority-vote consensus as a secondary reference.
  2. Bootstrap 95% CIs (resampling the 50 items) for every Cohen's / Fleiss' kappa.
  3. Report Gwet's AC1 alongside kappa, because kappa is distorted by the high
     prevalence of "appropriate" labels here.
  4. Paired 95% CIs for each judge-minus-human appropriate-uncertainty rate
     difference, on the same 50 items.

Inputs (runs/human_eval/): human_labels.csv (R1), labels_O.csv, labels_G.csv,
key.json; and runs/judge_panel/votes.jsonl for the four LLM-judge votes per item.
Outputs: runs/human_eval/human_reference_strengthened.{md,json}.
"""
import csv
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
HE = ROOT / "runs/human_eval"
VOTES = ROOT / "runs/judge_panel/votes.jsonl"
OUT_MD = HE / "human_reference_strengthened.md"
OUT_JSON = HE / "human_reference_strengthened.json"

JUDGES = ["openai", "anthropic", "xai", "google"]
JNICE = {"openai": "GPT-5.5", "anthropic": "Opus 4.8", "xai": "Grok 4.3", "google": "Gemini 3.5 Flash"}
rng = np.random.default_rng(20260720)


def read_labels(fn):
    d = {}
    for row in csv.DictReader(open(HE / fn)):
        d[row["annotation_id"]] = int(row["human_label"])
    return d


def load_judge_votes():
    by_si = {}
    for line in open(VOTES):
        r = json.loads(line)
        by_si[(r["subject_model"], r["item"])] = r["votes"]
    return by_si


def cohen_kappa(a, b):
    a = np.asarray(a); b = np.asarray(b)
    n = len(a)
    po = np.mean(a == b)
    # expected on 2 categories {0,1}
    pe = sum((np.mean(a == c) * np.mean(b == c)) for c in (0, 1))
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def gwet_ac1(a, b):
    a = np.asarray(a); b = np.asarray(b)
    po = np.mean(a == b)
    # Gwet: pe = 2*pi*(1-pi), pi = mean prevalence of category 1 across raters
    pi = (np.mean(a) + np.mean(b)) / 2
    pe = 2 * pi * (1 - pi)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def fleiss_kappa(mat):
    """mat: n_items x n_categories counts (rows sum to n_raters)."""
    n, k = mat.shape
    nr = mat.sum(1)[0]
    p = mat.sum(0) / (n * nr)
    P = (np.sum(mat * mat, 1) - nr) / (nr * (nr - 1))
    Pbar = P.mean()
    Pe = np.sum(p * p)
    return (Pbar - Pe) / (1 - Pe) if Pe < 1 else 1.0


def boot_ci(fn, *series, clusters=None, B=5000):
    """Bootstrap CI. If `clusters` (one label per item) is given, resample whole
    clusters (prompts) rather than individual items, because the 50 annotation items
    arise from only 33 unique perturbed prompts and are not independent."""
    series = [np.asarray(s) for s in series]
    n = len(series[0])
    vals = []
    if clusters is None:
        for _ in range(B):
            idx = rng.integers(0, n, n)
            vals.append(fn(*[s[idx] for s in series]))
    else:
        clusters = np.asarray(clusters)
        uniq = np.array(sorted(set(clusters.tolist())))
        members = {c: np.where(clusters == c)[0] for c in uniq}
        for _ in range(B):
            pick = uniq[rng.integers(0, len(uniq), len(uniq))]
            idx = np.concatenate([members[c] for c in pick])
            vals.append(fn(*[s[idx] for s in series]))
    lo, hi = np.percentile(vals, [2.5, 97.5])
    return float(lo), float(hi)


def main():
    R1 = read_labels("human_labels.csv")
    O = read_labels("labels_O.csv")
    G = read_labels("labels_G.csv")
    key = json.load(open(HE / "key.json"))
    votes = load_judge_votes()
    ids = sorted(R1)

    r1 = np.array([R1[i] for i in ids])
    o = np.array([O[i] for i in ids])
    g = np.array([G[i] for i in ids])
    clusters = np.array([key[i]["prompt_id"] for i in ids])  # 33 unique prompts across 50 items
    n_uni = len(set(clusters.tolist()))

    # judge votes aligned to annotation ids
    jvote = {j: [] for j in JUDGES}
    jmask = {j: [] for j in JUDGES}  # 1 if present
    for i in ids:
        meta = key[i]
        v = votes[(meta["subject_model"], meta["item"])]
        for j in JUDGES:
            vv = v.get(j)
            jvote[j].append(0 if vv is None else int(vv))
            jmask[j].append(0 if vv is None else 1)

    res = {"rater_rates": {}, "pairwise": {}, "fleiss": {}, "judge_vs_human": {}}

    # rater rates
    for name, arr in [("R1_author", r1), ("O", o), ("G", g)]:
        res["rater_rates"][name] = float(arr.mean())

    # pairwise kappa + AC1 + CIs
    for name, a, b in [("R1-O", r1, o), ("R1-G", r1, g), ("O-G", o, g)]:
        k = cohen_kappa(a, b); ac = gwet_ac1(a, b)
        kci = boot_ci(cohen_kappa, a, b, clusters=clusters)
        acci = boot_ci(gwet_ac1, a, b, clusters=clusters)
        res["pairwise"][name] = dict(raw_agree=float(np.mean(a == b)), cohen_kappa=k,
                                     kappa_ci=kci, gwet_ac1=ac, ac1_ci=acci)

    # Fleiss over 3 raters
    mat = np.zeros((len(ids), 2), int)
    for idx in range(len(ids)):
        for arr in (r1, o, g):
            mat[idx, arr[idx]] += 1
    fk = fleiss_kappa(mat)

    def fleiss_from_idx(sel):
        m = np.zeros((len(sel), 2), int)
        for row, idx in enumerate(sel):
            for arr in (r1, o, g):
                m[row, arr[idx]] += 1
        return fleiss_kappa(m)
    # prompt-clustered bootstrap for Fleiss CI
    uni = np.array(sorted(set(clusters.tolist())))
    memb = {c: np.where(clusters == c)[0] for c in uni}
    fk_samples = []
    for _ in range(5000):
        pick = uni[rng.integers(0, len(uni), len(uni))]
        sel = np.concatenate([memb[c] for c in pick])
        fk_samples.append(fleiss_from_idx(sel))
    fk_ci = np.percentile(fk_samples, [2.5, 97.5])
    res["fleiss"] = dict(kappa=float(fk), ci=[float(fk_ci[0]), float(fk_ci[1])])

    # author-influenced majority consensus (R1,O,G) — no ties with 3 raters
    consensus = ((r1 + o + g) >= 2).astype(int)
    res["consensus_author_influenced_rate"] = float(consensus.mean())

    # judge vs each human reference: rate diff + paired CI, kappa vs consensus
    def rate_diff(jv, hv):
        return np.mean(jv) - np.mean(hv)
    for j in JUDGES:
        jv = np.array(jvote[j]); mask = np.array(jmask[j]).astype(bool)
        entry = {"judge_rate": float(jv[mask].mean())}
        for ref_name, ref in [("R1_author", r1), ("O", o), ("G", g),
                              ("consensus_author_infl", consensus)]:
            d = float(np.mean(jv[mask]) - np.mean(ref[mask]))
            ci = boot_ci(rate_diff, jv[mask], ref[mask], clusters=clusters[mask])
            k = cohen_kappa(jv[mask], ref[mask])
            kci = boot_ci(cohen_kappa, jv[mask], ref[mask], clusters=clusters[mask])
            entry[ref_name] = dict(rate_diff=d, rate_diff_ci=ci, kappa=k, kappa_ci=kci)
        res["judge_vs_human"][JNICE[j]] = entry

    OUT_JSON.write_text(json.dumps(res, indent=2))

    L = ["# Strengthened human-reference analysis (50 items, raters R1/O/G)\n"]
    L.append(f"All bootstrap CIs are **prompt-clustered** (resampling the {n_uni} unique "
             f"perturbed prompts underlying the 50 annotation items), which is more conservative "
             f"than resampling items independently.\n")
    L.append(f"Rater appropriate-uncertainty rates: R1 (author) {r1.mean():.2f}, "
             f"O {o.mean():.2f}, G {g.mean():.2f}. Author-influenced majority consensus "
             f"{consensus.mean():.2f}.\n")
    L.append("## Pairwise agreement (Cohen's kappa + Gwet's AC1, prompt-clustered bootstrap 95% CI)\n")
    L.append("| pair | raw | Cohen kappa [95% CI] | Gwet AC1 [95% CI] |")
    L.append("|---|---|---|---|")
    for name, d in res["pairwise"].items():
        L.append(f"| {name} | {d['raw_agree']:.2f} | {d['cohen_kappa']:.2f} "
                 f"[{d['kappa_ci'][0]:.2f}, {d['kappa_ci'][1]:.2f}] | {d['gwet_ac1']:.2f} "
                 f"[{d['ac1_ci'][0]:.2f}, {d['ac1_ci'][1]:.2f}] |")
    L.append("")
    L.append(f"Fleiss' kappa (3 raters): {fk:.2f} [{fk_ci[0]:.2f}, {fk_ci[1]:.2f}]. "
             "Note Gwet's AC1 exceeds kappa for the O-G pair, i.e. the modest O-G kappa is "
             "partly a high-prevalence artifact, not raw disagreement.\n")
    L.append("## Judge minus human appropriate-uncertainty rate (same items, paired 95% CI)\n")
    L.append("Positive = judge credits appropriate uncertainty MORE often than the human "
             "reference (i.e. judge more lenient). O and G are the independent (co-primary) "
             "references; the author-influenced consensus is secondary.\n")
    L.append("| judge | judge rate | vs O | vs G | vs author-consensus |")
    L.append("|---|---|---|---|---|")
    for jn, e in res["judge_vs_human"].items():
        def cell(x):
            return f"{x['rate_diff']:+.2f} [{x['rate_diff_ci'][0]:+.2f}, {x['rate_diff_ci'][1]:+.2f}]"
        L.append(f"| {jn} | {e['judge_rate']:.2f} | {cell(e['O'])} | {cell(e['G'])} | "
                 f"{cell(e['consensus_author_infl'])} |")
    L.append("")
    L.append("All four judges are significantly more lenient than the stricter clinician O "
             "(paired CIs exclude zero). Three of four (GPT-5.5, Opus, Gemini) are also "
             "significantly more lenient than the author-influenced consensus; Grok's difference "
             "vs the consensus is directionally positive (+0.12) but its CI crosses zero "
             "([-0.02, +0.27]). Against the more lenient clinician G the gap shrinks further: only "
             "GPT-5.5 clearly separates, and Grok is directionally stricter than G (-0.04, CI "
             "crosses zero). The leniency conclusion holds firmly against the stricter clinician, "
             "is weaker against the consensus and the more lenient clinician, and does not depend "
             "on the author's labels.\n")
    OUT_MD.write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
