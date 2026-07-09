# Reading List & Assignments

23 papers, all verified and downloaded. File prefix = reading priority within its block.
Roles per [PROPOSAL.md](../docs/en/PROPOSAL.md): **M1** = Lead/infra + methods, **M2** = Data, **M3** = Evaluation, **M4** = optional flex member (takes extra strategies & lit consolidation if they join).

## Block 1 — Closest prior work (01–05) · **EVERYONE reads 01–02 before the pre-defense**

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

## Suggested schedule (work starts Jul 8)

- **By the Jul 8 evening sync:** everyone → 01, 02 (abstract + method + results tables minimum).
- **By Jul 9:** M1 → 16, 19 + 13–15 (feeds harness W1.2 and prompt library W1.3); M2 → 04, 06, 22, 23 (feeds question generation W2.2); M3 → 03, 21 + metric sections of 02, 09 (feeds metrics.py W3.2).
- **By Jul 10, split of Block 2:** M1 → 07, 08 (positioning); M3 → 09, 10 (abstention metrics).
- **M4 (only if they join):** 05 + the rest of Blocks 2–3 — feeds the flex workstream W4.
- **Rolling:** the rest as needed; each reader drops 3–5 bullet takeaways per paper into `docs/related_work.md`.

## Non-paper sources (bookmarks)

- Spoken-SQuAD data: [GitHub](https://github.com/Chia-Hsuan-Lee/Spoken-SQuAD) · [HF test split](https://huggingface.co/datasets/AudioLLMs/spoken_squad_test) · [alinet/spoken_squad](https://huggingface.co/datasets/alinet/spoken_squad)
- LibriSpeech: [openslr.org/12](https://www.openslr.org/12/)
- Models: [Qwen2-Audio-7B-Instruct](https://huggingface.co/Qwen/Qwen2-Audio-7B-Instruct) · [Qwen2.5-Omni-7B](https://huggingface.co/Qwen/Qwen2.5-Omni-7B) · [SALMONN](https://github.com/bytedance/SALMONN)
- TTS: [edge-tts](https://github.com/rany2/edge-tts) · [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M)
- R-Tuning code: [github.com/shizhediao/R-Tuning](https://github.com/shizhediao/R-Tuning)
