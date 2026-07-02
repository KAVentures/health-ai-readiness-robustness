# Human-validity annotation — provenance and rater identities

This directory holds the blinded 50-item human-validity subsample used in §3.5 of the
paper (judge validity against a human reference). This note documents exactly who
produced each label file, how the files map to one another, and the conflict of
interest involved, so the released artifact is self-consistent and independently
auditable.

## Raters

The human reference is a **three-rater panel**. Every rater labeled the *same* 50
blinded items (`annotation_sheet.md` / `key.json`), independently, using the single
appropriate-uncertainty criterion in `packets/CLINICIAN_HANDOFF.md`. Model identity and
all machine (LLM-judge) verdicts were hidden; items were in randomized order.

| rater ID | who | label file | appropriate-uncertainty rate |
|---|---|---|---|
| `R1` | **the author** (Koyar Afrasyab, M.D. — a physician) | `human_labels.csv` | 0.54 |
| `O`  | **independent clinician** (de-identified by initial) | `labels_O.csv` | 0.52 |
| `G`  | **independent clinician** (de-identified by initial) | `labels_G.csv` | 0.70 |

The two independent clinicians (`O`, `G`) have **no financial or employment ties** to
the evaluated model providers (OpenAI, Anthropic, xAI, Google) or to Kinvectum AB, and
no relationship to the author beyond volunteering for this annotation. They are
de-identified by initial at their request; identifying details can be provided to
editors/reviewers in confidence.

## Conflict of interest (disclosed)

One of the three raters (`R1`) is the **author of the study**. This is a conflict of
interest: an author validating their own study can bias the human reference toward the
study's conclusion. We disclose and bound it rather than hide it:

- Every rater's labels are released separately (this directory), not just a pooled
  number.
- The author (`R1`) and clinician `O` agree on **47/50 items** (Cohen's κ = 0.88), so
  the majority-vote **consensus is author-influenced** — it tracks the author's labels
  almost exactly and is *not* independent of the author. The paper reports the consensus
  as a *corroborated author reference*, not an author-independent one.
- The paper's central human-validity conclusion — that every LLM judge is systematically
  more lenient than the human raters — is shown to hold on the **two independent
  clinicians' labels alone** (`O` = 0.52, `G` = 0.70; both at or below every LLM judge's
  0.66–0.84), i.e. without relying on the author's labels.

A larger, fully external multi-clinician adjudication with **no author participation**
is the ideal design; it was not reached here and is flagged as the primary follow-up
(paper §5).

## File map and the `R2`/`R3` packet templates

`make_annotator_packets.py` generates generic, blank, blinded packets with slot IDs
`R2`, `R3`, … to hand to additional raters. Those templates are included for
reproducibility:

- `packets/R2/`, `packets/R3/` — the blank packet templates (`INSTRUCTIONS.md`,
  `annotation_sheet.md`, and an **empty** `labels_R2.csv` / `labels_R3.csv`). These are
  the *unfilled hand-out forms*, not returned data. They are intentionally empty.
- The two independent clinicians returned their completed labels, which are stored under
  their anonymized initials as **`labels_O.csv`** and **`labels_G.csv`** (not as
  `labels_R2.csv` / `labels_R3.csv`). The scored analysis uses `R1` (=`human_labels.csv`),
  `O`, and `G`.

So: the empty `packets/R2,R3` CSVs and the filled `labels_O,G.csv` are **not** a
mismatch — the former are the blank templates, the latter are the returned,
initial-keyed results. `scripts/score_human_eval_multi.py` discovers and scores the
filled files (`R1`, `O`, `G`); empty files are skipped.

## Scoring

- Multi-rater scorer: `scripts/score_human_eval_multi.py`
- Outputs: `human_validity_multi.{md,json}` (per-rater rates, pairwise Cohen's κ,
  Fleiss' κ across the panel, and each judge vs the majority-vote consensus).
- Confusion matrices vs consensus: `confusion_matrices.md`.
