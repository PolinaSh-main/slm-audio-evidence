# Related Work — team notes

3–5 plain bullets per paper (takeaways, not summaries). Paper numbers refer to [papers/README.md](../papers/README.md); full citations in [PROPOSAL.md §9](en/PROPOSAL.md).
Split (due Jul 10, PLAN.md §3): **M1** — positioning & models (01, 02, 16, 19) · **M2** — data & benchmarks (04, 06, 22, 23) · **M3** — metrics & uncertainty (03, 21, 09, 10 + metric sections of 02).

## Positioning & closest work (M1)

**01 — AQUA-Bench (Kuan & Lee, arXiv 2601.12248, Jan 2026)**
- Benchmark for *unanswerability* in audio QA: absent answer option, incompatible answer set, incompatible audio–question pair.
- Format is multiple-choice over general audio (sound events); models do well on answerable items, markedly worse on unanswerable ones — confirms the problem is real and current.
- Measures only; proposes no mitigation.
- **Our gap:** spoken-content QA (not sound events), free-form answers (not MCQ), and a head-to-head comparison of abstention strategies — we start where they stop.

**02 — Towards Reliable LALM (Ma et al., arXiv 2505.19294)**
- Systematically tests ways to make audio-LLMs refuse what they don't know: training-free (multimodal chain-of-thought, IDK instructions) and training-based (SFT).
- Introduces the Reliability Gain Index (RGI) — a metric for how much a method improves refusal behaviour beyond what it costs.
- Finds "reliability" transfers across audio modalities like a meta-ability.
- **We adopt:** their IDK-prompt idea is our S1; RGI is planned for the main phase.

**16 — Qwen2-Audio (Chu et al., arXiv 2407.10759)**
- Open 7B audio-language model: Whisper-style encoder + Qwen LLM, natural-language prompts instead of task tags, DPO for factuality.
- Two modes (voice chat / audio analysis) without a mode switch; strong AIR-Bench results.
- **Our primary system**; practical note: answers degrade quietly if the chat template deviates from the model card.

**19 — Whisper (Radford et al., arXiv 2212.04356)**
- ASR trained on 680k h of weakly supervised audio; robust zero-shot transcription.
- **Role here:** front-end of our cascade baseline (Whisper → text LLM), which isolates "didn't hear it" failures from "can't reason about evidence" — the key ablation for interpreting hallucination numbers.

## Datasets & benchmarks (M2)

### 04 — Understanding Sounds, Missing the Questions: Object Hallucination in LALMs

- Tests whether LALMs hallucinate objects in audio, not just whether they can caption audio.
- Useful design idea: ask discriminative questions about whether specific evidence is present in the audio.
- Negative examples are built by sampling objects that are not in the clip, including harder adversarial/co-occurring objects.
- Main lesson for us: models may understand the audio generally but still fail when the question asks for a precise supported/unsupported detail.
- Difference from our dataset: their questions are mostly yes/no about sound objects; ours are free-form speech-content questions with A/B/C labels.

### 06 — SQuAD 2.0: Know What You Don't Know

- This is the main blueprint for our C questions: unanswerable questions should look relevant, not obviously unrelated.
- Section 2 gives two key rules: the question should match the paragraph topic, and the paragraph should contain a plausible distractor of the right type.
- Section 3 explains why easy negatives are weak: random or automatically mismatched questions can be detected by word overlap or type heuristics.
- Their unanswerable examples include several patterns close to our C subtypes: entity swaps, impossible conditions, contradictions, and neutral missing facts.
- Main lesson for us: C questions need human verification, because a question that is secretly answerable breaks the whole benchmark.

### 22 — SAKURA: Multi-hop Reasoning of Large Audio-Language Models

- Evaluates whether LALMs can combine information from speech/audio, not only recognize one direct attribute.
- Useful for our B category: B questions should require connecting facts, comparing, or doing a small inference from the transcript.
- Their construction separates single-hop perception from multi-hop reasoning, which matches our need to distinguish A from B.
- They use generated questions plus human verification, which supports our pipeline of prompt generation, filtering, and non-author checking.
- Difference from our dataset: SAKURA is multiple-choice and broader audio/speech attributes; ours is free-form QA over spoken passages.

### 23 — Spoken SQuAD

- Primary source corpus for our pilot: SQuAD passages converted into spoken documents, with text questions.
- Built from SQuAD using text-to-speech audio and ASR transcripts; the original paper reports 37,111 train QA pairs and 5,351 test QA pairs.
- The paper shows ASR errors strongly hurt QA performance, which motivates keeping clean transcripts for generation and checking audio quality separately.
- It is a good fit for our pilot because it already gives aligned passage audio, transcripts, and native A questions.
- Limitation for us: the audio is read/TTS-style SQuAD content, not natural conversation or a broad real-world speech domain.

## Metrics, abstention & uncertainty (M3)

*(to fill)*
