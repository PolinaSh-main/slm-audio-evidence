# Role M3 — Evaluation Lead: turn model answers into trustworthy numbers

**How to read this file:** it explains your tasks step by step and explains every technical word the first time it appears. You can start working from this file alone. Links are only for going deeper: [full proposal](PROPOSAL.md) · [execution plan](PLAN.md) · [glossary](../../../en/GLOSSARY.md) · [papers guide](../../../../papers/README.md) · [русская версия](../ru/ROLE_M3.md).

## The project in plain words

- A **Speech LLM** is an AI model: sound recording + written question in, text answer out.
- Problem: when the recording does not contain the answer, models invent one (a **hallucination**). Audio: "I like apples." Question: "What color was the jacket?" Model: "Blue."
- Our test items have three categories: **A** — answer is spoken in the recording; **B** — answer can be figured out from what was said; **C** — answer is not there at all. On C the correct behavior is to refuse (**abstain**); the stored correct answer for C is the literal word `UNANSWERABLE`.
- We compare two prompt styles: `plain` (just the question) vs `s1_idk` (adds: "if the audio doesn't contain it, say so"). **The main slide of our defense is your table comparing them.**
- Deliverable: repository + slides by **July 12, 23:00 UTC+3**; your numbers are due **July 11**.

## Words used in this file

| Word | Plain meaning |
|---|---|
| Label | The tag you attach to a model answer: `answer`, `abstain`, or `hedge` |
| Classifier | A script that attaches those labels automatically |
| Rule-based | Working by simple hand-written rules (like "contains the phrase 'not mentioned'"), no AI involved |
| Refusal phrase | A phrase showing the model declines to answer ("no information", "cannot be determined") |
| Hedge | A vague answer that neither really answers nor clearly refuses ("it might be something…") |
| Gold answer | The stored correct answer for an item |
| Normalize | Lowercase the text, strip punctuation — so "The Dog." equals "dog" |
| Fuzzy match | Approximate text comparison; `rapidfuzz` is a Python library for it; "ratio ≥85" means at least 85% similar |
| LLM-judge | A separate AI model that grades answers using a fixed instruction |
| Rubric | That fixed grading instruction — same for every answer, saved in a file |
| Dev set | ~20 examples you label by hand first, used to tune and sanity-check the automatic grading |
| Metric / rate | A number summarizing results; a rate = a share, count-of-cases ÷ total |
| Confidence interval (CI) | The honest range around a rate given the sample size; **Wilson CI** is the formula we use — with few items the range is wide, and we show it anyway |
| Unit test | A tiny automatic test: feed the code a hand-made input where you know the right output, check it matches |
| JSONL / manifest | A text file with one JSON record per line / the file listing all test items |
| Run | One pass of one model with one prompt style over the whole dataset |
| Stratified sample | A sample taken evenly across groups (e.g., a few from every category × label combination) |
| Blind check | Grading without seeing what the automatic grader said, so you're not influenced |
| Audit | A human check of a sample of automatic decisions, giving an agreement % |

## Your mission

Model answers arrive as free text. You turn them into numbers people can trust: label each answer, grade correctness, compute the metrics, run the pilot experiment, and make the results table and chart for the deck. You are the guardian of honesty: every number ships together with *how it was graded* and *how well the automatic grader agrees with humans*.

---

## What you receive and what you produce

**From M1** (the harness output): `results/<run_id>/responses.jsonl` — one line per item: `{"id", "model", "strategy", "response", "samples", …}`.
**From M2** (the dataset): `data/manifests/pilot.jsonl` — `{"id", …, "category": "A|B|C", "gold_answer": "…|UNANSWERABLE"}`.
**You produce:** `responses_judged.jsonl` — each response line plus `{"label": "answer|abstain|hedge", "correct": true|false|null, "judge": "rules|human|llm-v1"}` — and `metrics.md` (the readable results table).

---

## Task 1 — The answer classifier · finish **July 9**

**Goal:** given a model's text answer, decide automatically: did it answer, abstain, or hedge? And if it answered — was it correct?

Build it in three stages in `src/judge.py`:

1. **Rules first** (free and predictable). Start from this refusal-phrase list and grow it from real outputs:
   `does not provide`, `doesn't provide`, `not mentioned`, `no information`, `cannot be determined`, `can't be determined`, `cannot answer`, `unable to determine`, `not specified`, `not stated`, `I don't know`, `there is no mention`.
   Hedge markers (use only when no concrete answer is given): `possibly`, `probably`, `it seems`, `might be`, `I guess`, `likely`, `perhaps`.
   The deciding rule: refusal phrase and no concrete answer → `abstain`. A concrete answer present — even wrapped in "probably" — → `answer` (**an unsure wrong answer is still a hallucination**). Neither → `hedge`.
2. **Correctness** for answers: category A — normalize both texts, compare with fuzzy match (`rapidfuzz` ratio ≥85 = correct). Category B — use the LLM-judge (stage 3), wording varies too much for matching. Category C — any `answer` is automatically incorrect (there is nothing to answer).
3. **LLM-judge** for B and unclear A cases. The rubric, saved as `src/prompts/judge_v1.txt` (version it like code):
   > You grade a QA system. TRANSCRIPT: {transcript} QUESTION: {question} GOLD ANSWER: {gold} SYSTEM ANSWER: {response}. Reply with exactly one word: CORRECT (same meaning as gold), INCORRECT (different/contradicting), or ABSTAINED (declines to answer). Judge meaning, not wording.
   Which model plays judge (a cheap API one or a local model) — decide with M1 by budget; write the choice into `docs/decisions.md`.

