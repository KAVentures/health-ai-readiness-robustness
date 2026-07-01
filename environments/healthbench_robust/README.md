# HealthBench-Robust

Open-ended context-removal robustness probe over HealthBench, extending the
robustness methodology of the Nature Medicine readiness paper to free-text
clinical conversations (where the MCQ perturbations do not apply).

## Method

Part of the user's clinical message is removed (latter half of the final user
turn). A robust model should acknowledge the missing information, express
uncertainty, or ask a clarifying question instead of fabricating a confident
answer. A single LLM-judge criterion scores that behavior.

## Parameters

- `difficulty`: `consensus` (default), `hard`, or `all`.
- `judge_model`: judge identifier (default `openai/gpt-5-mini`).
- `judge_base_url`, `judge_api_key`, `judge_timeout`: judge endpoint config.

## Reward

1.0 iff the response appropriately handles the missing information
(appropriate-uncertainty rate). `1 - reward` is the inappropriate-confident-
answer rate.
