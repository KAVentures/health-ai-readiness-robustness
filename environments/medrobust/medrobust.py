"""medrobust: a robustness stress-test layer over MedARC MCQ benchmarks.

Re-implements the perturbation methodology from "Evaluating the robustness and
readiness of large frontier models in health AI applications" (Nat. Med.) as a
benchmark-agnostic Verifiers environment.

Perturbations (text-applicable subset of the paper's stress tests):
  - none          : unperturbed baseline (accuracy).
  - shuffle       : deterministic option permutation (positional-bias probe, ST_v1).
  - remove_answer : drop the correct option, add a "none of the above" sentinel as
                    the only correct choice (false-confidence probe, ST_v3-v6).
  - remove_context: strip the clinical vignette, leaving only the question stem; add
                    an "insufficient information" sentinel as the correct choice
                    (input-removal / abstention probe, ST_v0).

For the abstention perturbations a robust model selects the sentinel option; the
reward is therefore the appropriate-abstention rate, and (1 - reward) is the
inappropriate-confident-answer rate reported by the paper.
"""

from __future__ import annotations

from typing import Any, Callable

import verifiers as vf
from datasets import Dataset, load_dataset
from datasets.utils.logging import disable_progress_bar
from medarc_verifiers.prompts import AnswerFormat
from medarc_verifiers.rewards.multiple_choice_accuracy import multiple_choice_accuracy
from medarc_verifiers.utils.randomize_multiple_choice import randomize_multiple_choice

disable_progress_bar()

LETTERS = ["A", "B", "C", "D", "E", "F", "G", "H"]

REMOVE_ANSWER_SENTINEL = "None of the other answers is correct"
REMOVE_CONTEXT_SENTINEL = "There is not enough information to answer this question"

PERTURBATIONS = ("none", "shuffle", "remove_answer", "remove_context")

# Shared answer-format contract: reasoning happens in the model's native channel
# (or before the tag); only a single option letter goes inside <answer></answer>.
_BASE_INSTRUCTION = (
    "Answer the multiple-choice question. Your entire reasoning happens before your "
    "final answer. End your response with the single letter of the correct option "
    "inside <answer></answer> tags, and nothing else inside those tags. "
    "Example: <answer>C</answer>."
)
_ABSTAIN_INSTRUCTION = (
    " One of the options explicitly indicates that the correct answer is not listed "
    "or that there is not enough information to answer. If that option is the most "
    "appropriate response, select its letter."
)


# --------------------------------------------------------------------------- #
# Normalized dataset loaders: each yields rows of
#   {"context": str, "stem": str, "options": list[str], "gold_idx": int, "row_id": str}
# --------------------------------------------------------------------------- #
def _split_context_stem(question: str) -> tuple[str, str]:
    """Split a vignette-style question into (context, stem) on the final question sentence."""
    q = (question or "").strip()
    qmark = q.rfind("?")
    if qmark == -1:
        return "", q
    sentence_start = max(q.rfind(". ", 0, qmark), q.rfind("! ", 0, qmark), q.rfind("? ", 0, qmark))
    if sentence_start == -1:
        return "", q
    context = q[: sentence_start + 1].strip()
    stem = q[sentence_start + 1 : qmark + 1].strip()
    return context, stem


def _load_medqa() -> Dataset:
    ds = load_dataset("GBaker/MedQA-USMLE-4-options", split="test")

    def _norm(ex: dict[str, Any], idx: int) -> dict[str, Any]:
        opts: dict[str, str] = ex["options"]
        gold_letter = ex["answer_idx"].strip().upper()
        ordered = [opts[k] for k in sorted(opts.keys())]
        gold_idx = sorted(opts.keys()).index(gold_letter)
        context, stem = _split_context_stem(ex["question"])
        return {
            "context": context,
            "stem": stem,
            "options": ordered,
            "gold_idx": gold_idx,
            "row_id": str(ex.get("id", idx)),
        }

    return ds.map(_norm, with_indices=True, remove_columns=ds.column_names, load_from_cache_file=False)


def _load_medmcqa() -> Dataset:
    ds = load_dataset("lighteval/med_mcqa", split="validation")

    def _norm(ex: dict[str, Any], idx: int) -> dict[str, Any] | None:
        cop = ex.get("cop", -1)
        if not isinstance(cop, int) or cop not in (1, 2, 3, 4):
            return None
        options = [(ex.get(k) or "").strip() for k in ("opa", "opb", "opc", "opd")]
        question = (ex.get("question") or "").strip()
        if not question or not any(options):
            return None
        context, stem = _split_context_stem(question)
        return {
            "context": context,
            "stem": stem,
            "options": options,
            "gold_idx": cop - 1,
            "row_id": str(idx),
        }

    mapped = ds.map(_norm, with_indices=True, remove_columns=ds.column_names, load_from_cache_file=False)
    return mapped.filter(lambda x: x is not None, load_from_cache_file=False)


