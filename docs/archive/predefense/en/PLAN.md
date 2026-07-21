# Execution Plan — who does what, when, and at what scope

**Project:** Can Speech LLMs Recognize When Audio Evidence Is Insufficient? (SMILES 2026)
**Deadline:** repo + presentation by **July 12, 23:00 UTC+3**, then Zoom pre-defense.
**This document = execution** (who/when/how). The science (why/what) lives in [PROPOSAL.md](PROPOSAL.md); step-by-step per-member instructions live in [roles/en/](ROLE_M1.md); terms in [GLOSSARY.md](../../../en/GLOSSARY.md). Русская версия: [PLAN_RU.md](../ru/PLAN.md).

---

## 1. Team & roles

Core team = 3 people. Every member owns code in the repo (pre-defense criterion: *everyone visibly active*). Detailed step-by-step task cards: **[ROLE_M1](ROLE_M1.md) · [ROLE_M2](ROLE_M2.md) · [ROLE_M3](ROLE_M3.md)**.

| Who | Mission | Presents |
|---|---|---|
| **M1 — Team Lead: infrastructure, methods, integration** | Repo, inference harness, prompt library (plain + S1 + S4), Colab smoke test, final assembly + tag; coordinates daily sync and the decisions log | framing, plan, methods |
| **M2 — Data Lead** | Pull Spoken-SQuAD passages, generate B/C questions from transcripts, run non-author verification, freeze `pilot.jsonl`, data card | dataset |
| **M3 — Evaluation Lead** | Answer classifier (answer/abstain/hedge), LLM-judge + audit, metrics module, the E1+S1 pilot run, results table + chart | results |

**M4 (optional 4th member) — flex backlog, only if they join:** remaining strategies S2/S3/S5, S4 smoke test, related-work consolidation; main phase: Qwen2.5-Omni wrapper, degradation-ablation prep.
**Onboarding rule:** joins by **Jul 10** → takes the flex backlog fully and presents the methods slide. Joins Jul 11 → S4 smoke test + verification help + Q&A prep. Doesn't join → flex items move to main-phase week 2; the plan stands as-is.

## 2. Data contracts (CANONICAL — role files hold convenience copies)

Field changes go through `docs/decisions.md` the same day, never silently.

**Manifest** (M2 produces → everyone reads) — `data/manifests/pilot.jsonl`, one JSON per line:
```json
{"id": "sq-0421-C2",               // unique: source–passage–category+number
 "audio_path": "data/audio/….wav",
 "transcript": "…",                // exact text of the audio
 "question": "…",
 "category": "C",                  // A stated | B inferable | C unanswerable
 "subtype": "absent-attribute",    // A: "stated" · B: "inference" · C: C1 absent-entity, C2 absent-attribute, C3 false-premise, C4 off-topic
 "gold_answer": "UNANSWERABLE",    // reference answer; literal UNANSWERABLE for C
 "source": "spoken-squad",         // spoken-squad | tts
 "generator": "gpt-4o-mini/b-v2",  // model/prompt-version; "native" for original SQuAD questions
 "verified_by": "M3"}              // checker — never the author
```

