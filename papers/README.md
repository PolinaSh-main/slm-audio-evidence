# Reading List & Assignments

27 papers, all verified and downloaded (PDFs local-only, gitignored). File prefix = reading priority within its block.
Roles per [docs/en/ROLE files](../docs/en/ROLE_M1.md): **M1** = lead/decisions, **M2** = experiments, **M3** = literature & text, **M4** = judge & baselines.
**The reading schedule for the paper phase lives in [PLAN.md §6](../docs/en/PLAN.md) — canonical.** Blocks below = the catalog.

## Block 0 — Paper-phase core (24–27) · **read FIRST — 24 and 01 by everyone, by Tue Jul 21**

| # | Paper | Why read it | Deep read |
|---|---|---|---|
| 24 | **Pre-Generation Hallucination Detection via Soft-Target Attention Probing** (Miftakhova & Zaytsev, 2606.21917) | **The method we transfer** (Stage A2): probe prompt hidden states before generation; soft targets from k sampled answers; AUROC | **All**; deep: M2 |
| 25 | **Walking Through Uncertainty** (2604.25591) | Neighbor NTU-lab work: *output-level* uncertainty for LALMs → our entropy baseline + the paper's key positioning contrast (they post-hoc, we pre-generation) | M4, M3 |
| 26 | **LISTEN — "what does not hear"** (Kuan & Lee, 2505.14518, Interspeech 2025) | *Training-based* hallucination mitigation for audio LLMs — contrast to our training-free approach | M3 |
| 27 | **BALSa** (2505.20166) | Same lab: audio-language alignment with synthetic negatives. Note: the mentor referred to 26 and 27 together as "BALSa" — they are two distinct papers | M3 |

## Block 1 — Closest prior work (01–05) · 01 is everyone's second read (AQUA-Bench = our A1 validation target)

| # | Paper | Why read it | Deep read |
|---|---|---|---|
| 01 | **AQUA-Bench** (Kuan & Lee, 2026) | The closest existing work — unanswerable audio QA (MCQ). Curators may ask "how are you different?" Our answer: speech content, free-form answers, mitigation comparison, epistemic gradient | **All** |
| 02 | **Towards Reliable LALM** (Ma et al., 2025) | Training-free IDK-prompting + the RGI metric we adopt | **All**, esp. M3/M4 |
| 03 | HalluAudio (2026) | 5K-item LALM hallucination benchmark; protocol ideas (refusal rate, yes/no bias) | M3 |
| 04 | LALM object hallucination (2024) | Discriminative-question probing design | M2 |
| 05 | Can LALMs Truly Hear? (2024) | Multi-turn CoT mitigation on audio tasks | M4 |

## Block 2 — Unanswerable QA & abstention, text domain (06–10) · **split: M1 → 07–08, M3 → 09–10, M2 → 06** (M4 takes the whole block if they join)

| # | Paper | Why read it |
|---|---|---|
| 06 | SQuAD 2.0 (2018) | The recipe for adversarial unanswerable questions — our category-C blueprint |
| 07 | SelfAware / Do LLMs Know What They Don't Know (2023) | Self-knowledge evaluation methodology |
| 08 | AbstentionBench (2025) | Modern abstention eval; "reasoning tuning degrades abstention 24%" — motivation slide material |
| 09 | Know Your Limits — abstention survey (TACL 2025) | Map of the whole abstention field; skim for framing & metrics vocabulary |
| 10 | R-Tuning (2023) | Refusal-aware tuning — our stretch goal for the main phase |

## Block 3 — Uncertainty signals & inference-time strategies (11–15) · **M1 (strategy design) + M3 (uncertainty signals)**

| # | Paper | Why read it |
|---|---|---|
| 11 | Semantic Uncertainty (2023) | Sampling-based uncertainty over meanings — grounds strategy S4 |
| 12 | Semantic Entropy, Nature (2024) | Peer-reviewed flagship version — credibility citation |
| 13 | Confidence elicitation (2023) | Verbalized confidence is overconfident — grounds S5 design & H2 |
| 14 | Self-Consistency (2022) | Sampling + agreement — grounds S4 |
| 15 | Chain-of-Verification (2023) | Two-stage self-check — grounds S3 |

## Block 4 — Models (16–19) · **M1**

| # | Paper | Why read it |
|---|---|---|
| 16 | Qwen2-Audio (2024) | Primary model — prompt format, audio modes, eval setup |
| 17 | Qwen2.5-Omni (2025) | Second model — Thinker-Talker architecture, input pipeline |
| 18 | SALMONN (2023) | Third model — setup & known quirks |
| 19 | Whisper (2022) | Cascade baseline ASR component |

## Block 5 — Benchmarks & data (20–23) · **M2 + M3**

| # | Paper | Why read it |
|---|---|---|
| 20 | MMAU (2024) | QA design & difficulty calibration reference |
| 21 | AudioBench (2024) | Open eval toolkit — reuse harness/judge patterns (M3) |
| 22 | SAKURA (2025) | Multi-hop speech reasoning — category-B design reference (M2) |
| 23 | Spoken SQuAD (2018) | Our primary audio corpus — how it was built, its ASR error rates |

## Reading schedule — paper phase (starts Jul 18; the pre-defense schedule was never executed and is superseded)

Canonical version with focus notes: [PLAN.md §6](../docs/en/PLAN.md). Per paper: 3–5 takeaway bullets → [docs/related_work.md](../docs/related_work.md) (+ save the BibTeX entry right away).

| Who | Papers | By |
|---|---|---|
| **Everyone** | 24, 01 | Tue Jul 21 |
| M2 | 24 (deep) + 16 | Wed Jul 22 |
| M4 | 25 + 02 | Wed Jul 22 |
| M3 | conveyor 01 → 02 → 03 → 26 → 27 → 25 (+ skim 09) | Jul 19–25, ~1/day |
| M1 | 24 + 01 (decision level), skim 25 | Wed Jul 22 |

Blocks 2–5 below are the reference catalog — dip in when a section of the paper needs them (11–15 for uncertainty baselines, 06/23 for data lineage, 16–19 for model details).

## Non-paper sources (bookmarks)

- Spoken-SQuAD data: [GitHub](https://github.com/Chia-Hsuan-Lee/Spoken-SQuAD) · [HF test split](https://huggingface.co/datasets/AudioLLMs/spoken_squad_test) · [alinet/spoken_squad](https://huggingface.co/datasets/alinet/spoken_squad)
- LibriSpeech: [openslr.org/12](https://www.openslr.org/12/)
- Models: [Qwen2-Audio-7B-Instruct](https://huggingface.co/Qwen/Qwen2-Audio-7B-Instruct) · [Qwen2.5-Omni-7B](https://huggingface.co/Qwen/Qwen2.5-Omni-7B) · [SALMONN](https://github.com/bytedance/SALMONN)
- TTS: [edge-tts](https://github.com/rany2/edge-tts) · [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M)
- R-Tuning code: [github.com/shizhediao/R-Tuning](https://github.com/shizhediao/R-Tuning)
