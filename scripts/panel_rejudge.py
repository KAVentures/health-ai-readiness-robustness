#!/usr/bin/env python
"""Cross-provider judge panel for the HealthBench context-removal probe.

Re-judges the *already-saved* probe completions with multiple providers so we can
report (a) per-judge appropriate-uncertainty rates, (b) inter-rater agreement
(Fleiss' kappa), and (c) a leave-one-provider-out self-preference check (does a
provider's judge rate its own provider's subject model more leniently?).

We do NOT re-sample the subject models — only re-score saved text — so this is
cheap. GPT-5.5's votes are taken from the saved run (authoritative; they define
the numbers in the paper); the other three providers are called fresh on the
identical (perturbed conversation + completion) inputs.

Outputs (under --out, default runs/judge_panel/):
  votes.jsonl        one row per (subject_model, item) with each judge's binary vote
  panel_summary.json machine-readable summary (per-judge rates, kappa, self-pref)
  panel_summary.md   human-readable summary
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path

# Reuse the exact judge template / criterion / parsing from the env so the panel
# scores identical inputs to the original run.
import sys

ENV_DIR = Path(__file__).resolve().parent.parent / "environments" / "healthbench_robust"
sys.path.insert(0, str(ENV_DIR))
from healthbench_robust import JUDGE_TEMPLATE, UNCERTAINTY_CRITERION, _format_conversation, _parse_json  # noqa: E402

from medarc_verifiers.judging import MultiJudge  # noqa: E402

# Canonical probe runs (gpt-5.5 judge, n=50) that match the paper's HealthBench table.
SUBJECT_RUNS = {
    "opus-4_8-high": "environments/healthbench_robust/outputs/evals/healthbench_robust--claude-opus-4-8/b7e3a9ca/results.jsonl",
    "gpt-5_5-high": "environments/healthbench_robust/outputs/evals/healthbench_robust--gpt-5.5/a8036c59/results.jsonl",
    "grok-4_3": "environments/healthbench_robust/outputs/evals/healthbench_robust--grok-4.3/ea8170e2/results.jsonl",
    "gemini-3_5-flash": "environments/healthbench_robust/outputs/evals/healthbench_robust--gemini-3.5-flash/1bbb4127/results.jsonl",
}

# Which provider each subject model belongs to (for the self-preference check).
SUBJECT_PROVIDER = {
    "opus-4_8-high": "anthropic",
    "gpt-5_5-high": "openai",
    "grok-4_3": "xai",
    "gemini-3_5-flash": "google",
}

# The three judges we call fresh (provider -> (model, base_url, api_key_env)).
# Anthropic is reached through its OpenAI-compatible endpoint so the OpenAI SDK works.
FRESH_JUDGES = {
    "anthropic": ("claude-opus-4-8", "https://api.anthropic.com/v1/", "ANTHROPIC_API_KEY"),
    "xai": ("grok-4.3", "https://api.x.ai/v1", "XAI_API_KEY"),
    "google": ("gemini-3.5-flash", "https://generativelanguage.googleapis.com/v1beta/openai", "GOOGLE_API_KEY"),
}
# GPT-5.5 (openai) votes come from the saved run, not a fresh call.
ALL_PROVIDERS = ["openai", "anthropic", "xai", "google"]


def build_full_prompt(record: dict) -> str:
    prompt = record["prompt"]
    completion = record["completion"]
    raw_completion = completion[-1].get("content", "") if isinstance(completion, list) and completion else str(completion)
    conversation = _format_conversation(prompt, raw_completion)
    return JUDGE_TEMPLATE.replace("<<conversation>>", conversation).replace("<<rubric_item>>", UNCERTAINTY_CRITERION)


def parse_met(raw: str | None) -> bool | None:
    if not raw:
        return None
    parsed = _parse_json(str(raw))
    if isinstance(parsed, dict) and "criteria_met" in parsed:
        return bool(parsed.get("criteria_met"))
    return None


async def main_async(args) -> None:
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    # Build one MultiJudge across the three fresh providers.
    providers = list(FRESH_JUDGES.keys())
    models = [FRESH_JUDGES[p][0] for p in providers]
    base_urls = [FRESH_JUDGES[p][1] for p in providers]
    api_keys = []
    for p in providers:
        key = os.environ.get(FRESH_JUDGES[p][2])
        if not key:
            raise SystemExit(f"Missing env var {FRESH_JUDGES[p][2]} for judge provider {p}")
        api_keys.append(key)

    judge = MultiJudge.from_env_args(
        judge_model=models,
        judge_base_url=base_urls,
        judge_api_key=api_keys,
        judge_prompt="{question}",
        judge_timeout=args.timeout,
    )

    sem = asyncio.Semaphore(args.concurrency)
    rows: list[dict] = []
    errors: dict[str, int] = {p: 0 for p in providers}

    async def judge_one(subject: str, idx: int, record: dict) -> dict:
        full_prompt = build_full_prompt(record)
        gpt55_vote = bool(record.get("reward", 0.0) >= 0.5)  # saved gpt-5.5 vote
        votes = {"openai": gpt55_vote}
        async with sem:
            results = await judge.judge([{"role": "user", "content": full_prompt}], "", "", {})
        for r in results:
            prov = providers[r.index]
            met = parse_met(r.raw)
            if met is None:
                errors[prov] += 1
            votes[prov] = met
        return {
            "subject_model": subject,
            "item": idx,
            "prompt_id": record.get("info", {}).get("prompt_id"),
            "theme": record.get("info", {}).get("theme"),
            "votes": votes,
        }

    tasks = []
    for subject, path in SUBJECT_RUNS.items():
        recs = [json.loads(l) for l in open(path)]
        for idx, rec in enumerate(recs):
            tasks.append(judge_one(subject, idx, rec))
    rows = await asyncio.gather(*tasks)
    rows.sort(key=lambda r: (r["subject_model"], r["item"]))

    with open(out / "votes.jsonl", "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")

    summarize(rows, errors, out)


def _rate(votes_for_provider: list[bool | None]) -> tuple[float | None, int]:
    valid = [v for v in votes_for_provider if v is not None]
    if not valid:
        return None, 0
    return sum(1 for v in valid if v) / len(valid), len(valid)


def fleiss_kappa(rows: list[dict]) -> tuple[float | None, int]:
    """Fleiss' kappa over items rated by all judges (binary categories)."""
    n_per_item = len(ALL_PROVIDERS)
    table = []  # each row: [n_true, n_false] for items with complete ratings
    for r in rows:
        vals = [r["votes"].get(p) for p in ALL_PROVIDERS]
        if any(v is None for v in vals):
            continue
        n_true = sum(1 for v in vals if v)
        table.append([n_true, n_per_item - n_true])
    N = len(table)
    if N == 0:
        return None, 0
    n = n_per_item
    # P_i per item
    Pi = [(row[0] ** 2 + row[1] ** 2 - n) / (n * (n - 1)) for row in table]
    P_bar = sum(Pi) / N
    # category marginals
    p_true = sum(row[0] for row in table) / (N * n)
    p_false = 1 - p_true
    P_e = p_true ** 2 + p_false ** 2
    if P_e >= 1.0:
        return 1.0, N
    kappa = (P_bar - P_e) / (1 - P_e)
    return kappa, N


