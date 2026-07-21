#!/usr/bin/env python3
"""Judge-severity-adjusted self-preference analysis.

The raw self-preference statistic reported in the paper (own-provider judge rate
minus mean of the three peer judges, on the same items) conflates two things:
(a) a judge's *general* severity/leniency across all subjects, and
(b) genuine extra preference for the judge's own provider's outputs.

This script isolates (b) with three mutually supporting analyses over the
800-vote grid in runs/judge_panel/votes.jsonl (4 subjects x 50 items x 4 judges,
2 votes missing where the xAI judge hit provider moderation):

1. Descriptive difference-in-differences (DiD) per subject model:
     [own judge on self - own judge on other subjects]
   - [peer judges on self - peer judges on other subjects]
   This nets out both the own judge's general leniency and the subject's
   general quality.

2. Vote-level logistic regression (numpy IRLS, no external deps):
     logit P(vote=appropriate) = subject-model FE + judge FE + beta * same_provider
   with a single shared same-provider coefficient, and a variant with a
   GPT-5.5-specific same-provider term. CIs via prompt-clustered bootstrap
   (resampling the 50 prompt_ids, preserving all votes for a resampled prompt).
   Note: these are subject-model and judge fixed effects, NOT per-prompt/item
   fixed effects.

3. Exact permutation test: under H0 (no same-provider association beyond judge
   severity), the labelling of which judge is "own" for each subject is
   exchangeable as a BIJECTION. There are only 4! = 24 ways to assign the four
   judges to the four subjects as own-judges, so we enumerate all 24 exactly and
   refit; the p-value is the exact fraction of mappings whose |shared coefficient|
   >= the observed one (deterministic, not Monte Carlo).

Outputs: runs/judge_panel/self_preference_adjusted.{md,json}
"""
import json
import math
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VOTES = ROOT / "runs/judge_panel/votes.jsonl"
OUT_MD = ROOT / "runs/judge_panel/self_preference_adjusted.md"
OUT_JSON = ROOT / "runs/judge_panel/self_preference_adjusted.json"

SUBJ_PROVIDER = {
    "gpt-5_5-high": "openai",
    "opus-4_8-high": "anthropic",
    "grok-4_3": "xai",
    "gemini-3_5-flash": "google",
}
NICE = {
    "gpt-5_5-high": "GPT-5.5",
    "opus-4_8-high": "Opus 4.8",
    "grok-4_3": "Grok 4.3",
    "gemini-3_5-flash": "Gemini 3.5 Flash",
}
JUDGES = ["openai", "anthropic", "xai", "google"]
JNICE = {"openai": "GPT-5.5", "anthropic": "Opus 4.8", "xai": "Grok 4.3", "google": "Gemini 3.5 Flash"}

rng = np.random.default_rng(20260720)


def load_long():
    rows = [json.loads(l) for l in open(VOTES)]
    recs = []  # (subject, judge, prompt_id, y, same_provider)
    for r in rows:
        s = r["subject_model"]
        for j, v in r["votes"].items():
            if v is None:
                continue
            recs.append((s, j, r["prompt_id"], int(bool(v)), int(SUBJ_PROVIDER[s] == j)))
    return recs


def did_table(recs):
    """Descriptive DiD per subject."""
    # rate[subject][judge]
    agg = {}
    for s, j, _, y, _ in recs:
        agg.setdefault((s, j), []).append(y)
    rate = {k: float(np.mean(v)) for k, v in agg.items()}
    out = {}
    for s in SUBJ_PROVIDER:
        own = SUBJ_PROVIDER[s]
        others = [t for t in SUBJ_PROVIDER if t != s]
        own_on_self = rate[(s, own)]
        own_on_others = float(np.mean([rate[(t, own)] for t in others]))
        peers = [j for j in JUDGES if j != own]
        peer_on_self = float(np.mean([rate[(s, j)] for j in peers]))
        peer_on_others = float(np.mean([rate[(t, j)] for t in others for j in peers if (t, j) in rate]))
        raw = own_on_self - peer_on_self
        did = (own_on_self - own_on_others) - (peer_on_self - peer_on_others)
        out[s] = dict(own_on_self=own_on_self, own_on_others=own_on_others,
                      peer_on_self=peer_on_self, peer_on_others=peer_on_others,
                      raw_self_pref=raw, did_self_pref=did)
    return out


