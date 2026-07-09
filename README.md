# slm-audio-evidence — Can Speech LLMs Recognize When Audio Evidence Is Insufficient?

**SMILES 2026 · Curator: Assel Yermekova · Team: M1 (lead), M2, M3 (+ optional M4)**
**Pre-defense: this repo + presentation by July 12, 23:00 UTC+3.** Русская версия: [README_RU.md](README_RU.md).

## The project in 5 bullets

- A **Speech LLM** takes a sound recording + a written question and answers in text.
- Problem: when the recording does not contain the answer, models invent one. Audio: "I like apples." Question: "What color was the jacket?" Model: "Blue." — a **hallucination**.
- We build a test set with three question kinds: **A** answer stated · **B** answer inferable · **C** not in the audio at all (the model should say so).
- We measure how often models hallucinate on C and compare prompt-level fixes against the cost of refusing too much.
- Scope is tiered (MINIMUM / MEDIUM / MAXIMUM) with a go/no-go checkpoint on July 10 evening.

## Where to look — 3 files per person

All knowledge lives in **[docs/en/](docs/en/)** (English) and **[docs/ru/](docs/ru/)** (Russian) — same seven files each:

| File | What it is | Who needs it |
|---|---|---|
| [GLOSSARY.md](docs/en/GLOSSARY.md) | Every term + "what is a Speech LLM" intro | everyone, once (5 min) |
| [ROLE_M1](docs/en/ROLE_M1.md) / [ROLE_M2](docs/en/ROLE_M2.md) / [ROLE_M3](docs/en/ROLE_M3.md) | **Your tasks, step by step** — self-contained | you, daily |
| [PROPOSAL.md](docs/en/PROPOSAL.md) | Vision & science: hypotheses, literature, experiments, per-tier claims | lead, curator, Q&A prep |
| [PLAN.md](docs/en/PLAN.md) | Execution: schedule, tiers & switching, data contracts, checklist | lead, checkpoints |
| [KANBAN_M1.md](docs/en/KANBAN_M1.md) | M1's board cards with checklists | M1 |

Shared working logs: [docs/decisions.md](docs/decisions.md) (every decision, same-day schema announcements) · [docs/related_work.md](docs/related_work.md) (paper notes, split M1/M2/M3). Papers: [papers/README.md](papers/README.md) (reading guide; PDFs local-only, gitignored).

## Repository layout

```
README(_RU).md      ← you are here
docs/en/ · docs/ru/ ← all project docs, one folder per language (7 files each)
docs/               ← shared logs: decisions.md, related_work.md, data_card.md (soon)
papers/             ← reading guide (+ local PDFs, not committed)
data/manifests/     ← eval-set JSONL (pilot.jsonl appears at the Jul 10 freeze)
data/generation/    ← passage selection, A-questions, TTS fallback (M2 — already started)
src/models/         ← wrappers: base.py, qwen2_audio.py, cascade.py (M1)
src/prompts/        ← strategy files: plain.txt, s1_idk.txt, … (M1)
src/                ← inference.py (M1) · judge.py, metrics.py (M3)
configs/ notebooks/ results/
```

## Setup & run (commands become real as tasks land — see docs/en/PLAN.md §3)

```bash
pip install -r requirements.txt
python -m src.inference --model qwen2audio --strategy plain --data data/manifests/pilot.jsonl --out results/
```

## Working rules

- Branches `m1/…`, `m2/…`, `m3/…`; merge into `main` via PR + 1 review; no direct pushes.
- Every decision → [docs/decisions.md](docs/decisions.md); data-schema changes announced there the same day. Canonical schemas: [docs/en/PLAN.md §2](docs/en/PLAN.md).
- Every document exists in both languages ([docs/en](docs/en/) ↔ [docs/ru](docs/ru/)), cross-linked. Each fact has one home; everything else links to it.
