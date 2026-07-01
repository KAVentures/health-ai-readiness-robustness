# MedRobust

Robustness stress-test layer over MedARC MCQ benchmarks, replicating the
perturbation methodology of *"Evaluating the robustness and readiness of large
frontier models in health AI applications"* (Nature Medicine).

## Parameters

- `dataset`: base benchmark (`medqa`, `medmcqa`).
- `perturbation`: `none` (baseline), `shuffle` (option permutation), `remove_answer`
  (drop correct option, add "none of the above" sentinel), `remove_context`
  (strip vignette, add "insufficient information" sentinel).
- `shuffle_seed`: seed for the `shuffle` perturbation; vary across runs.

## Reward semantics

- `none` / `shuffle`: 1.0 iff the model selects the correct option (accuracy).
- `remove_answer` / `remove_context`: 1.0 iff the model selects the sentinel option
  (appropriate abstention). `1 - reward` is the inappropriate-confident-answer rate.

## Robustness metrics

- Δaccuracy = accuracy(none) − accuracy(shuffle): positional-bias sensitivity.
- Inappropriate-answer rate = 1 − reward under `remove_answer` / `remove_context`.