def design(recs, gpt_specific=False, own_override=None):
    """Build design matrix: intercept + subject FE (3) + judge FE (3) + same-provider term(s).

    own_override: optional dict subject->judge to use instead of the true own-provider
    (for the permutation test)."""
    subs = list(SUBJ_PROVIDER)
    n = len(recs)
    p = 1 + 3 + 3 + (2 if gpt_specific else 1)
    X = np.zeros((n, p))
    y = np.zeros(n)
    for i, (s, j, _, yy, _) in enumerate(recs):
        y[i] = yy
        X[i, 0] = 1.0
        si = subs.index(s)
        if si < 3:
            X[i, 1 + si] = 1.0
        ji = JUDGES.index(j)
        if ji < 3:
            X[i, 4 + ji] = 1.0
        own = (own_override[s] if own_override else SUBJ_PROVIDER[s])
        same = int(own == j)
        if gpt_specific:
            X[i, 7] = same * (1 if s != "gpt-5_5-high" else 0)
            X[i, 8] = same * (1 if s == "gpt-5_5-high" else 0)
        else:
            X[i, 7] = same
    return X, y


def fit_logistic(X, y, ridge=1e-6, iters=100):
    """IRLS with a tiny ridge for stability. Returns beta or None on failure."""
    n, p = X.shape
    b = np.zeros(p)
    for _ in range(iters):
        eta = X @ b
        mu = 1 / (1 + np.exp(-np.clip(eta, -30, 30)))
        w = np.clip(mu * (1 - mu), 1e-9, None)
        z = eta + (y - mu) / w
        A = (X * w[:, None]).T @ X + ridge * np.eye(p)
        bn = np.linalg.solve(A, (X * w[:, None]).T @ z)
        if np.max(np.abs(bn - b)) < 1e-10:
            b = bn
            break
        b = bn
    return b


def cluster_bootstrap(recs, gpt_specific, B=2000):
    """Bootstrap resampling the 50 prompt_ids (clusters)."""
    ids = sorted({r[2] for r in recs})
    by_id = {}
    for r in recs:
        by_id.setdefault(r[2], []).append(r)
    stats = []
    for _ in range(B):
        sample_ids = rng.choice(len(ids), size=len(ids), replace=True)
        boot = [r for k in sample_ids for r in by_id[ids[k]]]
        X, y = design(boot, gpt_specific=gpt_specific)
        b = fit_logistic(X, y)
        stats.append(b[-1] if not gpt_specific else (b[7], b[8]))
    return np.array(stats)


def permutation_test(recs):
    """Exact permutation test over all 4! = 24 bijections assigning the four judges
    to the four subjects as 'own' judges. Deterministic (full enumeration)."""
    import itertools
    subs = list(SUBJ_PROVIDER)
    X, y = design(recs)
    obs = fit_logistic(X, y)[7]
    perm = []
    for order in itertools.permutations(range(len(JUDGES))):
        ov = {subs[i]: JUDGES[order[i]] for i in range(len(subs))}
        Xp, yp = design(recs, own_override=ov)
        perm.append(fit_logistic(Xp, yp)[7])
    perm = np.array(perm)
    # two-sided exact p: fraction of the 24 mappings at least as extreme as observed
    pval = float(np.mean(np.abs(perm) >= abs(obs) - 1e-12))
    return obs, pval, perm


def pct(x):
    return f"{x:+.3f}"