**First, make your dev set:** take 20 real model answers (from M1's smoke test), label them by hand. **You are done when** the automatic pipeline agrees with your hand labels on ≥85% of those 20, and you've walked through the disagreements once with M1.

## Task 2 — The metrics module · finish **July 10**

`src/metrics.py` reads `responses_judged.jsonl` + the manifest and writes `metrics.md`. Each metric in plain words (n_X = number of items in category X):

- **Hallucination rate** = answers given on category C ÷ n_C. *The headline: how often the model invents.*
- **Correct-abstain rate** = refusals on C ÷ n_C. *The desired behavior.*
- **Hedge rate on C** = hedges on C ÷ n_C. *Report separately; don't hide it in either bucket.*
- **Accuracy A / Accuracy B** = correct answers ÷ n_A (resp. n_B). *Is the model still useful?*
- **Over-refusal rate** = refusals on A and B ÷ (n_A + n_B). *The price of caution — always shown next to the headline.*
- **Abstention precision** = refusals that were right (on C) ÷ all refusals; **recall** = refusals on C ÷ n_C; **F1** = their harmonic mean. *How well-aimed the refusing is.*
- **Wilson 95% CI** on every rate — implement once, apply everywhere.
- *(Main phase only:)* risk–coverage curve, AURC, and RGI — take the exact definition of RGI from paper 02 ([Towards Reliable LALM](https://arxiv.org/abs/2505.19294)); do not improvise it.

Layout of `metrics.md`: one row per (model, strategy); columns = the rates above with their intervals; category and subtype breakdowns below.

**You are done when:** a unit test with a tiny hand-made input file reproduces values you computed on paper.

## Task 3 — The pilot run and the results · finish **July 11** ⚠ the deck waits for this

1. The moment M2 freezes the data, start the four runs with M1's harness: `qwen2audio` and `cascade`, each with `plain` and `s1_idk` (~120 items × 4 runs — it's hours, start early in the day).
2. Push all four through your classifier and metrics.
3. Produce for the deck:
   **(a)** the main table — 4 rows (model × strategy), columns: hallucination rate ↓, correct-abstain ↑, accuracy A, accuracy B, over-refusal ↓, each with its interval;
   **(b)** one grouped bar chart — hallucination on C vs over-refusal on A+B, plain vs S1, per model (matplotlib; fonts big enough to read on a Zoom call);
   **(c)** three verbatim examples: one clean hallucination, one correct refusal, one over-refusal. Real quotes make the talk.
4. Before publishing numbers, sanity-check: eyeball 20 random C-item labels; every run covers every manifest id exactly once; cascade transcripts aren't empty.

**You are done when:** table + chart + examples are committed to `results/pilot/` and pasted into the deck, and you can explain where every number came from.

## Task 4 — The judge audit · **July 12**

Take a stratified sample of 30 judged answers (a few from each category × label), grade them yourself **blind**, have M2 double-grade 10 of them. Compute the agreement %. It goes into `metrics.md` and as a footnote on the results slide ("automatic grading agrees with humans on N/30"). **If agreement is below 80%**, the deck shows rule-based + hand-graded numbers instead — that call is yours; log it.

## Task 5 — Your slides · **July 9–12**

- Into `docs/related_work.md`: 3–5 plain bullets each on papers 03, 21, 09, 10 + the metrics sections of 02 (see the [papers guide](../../../../papers/README.md)).
- **You present the results slide**: the table, the chart, one hallucination example read aloud. Expected questions: "How do you grade free-text answers?" (your chain: rules → fuzzy match → judge → human audit) and "Why trust an AI judge?" (the audit number).

## If plans shrink or grow

- **Fallback (decided July 10 evening):** skip the LLM-judge and the audit; all ~120 answers get graded by hand by the three of you in one evening; metrics = the first three rates + intervals.
- **Stretch:** a detector built on the model's internal probabilities, and a calibration study — see [PLAN.md §4](PLAN.md).

## Your days

| Jul 8 | Jul 9 | Jul 10 | Jul 11 | Jul 12 |
|---|---|---|---|---|
| metric definitions; grading sheet; start the rules | Task 1 + hand-label the 20-item dev set; related-work bullets | Task 2 + unit test; dry-run on M1's smoke outputs | **Task 3: runs, table, chart, examples** | Task 4 audit; final numbers into the deck; rehearse |

## Reading order

Papers 01 and 02 (everyone, by the July 8 sync; 02 also defines RGI) → 03, 21 (grading protocols) → 09 (metric vocabulary), 10.

## Traps to avoid

- **An unsure wrong answer is a hallucination, not a hedge** — the label depends on whether a concrete answer is present, not on the tone.
- Never tune your refusal-phrase list on the same items you report — dev set (your 20) and report set stay separate.
- The judge reads the *transcript*, never the audio. That's fine (the correct answers are text), but say it out loud when asked.
- Intervals on ~30 items are wide. Show them anyway — honest error bars beat clean-looking points.
- Start the runs the moment the data freezes — Colab plus ~480 generations is half a day, not an hour.