**Responses** (M1's harness produces → M3 reads) — `results/<run_id>/responses.jsonl`:
```json
{"id": "sq-0421-C2", "model": "qwen2audio", "strategy": "plain",
 "response": "…", "samples": null,   // samples = list of 5 answers for s4_consistency
 "latency_s": 3.1, "ts": "2026-07-11T14:02:11", "prompt_version": "plain.txt"}
```

**Judged responses** (M3 produces) — response line plus:
```json
{"label": "answer|abstain|hedge", "correct": true, "judge": "rules|human|llm-v1"}
```

## 3. Milestones & day-by-day (work starts Jul 8)

| Date | Milestone |
|---|---|
| Jul 8 | Kickoff: repo + roles, corpora/models chosen, schema fixed, passages pulled |
| Jul 9 | B/C questions generated; harness runs end-to-end |
| Jul 10 | Pilot frozen (90–120 items); metrics + S1/S4 prompts ready; deck skeleton — **tier checkpoint (§4)** |
| Jul 11 | E1 + S1 comparison numbers + plots; slides filled |
| Jul 12 | Judge audit, rehearsal, tag `v0.1-predefense`, **submit 23:00 UTC+3** |

| | Jul 8 | Jul 9 | Jul 10 | Jul 11 | Jul 12 |
|---|---|---|---|---|---|
| **M1** | repo + board, harness skeleton | wrappers done; related-work: positioning | prompt lib S1/S4, Colab smoke test, deck skeleton | integrate, README | tag v0.1, rehearse, **submit** |
| **M2** | corpora recon, passages + TTS | B/C generation; related-work: data | verification, freeze pilot | data card, slides: data | buffer, rehearse |
| **M3** | metrics design, classifier rules | judge v1; related-work: metrics | metrics.py done | **E1 pilot + S1 comparison + plots** | judge audit, rehearse |
| *M4 (if joins)* | — | — | flex backlog: S2/S3/S5 prompts | S4 smoke test, slides: methods | Q&A prep, rehearse |

Dependencies: harness (Jul 9) → pilot run; data freeze (Jul 10) → pilot run; pilot numbers (Jul 11) → deck.

## 4. Scope tiers — each contains the previous one; checkpoint **Jul 10 evening**

What each tier *claims* scientifically is in [PROPOSAL.md §7](PROPOSAL.md).

| Dimension | **Tier 1 MINIMUM** (emergency floor) | **Tier 2 MEDIUM** (default) — adds | **Tier 3 MAXIMUM** (stretch) — adds |
|---|---|---|---|
| Dataset | 60 items (20/20/20), C = C1+C2 only, Spoken-SQuAD audio only | 90–120 pilot with C1–C4, TTS fallback; main phase 600–900, ~50/50 TTS/natural | 1,000–1,200; + LibriSpeech slice, paralinguistic B-questions, degradation set (noise/truncation) |
| Systems | Qwen2-Audio (int8, Colab); cascade if time | cascade mandatory; main phase + Qwen2.5-Omni → 3 | + SALMONN + one closed-source reference → 5 |
| Strategies | plain + S1 | + S4 implemented; main phase S1–S5 | + S6 internal-signal detector (logprobs / semantic entropy) |
| Grading | rules + manual (one evening for 3 people) | LLM-judge v1 + 30-item human audit | + calibration deep-dive |
| Metrics | 3 core rates + Wilson CIs | + F1, risk–coverage/AURC, RGI | + AUROC for detectors, degradation curves |
| Extras | — | E3 analysis (epistemic gradient, subtype taxonomy) | LoRA refusal-tune experiment; transfer eval on AQUA-Bench/HalluAudio; HF dataset release + workshop paper draft |

**Switching rules:**
- **Down to Tier 1** if at the Jul 10 evening checkpoint: pilot not frozen OR harness not running OR a core member lost ≥2 days. It's a scope cut, not a re-plan — Tier 1 is already built by then (that's the point of stacking). No direct path Tier 1 → Tier 3.
- **Up to Tier 3** only if ALL: M4 joined by Jul 10; Jul 9 milestones met on time; after the pre-defense — GPUs granted + small API budget.
- **Tier 3 add-on ladder** (adopt top-down, drop bottom-up; a rung never endangers Tier 2's definition of done): 1) full S1–S5 grid on 3 systems → 2) SALMONN + closed-source reference → 3) LibriSpeech + paralinguistic B → 4) degradation set + curve → 5) S6 detector → 6) transfer eval → 7) LoRA experiment → 8) HF release + paper draft. If any main-phase week slips ≥3 days, drop the lowest unadopted rung — no other re-planning.

## 5. Coordination

- **Daily 15-min sync**, fixed evening time; Telegram group for async.
- **`docs/decisions.md`** — every decision: date, what, why. Schema changes always go here.
- **Git workflow:** branches `m1/…`, `m2/…`, `m3/…`; PR + 1 review into `main`; no direct pushes.
- **Verification duty:** every generated dataset item is checked by a non-author (protocol in [ROLE_M2](ROLE_M2.md), Task 3).

## 6. Repository structure

```
slm-audio-evidence/                # github.com/ladnlav/slm-audio-evidence
├── README.md                  # what/why/how to run + team + pilot results
├── docs/related_work.md · decisions.md · data_card.md
├── data/manifests/*.jsonl     # pilot.jsonl (frozen), later versions
│   └── generation/            # passage selection, TTS, question-gen prompts, filters, validator
├── src/
│   ├── models/base.py qwen2_audio.py cascade.py (omni.py salmonn.py later)
│   ├── prompts/               # plain.txt, s1_idk.txt, judge_v1.txt, stubs s2/s3/s5
│   ├── inference.py  judge.py  metrics.py
├── configs/*.yaml
├── notebooks/colab_smoke_test.ipynb  analysis.ipynb
└── results/                   # responses + judged + metrics (large files gitignored)
```

## 7. Pre-defense checklist & speakers

| Criterion | Our evidence |
|---|---|
| ✅ Team understands the goal | Slides restating problem, RQs, A/B/C design in our own words |
| ✅ Realistic, clear plan | This document: milestones, tier system with Jul 10 checkpoint, role files |
| ✅ Meaningful, feasible experiments | E1/E2/E3 with defined metrics; pilot already executed on Colab |
| ✅ Initial progress | Repo: harness, data pipeline, metrics, pilot numbers (plain vs S1) |
| ✅ Team active & ready | 3 named roles with individual outputs + severable scope for an optional 4th; commit history from all |

**Deck (10 slides):** problem+example → RQs → related-work gap → dataset design → models → experiments → metrics → pilot numbers → timeline+tiers → team.
**Speakers:** M1 framing/plan + methods (M4 takes methods if joined by Jul 10), M2 data, M3 results.
**Q&A prep:** "difference from AQUA-Bench?" · "what if GPUs are delayed?" · "how do you judge free-form answers?" · "what changes with 3 people?"

## 8. Main phase preview (after approval, with Yandex Cloud GPUs)

Weeks 2–3: scale dataset; full E1+E2 grid — **scope dial:** 3 people → 3 systems × 5 strategies; with M4 → 4 × 6. Weeks 4–5: E3 analysis, error taxonomy, audits (+ Tier 3 ladder rungs if entered). Week 6: report + final presentation; possible target: ICASSP/Interspeech workshop track.
