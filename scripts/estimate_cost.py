#!/usr/bin/env python
"""Cost estimate for the full robustness study, from measured token profiles.

Token profiles below are MEASURED (avg/call) from small probe runs on
2026-06-29. Prices are ESTIMATES in USD per 1M tokens — EDIT to match your
actual contracted rates; the token volumes are the hard facts.
"""

from __future__ import annotations

# ---- Measured per-call token profiles (input, output) ----
# MedQA (MCQ), avg of `none` + `remove_answer` probes, n=5 each.
MEDQA = {
    "opus-4_8-high": (447, 107),       # NOTE: Opus output looks low; thinking tokens
    "gpt-5_5-high": (291, 916),        #   may be undercounted -> see opus_adjusted below.
    "grok-4_3": (402, 205),
    "gemini-3_1-pro-high": (295, 406),
}
# HealthBench open-ended policy call (measured on gemini; applied to all models).
HB_POLICY = (250, 1100)
# Judge call (gpt-4.1-mini) per criterion: conversation+template in, short json out.
JUDGE = (1300, 120)
HB_CRITERIA_BASELINE = 2   # consensus split ~2 criteria/example (measured)
HB_CRITERIA_PROBE = 1      # single appropriate-uncertainty criterion

# ---- Prices (USD per 1M tokens) — ESTIMATES, edit to taste ----
PRICE = {
    "opus-4_8-high": (15.0, 75.0),
    "gpt-5_5-high": (1.25, 10.0),
    "grok-4_3": (3.0, 15.0),
    "gemini-3_1-pro-high": (1.25, 10.0),
    "judge": (0.40, 1.60),  # gpt-4.1-mini
}

# ---- Matrix sizing ----
MEDQA_CONDITIONS = 4   # none, shuffle, remove_answer, remove_context
MEDQA_N = 100
HB_N = 50
MODELS = list(MEDQA.keys())


def cost(profile, price, calls):
    cin, cout = profile
    pin, pout = price
    return calls * (cin * pin + cout * pout) / 1_000_000


def main() -> None:
    rows = []
    grand = 0.0
    for m in MODELS:
        # MedQA
        medqa_calls = MEDQA_CONDITIONS * MEDQA_N
        medqa_cost = cost(MEDQA[m], PRICE[m], medqa_calls)
        # HealthBench baseline + probe (policy calls)
        hb_policy_calls = 2 * HB_N  # baseline + probe
        hb_policy_cost = cost(HB_POLICY, PRICE[m], hb_policy_calls)
        # Judge calls (charged at judge price, not policy)
        judge_calls = HB_N * HB_CRITERIA_BASELINE + HB_N * HB_CRITERIA_PROBE
        judge_cost = cost(JUDGE, PRICE["judge"], judge_calls)
        subtotal = medqa_cost + hb_policy_cost + judge_cost
        grand += subtotal
        rows.append((m, medqa_calls + hb_policy_calls, judge_calls, medqa_cost, hb_policy_cost, judge_cost, subtotal))

    print(f"{'model':22s} {'main_calls':>10s} {'judge_calls':>11s} {'medqa$':>8s} {'hb$':>7s} {'judge$':>7s} {'total$':>8s}")
    for m, mc, jc, mq, hb, jd, st in rows:
        print(f"{m:22s} {mc:>10d} {jc:>11d} {mq:>8.2f} {hb:>7.2f} {jd:>7.2f} {st:>8.2f}")
    print("-" * 80)
    print(f"{'TOTAL (measured)':22s} {'':>10s} {'':>11s} {'':>8s} {'':>7s} {'':>7s} {grand:>8.2f}")

    # Opus-thinking-adjusted scenario: assume Opus actually emits ~2500 output tokens
    # (partial use of its 16k thinking budget) instead of the suspiciously low measured 107.
    opus_adj = cost((447, 2500), PRICE["opus-4_8-high"], MEDQA_CONDITIONS * MEDQA_N) \
        + cost((250, 2500), PRICE["opus-4_8-high"], 2 * HB_N) \
        + cost(JUDGE, PRICE["judge"], HB_N * (HB_CRITERIA_BASELINE + HB_CRITERIA_PROBE))
    opus_measured = rows[0][6]
    grand_adj = grand - opus_measured + opus_adj
    print(f"{'TOTAL (Opus thinking-adjusted)':30s} {grand_adj:>.2f}   "
          f"(Opus {opus_measured:.2f} -> {opus_adj:.2f})")


if __name__ == "__main__":
    main()
