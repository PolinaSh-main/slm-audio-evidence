# Pilot results — 100 items, 4 runs (2026-07-12)

Dataset: frozen `data/manifests/pilot.jsonl` — 30 A (stated) / 30 B (inference) / 40 C (unanswerable; 12+12+8+8 by subtype). Checker agreement on shared calibration items: 80% (16/20). Runs on Colab T4; per-run reports with 95% Wilson CIs: `results/<run_id>/metrics.md`.

## Main table

| Run | Halluc. on C ↓ | Correct abstain on C ↑ | Accuracy A ↑ | Accuracy B ↑ | Over-refusal (A+B) ↓ |
|---|---:|---:|---:|---:|---:|
| Qwen2-Audio · plain | **92.5%** (37/40) | 2.5% | 23.3% | 26.7% | 6.7% |
| Qwen2-Audio · S1 IDK | 17.5% (7/40) | 82.5% | 13.3% | 6.7% | **61.7%** |
| Cascade · plain | 62.5% (25/40) | 27.5% | 86.7% | 90.0% | 0.0% |
| Cascade · S1 IDK | **2.5%** (1/40) | **97.5%** | 86.7% | 83.3% | 6.7% |

(Hedge on C: 5% / 0% / 10% / 0% — reported separately, not folded into either bucket.)

## Findings

1. **The problem is real and severe:** the end-to-end Speech LLM fabricates an answer on 92.5% of unanswerable spoken questions under a plain prompt (e.g., it names *Johann Gutenberg* as the printer of Luther's 1521 writings — an invented "fact").
2. **A one-line IDK instruction is not free:** on Qwen2-Audio it cuts hallucination to 17.5% but collapses usefulness — 61.7% of answerable/inferable questions get wrongly refused. The model cannot tell "I heard it" from "I didn't".
3. **The bottleneck is epistemic, not acoustic:** the cascade (Whisper → Qwen2.5-7B) with the same instruction reaches **2.5% hallucination at 86.7%/83.3% accuracy and only 6.7% over-refusal** — near-ideal selective behavior. Reasoning over a clean transcript handles evidence far better than the audio-LLM does end-to-end.
4. Even the strong text LLM needs the instruction: cascade-plain still hallucinates 62.5%.

## Verbatim examples (Qwen2-Audio)

- ❌ Hallucination (plain, C): *"The printer who published Luther's 1521 writings on prophecy was Johann Gutenberg."*
- ✅ Correct abstain (S1, C): *"The audio does not provide that information."*
- ⚠️ Over-refusal (S1, A — gold: "vertebrates", stated in the audio): *"The audio does not provide that information."*

## Grading provenance

Labels (answer/abstain/hedge) and A/C correctness: rule-based classifier (`src/judge.py`, dev-set 20/20). Category B answered items (93 across runs): manually graded by M1 against gold + transcript (`judge: "manual-M1"` in `responses_judged.jsonl`); full model outputs inspected before grading. Pipeline validated on `tests/fixtures/smoke_synthetic/` before real data.
