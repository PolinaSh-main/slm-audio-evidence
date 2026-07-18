# ROLE M4 — Judge, baselines, Methods

Русская версия: [../ru/ROLE_M4.md](../ru/ROLE_M4.md) · Plan: [PLAN.md](PLAN.md) · Paper: [PAPER_OUTLINE.md](PAPER_OUTLINE.md)

**Mission.** You own answer grading (the LLM-judge) and the signal baselines the probe must beat. In Stage B you write Methods.

**Context in 3 bullets:** your judge already hit **94% agreement** with 93 human-graded B answers (Qwen3-8B + judge_v1) — that number goes in the paper; your PR is being redone Jul 21 (clean authorship + extra judge models — instructions you already have from M1); the probing plan (A2) needs you twice: soft-target grading and the entropy baseline.

## Stage A (Jul 21–29)

1. **Judge rework (Mon Jul 21)** — per M1's instructions: resubmit the judge package with clean commit authorship and test the additional judge models. Keep the audit table (model × agreement vs the 93 golden B grades) — it becomes a paper table. *Done when:* PR open, audit table in the PR description.
2. **Judge A1 outputs (Jul 22–24).** M2 hands you 4 runs on the AQUA subset. Grade with the best judge; spot-check ~20 items by hand. If AQUA stays MCQ (M1's Decision 1), grading is exact-match — then your job is just the free-form part, if any. *Done when:* `responses_judged.jsonl` for all A1 runs.
3. **Soft targets for A2 (Jul 23–24, with M2).** M2 samples k≈10 answers per item; you grade them (rules classifier + judge) → per-item fraction hallucinated. This is the probe's training signal — quality here decides A2. *Done when:* soft-label file per item delivered to M2.
4. **Entropy baseline (Jul 24–27).** From the same k samples compute the output-uncertainty baseline (answer-disagreement / entropy, as in paper 25). Report its AUROC the same way as the probes — the paper's claim "pre-generation beats output-level" rests on this comparison being fair.
5. **Probes with M1 (Jul 25–29).** M1 trains the probes (runs — M2); you are the second pair of eyes on evaluation and own the cross-validation protocol (no leakage: same passage never in train and test).

## Stage B — Methods (Jul 29–31)

Write Methods: systems (Qwen2-Audio, cascade), prompts (plain/S1), the judge (pipeline, model choice, 94% + audit), probing (capture → soft targets → probes → threshold). Then Experiments with M2. Contribution sentences to M1 by Jul 30.

## Reading (by Wed Jul 22)

| Paper | Read for | Depth |
|---|---|---|
| 25 — Walking Through Uncertainty | entropy-baseline design (task 4) | method + metrics |
| 02 — Towards Reliable LALM | RGI metric; how they judge refusals | metrics sections |
| 24 — attention probing | shared context for tasks 3–5 | method (everyone reads this) |

**If stuck:** judge disagrees with your gut on >3 of 20 spot-checks → escalate to M1 with examples, don't silently retune. Kaggle quota issues → DataSphere is the primary now, ask M1 for access.