def mean_pairwise_agreement(rows: list[dict]) -> float | None:
    """Average over judge pairs of the fraction of items they agree on."""
    pairs = []
    provs = ALL_PROVIDERS
    for i in range(len(provs)):
        for j in range(i + 1, len(provs)):
            a, b = provs[i], provs[j]
            agree = tot = 0
            for r in rows:
                va, vb = r["votes"].get(a), r["votes"].get(b)
                if va is None or vb is None:
                    continue
                tot += 1
                if va == vb:
                    agree += 1
            if tot:
                pairs.append(agree / tot)
    return sum(pairs) / len(pairs) if pairs else None


def summarize(rows: list[dict], errors: dict[str, int], out: Path) -> None:
    # Per-judge appropriate-uncertainty rate, overall and per subject model.
    subjects = sorted({r["subject_model"] for r in rows})
    per_judge_overall = {}
    for p in ALL_PROVIDERS:
        rate, n = _rate([r["votes"].get(p) for r in rows])
        per_judge_overall[p] = {"rate": rate, "n": n}

    per_subject = {}
    for s in subjects:
        srows = [r for r in rows if r["subject_model"] == s]
        per_subject[s] = {}
        for p in ALL_PROVIDERS:
            rate, n = _rate([r["votes"].get(p) for r in srows])
            per_subject[s][p] = {"rate": rate, "n": n}

    # Leave-one-provider-out self-preference: for each subject model, compare its
    # own-provider judge rate vs the mean of the other-provider judges on that
    # same subject. Positive delta = own judge is more lenient (more "appropriate
    # uncertainty" credited) than peers => possible self-preference.
    self_pref = {}
    for s in subjects:
        own = SUBJECT_PROVIDER[s]
        own_rate = per_subject[s][own]["rate"]
        others = [per_subject[s][p]["rate"] for p in ALL_PROVIDERS if p != own and per_subject[s][p]["rate"] is not None]
        peer_mean = sum(others) / len(others) if others else None
        self_pref[s] = {
            "own_provider": own,
            "own_judge_rate": own_rate,
            "peer_mean_rate": peer_mean,
            "delta_self_minus_peer": (own_rate - peer_mean) if (own_rate is not None and peer_mean is not None) else None,
        }

    kappa, kappa_n = fleiss_kappa(rows)
    mpa = mean_pairwise_agreement(rows)

    summary = {
        "n_items_total": len(rows),
        "per_judge_overall_appropriate_uncertainty": per_judge_overall,
        "per_subject_per_judge": per_subject,
        "self_preference": self_pref,
        "fleiss_kappa": {"value": kappa, "n_complete_items": kappa_n},
        "mean_pairwise_agreement": mpa,
        "judge_errors": errors,
    }
    with open(out / "panel_summary.json", "w") as fh:
        json.dump(summary, fh, indent=2)

    def f(x):
        return "—" if x is None else f"{x:.3f}"

    short = {"openai": "GPT-5.5", "anthropic": "Opus 4.8", "xai": "Grok 4.3", "google": "Gemini 3.5 Flash"}
    smodel = {"opus-4_8-high": "Opus 4.8", "gpt-5_5-high": "GPT-5.5", "grok-4_3": "Grok 4.3", "gemini-3_5-flash": "Gemini 3.5 Flash"}

    lines = []
    lines.append("# Cross-provider judge panel — open-ended context-removal probe\n")
    lines.append(f"Items judged: {len(rows)} (4 subject models x 50). GPT-5.5 votes from the saved run; "
                 "Opus/Grok/Gemini called fresh on identical inputs.\n")
    lines.append("Metric: appropriate-uncertainty rate (fraction of items each judge marks the criterion met).\n")

    lines.append("\n## Inter-rater reliability\n")
    lines.append(f"- Fleiss' kappa (4 judges, {kappa_n} complete items): **{f(kappa)}**")
    lines.append(f"- Mean pairwise agreement: **{f(mpa)}**")
    lines.append(f"- Judge parse/call errors: " + ", ".join(f"{short[p]}={errors.get(p,0)}" for p in providers_with_errors(errors)) or "- Judge errors: none")

    lines.append("\n## Appropriate-uncertainty rate by judge (rows = subject model, cols = judge)\n")
    header = "| subject \\ judge | " + " | ".join(short[p] for p in ALL_PROVIDERS) + " |"
    lines.append(header)
    lines.append("|" + "---|" * (len(ALL_PROVIDERS) + 1))
    for s in [k for k in SUBJECT_RUNS if k in per_subject]:
        cells = " | ".join(f(per_subject[s][p]["rate"]) for p in ALL_PROVIDERS)
        lines.append(f"| {smodel[s]} | {cells} |")
    overall_cells = " | ".join(f(per_judge_overall[p]["rate"]) for p in ALL_PROVIDERS)
    lines.append(f"| **all subjects** | {overall_cells} |")

    lines.append("\n## Self-preference (leave-one-provider-out)\n")
    lines.append("For each subject model: its own-provider judge's rate minus the mean of the other three judges' "
                 "rates on the same items. Positive = own judge credits more appropriate-uncertainty than peers.\n")
    lines.append("| subject model | own provider | own-judge rate | peer-mean rate | delta (self - peer) |")
    lines.append("|---|---|---|---|---|")
    for s in [k for k in SUBJECT_RUNS if k in self_pref]:
        d = self_pref[s]
        lines.append(f"| {smodel[s]} | {short[d['own_provider']]} | {f(d['own_judge_rate'])} | "
                     f"{f(d['peer_mean_rate'])} | {f(d['delta_self_minus_peer'])} |")

    (out / "panel_summary.md").write_text("\n".join(lines) + "\n")
    print((out / "panel_summary.md").read_text())


def providers_with_errors(errors: dict[str, int]) -> list[str]:
    return [p for p, c in errors.items() if c] or list(errors.keys())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="runs/judge_panel")
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--timeout", type=int, default=300)
    args = ap.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