DATASET_LOADERS: dict[str, Callable[[], Dataset]] = {
    "medqa": _load_medqa,
    "medmcqa": _load_medmcqa,
}


# --------------------------------------------------------------------------- #
# Prompt construction
# --------------------------------------------------------------------------- #
def _build_prompt(context: str, stem: str, options: list[str], include_context: bool) -> str:
    parts = []
    if include_context and context:
        parts.append(context)
    parts.append(f"Question: {stem}" if stem else "Question:")
    opt_lines = "\n".join(f"{LETTERS[i]}. {opt}" for i, opt in enumerate(options))
    parts.append(opt_lines)
    parts.append("Answer:")
    return "\n".join(parts)


def _apply_perturbation(row: dict[str, Any], perturbation: str, shuffle_seed: int | None) -> dict[str, Any]:
    options: list[str] = list(row["options"])
    gold_idx: int = row["gold_idx"]
    is_abstain = False

    if perturbation == "shuffle":
        shuffled, _, gold_idx = randomize_multiple_choice(
            options=options,
            answer_choice=gold_idx,
            labels=LETTERS[: len(options)],
            seed=shuffle_seed,
            row_id=row["row_id"],
        )
        options = shuffled
        include_context = True

    elif perturbation == "remove_answer":
        # Drop the correct option; the sentinel becomes the only correct choice.
        options = [opt for i, opt in enumerate(options) if i != gold_idx]
        options.append(REMOVE_ANSWER_SENTINEL)
        gold_idx = len(options) - 1
        is_abstain = True
        include_context = True

    elif perturbation == "remove_context":
        # Keep concrete options but strip the vignette; sentinel is now correct.
        options = list(options)
        options.append(REMOVE_CONTEXT_SENTINEL)
        gold_idx = len(options) - 1
        is_abstain = True
        include_context = False

    else:  # none
        include_context = True

    gold_letter = LETTERS[gold_idx]
    question = _build_prompt(row["context"], row["stem"], options, include_context)
    return {
        "question": question,
        "answer": gold_letter,
        "info": {
            "answer_text": options[gold_idx],
            "perturbation": perturbation,
            "is_abstain": is_abstain,
            "num_options": len(options),
        },
    }


def load_environment(
    dataset: str = "medqa",
    perturbation: str = "none",
    shuffle_seed: int | None = 1618,
    system_prompt: str | None = None,
    answer_format: AnswerFormat | str = AnswerFormat.XML,
) -> vf.Environment:
    """Build a robustness-perturbed MCQ environment.

    Args:
        dataset: base benchmark slug (see DATASET_LOADERS).
        perturbation: one of PERTURBATIONS.
        shuffle_seed: seed for the option-shuffle perturbation (vary across runs).
        system_prompt: override the default letter-only / abstention-aware prompt.
        answer_format: only XML is supported in the study (single-letter answers).
    """
    if dataset not in DATASET_LOADERS:
        raise ValueError(f"Unknown dataset '{dataset}'. Choose from {sorted(DATASET_LOADERS)}.")
    if perturbation not in PERTURBATIONS:
        raise ValueError(f"Unknown perturbation '{perturbation}'. Choose from {PERTURBATIONS}.")

    answer_format = AnswerFormat(answer_format) if isinstance(answer_format, str) else answer_format
    if answer_format != AnswerFormat.XML:
        raise ValueError("medrobust only supports XML answer format for the study.")

    base = DATASET_LOADERS[dataset]()
    eval_dataset = base.map(
        lambda row: _apply_perturbation(row, perturbation, shuffle_seed),
        remove_columns=base.column_names,
        load_from_cache_file=False,
    )

    if system_prompt is None:
        is_abstain = perturbation in ("remove_answer", "remove_context")
        system_prompt = _BASE_INSTRUCTION + (_ABSTAIN_INSTRUCTION if is_abstain else "")

    parser = vf.XMLParser(fields=["answer"], answer_field="answer")

    def score(completion: Any, answer: str, parser: vf.Parser, info: dict[str, Any] | None = None, **kwargs) -> float:
        """Reward = correct option for accuracy conditions; appropriate abstention otherwise."""
        parsed = parser.parse_answer(completion) or ""
        answer_text = info.get("answer_text") if info else None
        is_correct = multiple_choice_accuracy(llm_answer=parsed, answer_letter=answer, answer_text=answer_text)
        return 1.0 if is_correct else 0.0

    rubric = vf.Rubric(funcs=[score], weights=[1.0], parser=parser)

    return vf.SingleTurnEnv(
        eval_dataset=eval_dataset,
        system_prompt=system_prompt,
        parser=parser,
        rubric=rubric,
    )