def main():
    recs = load_long()
    n = len(recs)
    did = did_table(recs)

    # Shared same-provider effect
    X, y = design(recs)
    beta_shared = fit_logistic(X, y)[7]
    boot_shared = cluster_bootstrap(recs, gpt_specific=False)
    ci_shared = np.percentile(boot_shared, [2.5, 97.5])

    # GPT-specific term
    Xg, yg = design(recs, gpt_specific=True)
    bg = fit_logistic(Xg, yg)
    beta_other, beta_gpt = bg[7], bg[8]
    boot_g = cluster_bootstrap(recs, gpt_specific=True)
    ci_other = np.percentile(boot_g[:, 0], [2.5, 97.5])
    ci_gpt = np.percentile(boot_g[:, 1], [2.5, 97.5])

    obs, pval, _ = permutation_test(recs)

    # Convert GPT log-odds effect to a probability-scale effect at GPT-5.5's baseline
    # (peer-judged rate ~0.70)
    p0 = 0.70
    lo = math.log(p0 / (1 - p0))
    gpt_prob_effect = 1 / (1 + math.exp(-(lo + beta_gpt))) - p0

    res = dict(
        n_votes=n,
        did={NICE[s]: v for s, v in did.items()},
        shared_same_provider_logodds=float(beta_shared),
        shared_ci95=[float(c) for c in ci_shared],
        gpt_same_provider_logodds=float(beta_gpt),
        gpt_ci95=[float(c) for c in ci_gpt],
        nongpt_same_provider_logodds=float(beta_other),
        nongpt_ci95=[float(c) for c in ci_other],
        permutation_p_shared=pval,
        gpt_prob_scale_effect_at_p0_070=float(gpt_prob_effect),
    )
    OUT_JSON.write_text(json.dumps(res, indent=2))

    lines = []
    lines.append("# Judge-severity-adjusted self-preference\n")
    lines.append(f"Votes analysed: {n} (800 minus 2 xAI-judge moderation drops).\n")
    lines.append("## 1. Descriptive difference-in-differences (probability scale)\n")
    lines.append("Raw = own judge on self − peer judges on self (the paper's original statistic).")
    lines.append("DiD additionally nets out the own judge's general leniency on *other* subjects:")
    lines.append("DiD = (own on self − own on others) − (peers on self − peers on others).\n")
    lines.append("| subject | own judge on self | own judge on others | peers on self | peers on others | raw self-pref | severity-adjusted DiD |")
    lines.append("|---|---|---|---|---|---|---|")
    for s in SUBJ_PROVIDER:
        d = did[s]
        lines.append(
            f"| {NICE[s]} | {d['own_on_self']:.3f} | {d['own_on_others']:.3f} | "
            f"{d['peer_on_self']:.3f} | {d['peer_on_others']:.3f} | "
            f"{pct(d['raw_self_pref'])} | {pct(d['did_self_pref'])} |")
    lines.append("")
    lines.append("## 2. Fixed-effects logistic regression (subject FE + judge FE + same-provider)\n")
    lines.append(f"- Shared same-provider coefficient: **{beta_shared:+.3f} log-odds** "
                 f"(95% prompt-clustered bootstrap CI [{ci_shared[0]:+.3f}, {ci_shared[1]:+.3f}])")
    lines.append(f"- GPT-5.5-specific same-provider coefficient: **{beta_gpt:+.3f} log-odds** "
                 f"(95% CI [{ci_gpt[0]:+.3f}, {ci_gpt[1]:+.3f}])")
    lines.append(f"- Same-provider coefficient for the other three subjects: {beta_other:+.3f} "
                 f"(95% CI [{ci_other[0]:+.3f}, {ci_other[1]:+.3f}])")
    lines.append(f"- GPT-5.5 effect on the probability scale at its peer-judged baseline (0.70): "
                 f"{gpt_prob_effect:+.3f}")
    lines.append("")
    lines.append("## 3. Exact permutation test (all 24 bijective own-judge assignments)\n")
    lines.append(f"- Observed shared coefficient {obs:+.3f}, exact two-sided p = {pval:.4f} "
                 f"({int(round(pval*24))}/24 mappings at least as extreme)")
    lines.append("")
    lines.append("Interpretation: the raw +0.16 for GPT-5.5 conflates the GPT-5.5 judge's general "
                 "leniency with genuine self-preference; the DiD and regression isolate the latter. "
                 "Report the adjusted values as primary and the raw gap as descriptive.\n")
    OUT_MD.write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
