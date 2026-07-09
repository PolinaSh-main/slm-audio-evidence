# Project Proposal (Vision & Science) — Can Speech LLMs Recognize When Audio Evidence Is Insufficient?

**SMILES 2026 · Curator: Assel Yermekova · Core team of 3 (a 4th member may join)**
**Pre-defense deliverables (July 12, 23:00 UTC+3):** GitHub repo with current code + short plan presentation.
**This document = the science:** positioning, hypotheses, resources, dataset & experiment design, what we claim at each scope tier.
**Execution** (roles, schedule, tiers mechanics, coordination) → [PLAN.md](PLAN.md) · **per-member instructions** → [roles/en/](ROLE_M1.md) · **all terms explained** → [GLOSSARY.md](GLOSSARY.md) · **document map** → [README.md](../../README.md) · Русская версия: [PROPOSAL_RU.md](../ru/PROPOSAL.md).

---

## 1. Pitch (one paragraph)

Speech LLMs — models that take an audio clip plus a text question and answer in text (see [GLOSSARY.md](GLOSSARY.md)) — answer spoken questions fluently even when the audio contains **no evidence** for the answer — they hallucinate instead of saying *"the audio does not provide that information."* We build a controlled evaluation set of audio–question pairs across three epistemic levels (**stated / inferable / absent**), measure how modern Speech LLMs behave on it, and compare **training-free inference-time strategies** (uncertainty-aware prompting, explicit abstain option, self-verification, self-consistency, verbalized confidence) that trade hallucination against over-refusal. Output: a benchmark + a systematic comparison + practical recommendations for reliable speech assistants.

---

## 2. Positioning: what already exists and what we add

Verified literature (all links checked against arXiv/Crossref — full list with BibTeX in §9).

### 2.1 Closest prior work — read these first

| Paper | What they did | What we do differently |
|---|---|---|
| **AQUA-Bench** (Kuan & Lee, Jan 2026) — [arXiv:2601.12248](https://arxiv.org/abs/2601.12248) | Unanswerability benchmark for audio QA: absent answer option, incompatible answer set, incompatible audio–question. **MCQ (multiple-choice) format**, general audio (sound events) | We focus on **speech content** (spoken passages, not sound events), **free-form generation** (not MCQ), a graded epistemic taxonomy (stated/inferable/absent), and — crucially — **mitigation strategies**, not just measurement |
| **Towards Reliable LALM** (Ma et al., 2025) — [arXiv:2505.19294](https://arxiv.org/abs/2505.19294) | Training-free (multimodal chain-of-thought prompting, MCoT) + supervised fine-tuning (SFT) to make LALMs refuse what they don't know; propose the Reliability Gain Index (RGI) metric; reliability is a transferable "meta-ability" | We adopt their **RGI metric** and IDK-prompt baselines; we add self-consistency & self-verification strategies, risk–coverage analysis, and the answerable/inferable/unanswerable gradient on speech QA |
| **HalluAudio** (Zhao et al., Apr 2026) — [arXiv:2604.19300](https://arxiv.org/abs/2604.19300) | 5K+ human-verified QA benchmark for LALM hallucination across speech/sound/music; measures hallucination rate, yes/no bias, refusal rate | Benchmark only (no mitigation); we can reuse their protocol ideas (adversarial prompts, refusal-rate metric) and compare our numbers where tasks overlap |
| **LALM object hallucination** (Kuan et al., 2024) — [arXiv:2406.08402](https://arxiv.org/abs/2406.08402); **"Can LALMs Truly Hear?"** (Kuan & Lee, 2024) — [arXiv:2410.16130](https://arxiv.org/abs/2410.16130) | Sound-object hallucination probing; multi-turn CoT mitigation | Sound events, not spoken content; we borrow the discriminative-question idea for our category design |

**Novelty claim for the pre-defense:** unanswerability in *spoken-content* QA with *free-form* answers + a head-to-head comparison of *inference-time abstention strategies* under a *selective-prediction* (risk–coverage) lens is not covered by any of the above. AQUA-Bench proves the topic is timely (same lab published it 6 months ago); we go where they stopped.

### 2.2 Text-domain foundations (methods we transfer to audio)

| Cluster | Papers |
|---|---|
| Unanswerable QA design | SQuAD 2.0 — [arXiv:1806.03822](https://arxiv.org/abs/1806.03822) (adversarial unanswerables; our category-C recipe) |
| Do models know what they don't know | SelfAware — [arXiv:2305.18153](https://arxiv.org/abs/2305.18153); AbstentionBench — [arXiv:2506.09038](https://arxiv.org/abs/2506.09038) (reasoning fine-tuning *degrades* abstention by ~24% — great motivation slide); survey "Know Your Limits" — [arXiv:2407.18418](https://arxiv.org/abs/2407.18418) / TACL [10.1162/tacl_a_00754](https://doi.org/10.1162/tacl_a_00754) |
| Uncertainty signals | Semantic uncertainty — [arXiv:2302.09664](https://arxiv.org/abs/2302.09664); semantic entropy in Nature — [10.1038/s41586-024-07421-0](https://doi.org/10.1038/s41586-024-07421-0); verbalized confidence — [arXiv:2306.13063](https://arxiv.org/abs/2306.13063) |
| Inference-time strategies | Self-consistency — [arXiv:2203.11171](https://arxiv.org/abs/2203.11171); Chain-of-Verification — [arXiv:2309.11495](https://arxiv.org/abs/2309.11495); refusal-aware tuning R-Tuning — [arXiv:2311.09677](https://arxiv.org/abs/2311.09677) (stretch goal if we ever train) |

### 2.3 Benchmarks & infrastructure context

- **MMAU** — [arXiv:2410.19168](https://arxiv.org/abs/2410.19168): 10k audio QA, expert reasoning; even Gemini-1.5-Pro ≈53% — shows headroom.
- **AudioBench** — [arXiv:2406.16020](https://arxiv.org/abs/2406.16020): open eval toolkit for AudioLLMs — reuse their harness patterns/judge prompts.
- **SAKURA** — [arXiv:2505.13237](https://arxiv.org/abs/2505.13237): multi-hop reasoning over speech — relevant to our category B (inferable).

---

## 3. Research questions & hypotheses

- **RQ1.** When do Speech LLMs answer instead of refusing under insufficient audio evidence?
  **H1:** default-prompted models answer >70% of unanswerable questions (based on AQUA-Bench/AbstentionBench trends).
- **RQ2.** Can insufficient evidence be detected at inference time?
  **H2:** answer inconsistency across samples (self-consistency) and self-verification detect unanswerable cases better than raw verbalized confidence (which is overconfident per [arXiv:2306.13063](https://arxiv.org/abs/2306.13063)).
- **RQ3.** How should uncertainty be expressed — what maximizes correct abstention without over-refusal?
  **H3:** abstention prompts cut hallucination substantially but also raise over-refusal on answerable/inferable questions; the risk–coverage trade-off differs across models.
- **RQ4 (epistemic gradient).** Do models treat *inferable* (B) like *stated* (A) or like *absent* (C)?
  **H4:** abstention strategies disproportionately hurt category B — models can't separate "requires inference" from "not present."

---

## 4. Resources

### 4.1 Datasets (sources for our eval set)

| Resource | What | How we use it | Link |
|---|---|---|---|
| **Spoken-SQuAD** | TTS-read SQuAD passages + QA (37k train / 5.3k test) | Primary source of (audio passage, answerable Q) pairs; we add B/C questions per passage | [GitHub](https://github.com/Chia-Hsuan-Lee/Spoken-SQuAD) · [HF mirror](https://huggingface.co/datasets/AudioLLMs/spoken_squad_test) · [alinet/spoken_squad](https://huggingface.co/datasets/alinet/spoken_squad) |
| **SQuAD 2.0** | 50k+ adversarial unanswerable questions (text) | Recipe + ready unanswerables for passages we TTS ourselves | [arXiv:1806.03822](https://arxiv.org/abs/1806.03822) |
| **LibriSpeech** | 1000h read audiobooks + transcripts | Natural (non-TTS) audio for robustness slice | [openslr.org/12](https://www.openslr.org/12/) |
| **Own TTS pipeline** | Synthesize short passages → full control of content | Generate paired A/B/C questions from the same passage; multiple voices | [edge-tts](https://github.com/rany2/edge-tts) (free) or [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) (local, Apache-2.0) |
| Context benchmarks | MMAU / AudioBench / SAKURA / AQUA-Bench / HalluAudio | Protocol & metric reference; possible transfer eval later | links in §2 |

### 4.2 Models

| Model | Role | Notes | Link |
|---|---|---|---|
| **Qwen2-Audio-7B-Instruct** | Primary open Speech LLM | Best-documented HF integration (`transformers`), fits 1×A100/Colab | [HF](https://huggingface.co/Qwen/Qwen2-Audio-7B-Instruct) · [arXiv:2407.10759](https://arxiv.org/abs/2407.10759) |
| **Qwen2.5-Omni-7B** | Newer generation | Thinker–Talker; compare generational progress | [HF](https://huggingface.co/Qwen/Qwen2.5-Omni-7B) · [arXiv:2503.20215](https://arxiv.org/abs/2503.20215) |
| **SALMONN (13B/7B)** | Different architecture family | Whisper+BEATs encoders → Vicuna; heavier setup | [GitHub](https://github.com/bytedance/SALMONN) · [arXiv:2310.13289](https://arxiv.org/abs/2310.13289) |
| **Cascade: Whisper → text LLM** | Key ablation | whisper-large-v3 + Qwen2.5-7B-Instruct; separates "didn't hear" from "can't reason about evidence" | [arXiv:2212.04356](https://arxiv.org/abs/2212.04356) |
| *(optional)* GPT-4o-audio / Gemini 2.x | Closed-source reference | Only if API budget allows; not on critical path | — |

### 4.3 Tooling

`transformers` + `torch` + `soundfile/librosa`; `edge-tts`/Kokoro for synthesis; `pandas` + `matplotlib` for analysis; LLM-as-judge via a cheap API (e.g., `gpt-4o-mini`/DeepSeek) **or** local Qwen2.5-7B-Instruct — judge choice is config-driven; W&B or plain JSONL logs in `results/`.

---

## 5. Evaluation set design (v0.1 spec)

**Unit:** `(audio, question, category, gold)` in JSONL (canonical field-by-field schema: [PLAN.md §2](PLAN.md)):

```json
{"id": "sq-0421-C2", "audio_path": "audio/sq-0421.wav", "transcript": "...",
 "question": "What color was the speaker's jacket?", "category": "C",
 "subtype": "absent-attribute", "gold_answer": "UNANSWERABLE",
 "source": "spoken-squad", "generator": "gpt-4o-mini/v2-prompt", "verified_by": "M3"}
```

**Categories & subtypes:**

- **A — Answerable (stated):** span extractable from the audio. Source: existing Spoken-SQuAD QA.
- **B — Reasoning-based (inferable):** requires 1-hop inference/aggregation over what is said (negation, comparison, arithmetic on stated facts, paralinguistics optional). Generated by LLM from transcript, human-checked.
- **C — Unanswerable (absent):** plausible but unsupported. Subtypes to enable fine-grained analysis:
  - `C1 absent-entity` — asks about an entity never mentioned;
  - `C2 absent-attribute` — entity mentioned, attribute not (the brief's jacket example);
  - `C3 false-premise` — question presupposes something contradicting the audio;
  - `C4 off-topic` — question unrelated to the audio domain.

**Generation:** category-specific LLM prompts over **transcripts** (never the audio), temperature-varied, k candidates → filter by rules (no yes/no for C, no answer leakage) → **human verification**: every item labeled by one non-author teammate; disagreement → joint adjudication. We log inter-annotator agreement on a calibration round.

**Sizes:** pilot **90–120 items** (30–40 per category) by Jul 10 → **~600–900 items** in the main phase, balanced across categories and subtypes, ~50/50 TTS vs natural audio.

---

## 6. Experiments

### E1 — Baseline behavior (RQ1) · *pre-defense pilot*
Grid: {Qwen2-Audio, cascade} × {plain prompt} × pilot set. Classify each response as **answer / abstain / hedge** (judge + regex for refusal phrases). Main numbers: hallucination rate on C, accuracy on A/B.

### E2 — Inference-time mitigation (RQ2, RQ3) · *main phase, prompts drafted now*
Same grid plus strategies, each vs E1:
1. **S1 IDK-prompt:** "Answer only if the audio supports it; otherwise say the audio does not provide that information."
2. **S2 Explicit option:** append "cannot be determined from the audio" as an explicit valid choice.
3. **S3 Self-verification (CoVe-style):** stage 1 answer → stage 2 "Is this answer supported by the audio? Revise."
4. **S4 Self-consistency:** k=5 samples at T=0.7; agreement < θ ⇒ abstain (θ swept).
5. **S5 Verbalized confidence:** 0–100 confidence; threshold swept → risk–coverage curve.

### E3 — Epistemic analysis (RQ4)
A/B/C (and C-subtype) breakdowns; error taxonomy on C (fabrication vs hedged guess vs correct refusal); over-refusal on B as the key cost metric; cascade vs end-to-end comparison; (stretch) token-logprob signals, audio corruption (noise/truncation) as "evidence degradation" dial.

### Metrics (module `src/metrics.py`)
- Per category: accuracy (A, B), **hallucination rate** = answered-and-wrong / total (C), **correct-abstain rate** (C), **over-refusal rate** (A∪B).
- Selective prediction: risk–coverage curve, **AURC**; abstention F1 over {answer, abstain}.
- **Reliability Gain Index (RGI)** from [arXiv:2505.19294](https://arxiv.org/abs/2505.19294) for comparability.
- Judge: fixed rubric, versioned prompt, human audit.

---

## 7. Scope tiers — what we can claim at each level

Execution mechanics (scope tables, the Jul 10 checkpoint, switching rules, add-on ladder) live in [PLAN.md §4](PLAN.md). Here — the science: each tier contains the previous one, and each adds claims.

### Tier 1 — MINIMUM (emergency floor)
The smallest experiment that yields a defensible claim: one model, plain vs S1, 60 items, manual grading.
**RQ coverage:** RQ1 fully; RQ3 as a two-point trade-off; RQ2 not covered; RQ4 indicative only (20 items/category).
**Defensible claims:** "Qwen2-Audio answers **X%** of unanswerable spoken questions under a plain prompt" and "a one-line IDK instruction lowers that to **Y%** at the cost of **Z%** over-refusal" — exact counts with Wilson 95% intervals, framed as *pilot evidence*.
**Deliberately NOT claimed:** cross-model comparisons, detection mechanisms, calibration, subtype taxonomy.

### Tier 2 — MEDIUM (default = this proposal)
Everything in Tier 1, extended to a comparative study: 3 systems (adds cascade + Qwen2.5-Omni), strategies S1–S5, LLM-judge with human audit, 600–900 items.
**RQ coverage:** all of RQ1–RQ4; hypotheses H1–H4 (§3) all testable.
**Defensible claims:** first free-form (non-MCQ) unanswerability numbers on spoken content; a strategy ranking with explicit costs on risk–coverage curves; the "hearing vs epistemic reasoning" attribution via the cascade–end-to-end gap; RGI values directly comparable with Ma et al.

### Tier 3 — MAXIMUM (stretch)
Everything in Tier 2, pushed to a publishable study. Four extended research questions:
**RQ5 (degradation dial):** does abstention rise gracefully as evidence degrades (noise/truncation), or collapse? · **RQ6 (prompting vs tuning):** how much of ideal refusal do inference-time methods recover vs a small LoRA refusal-tune? · **RQ7 (internal vs verbalized signals):** do logprob/semantic-entropy detectors beat stated confidence (AUROC)? · **RQ8 (external validity):** do findings transfer to AQUA-Bench / HalluAudio speech subsets?
**Defensible claims** (each maps to one add-on-ladder rung; dropping a rung removes exactly one claim): 5-system leaderboard · degradation curves · detector AUROC comparison · prompting-vs-tuning verdict · transfer statement · public HF dataset + workshop paper draft.

---

## 8. Risks

| Risk | Mitigation |
|---|---|
| No GPU until approval | Pilot sized for Colab free tier / CPU (Qwen2-Audio-7B int8; ≤120 items; cascade is cheap). Everything config-driven so scaling up is a config change |
| AQUA-Bench "already did it" objection | Positioning ready (§2.1): speech content + free-form + mitigation comparison + epistemic gradient. Cite and build on it, don't compete on MCQ |
| Generated C-questions secretly answerable | Non-author verification of 100% of pilot; calibration round with agreement stats |
| SALMONN/Omni setup friction | Strict priority: Qwen2-Audio → cascade → Omni → SALMONN; first two suffice for pre-defense |
| Judge unreliability | Versioned rubric, human audit, exact-match fallback for span answers |
| Over-refusal hides behind good C numbers | Always report accuracy on A/B alongside abstention on C; risk–coverage curves make the trade-off explicit |
| Only 3 confirmed members (4th uncertain) | Plan is complete with 3: the flex workstream is severable; onboarding rule and main-phase scope dial in [PLAN.md](PLAN.md) §1, §8 |

---

## 9. References (all verified via arXiv/Crossref)

```bibtex
@online{rajpurkar2018know,  author={Pranav Rajpurkar and Robin Jia and Percy Liang},
  title={Know What You Don't Know: Unanswerable Questions for {SQuAD}},
  year={2018}, eprinttype={arXiv}, eprint={1806.03822}, url={https://arxiv.org/abs/1806.03822}}
@online{li2018spoken,       author={Chia-Hsuan Li and Szu-Lin Wu and Chi-Liang Liu and Hung-yi Lee},
  title={Spoken {SQuAD}: A Study of Mitigating the Impact of Speech Recognition Errors on Listening Comprehension},
  year={2018}, eprinttype={arXiv}, eprint={1804.00320}, url={https://arxiv.org/abs/1804.00320}}
@online{yin2023selfaware,   author={Zhangyue Yin and Qiushi Sun and Qipeng Guo and Jiawen Wu and Xipeng Qiu and Xuanjing Huang},
  title={Do Large Language Models Know What They Don't Know?},
  year={2023}, eprinttype={arXiv}, eprint={2305.18153}, url={https://arxiv.org/abs/2305.18153}}
@online{kirichenko2025abstentionbench, author={Polina Kirichenko and Mark Ibrahim and Kamalika Chaudhuri and Samuel J. Bell},
  title={{AbstentionBench}: Reasoning {LLMs} Fail on Unanswerable Questions},
  year={2025}, eprinttype={arXiv}, eprint={2506.09038}, url={https://arxiv.org/abs/2506.09038}}
@article{wen2025know,       author={Bingbing Wen and Jihan Yao and Shangbin Feng and Chenjun Xu and Yulia Tsvetkov and Bill Howe and Lucy Lu Wang},
  title={Know Your Limits: A Survey of Abstention in Large Language Models},
  journal={Transactions of the Association for Computational Linguistics}, year={2025}, doi={10.1162/tacl_a_00754}}
@online{zhang2023rtuning,   author={Hanning Zhang and Shizhe Diao and Yong Lin and Yi R. Fung and Qing Lian and Xingyao Wang and Yangyi Chen and Heng Ji and Tong Zhang},
  title={{R-Tuning}: Instructing Large Language Models to Say `I Don't Know'},
  year={2023}, eprinttype={arXiv}, eprint={2311.09677}, url={https://arxiv.org/abs/2311.09677}}
@online{kuhn2023semantic,   author={Lorenz Kuhn and Yarin Gal and Sebastian Farquhar},
  title={Semantic Uncertainty: Linguistic Invariances for Uncertainty Estimation in Natural Language Generation},
  year={2023}, eprinttype={arXiv}, eprint={2302.09664}, url={https://arxiv.org/abs/2302.09664}}
@article{farquhar2024detecting, author={Sebastian Farquhar and Jannik Kossen and Lorenz Kuhn and Yarin Gal},
  title={Detecting hallucinations in large language models using semantic entropy},
  journal={Nature}, year={2024}, doi={10.1038/s41586-024-07421-0}}
@online{xiong2023can,       author={Miao Xiong and Zhiyuan Hu and Xinyang Lu and Yifei Li and Jie Fu and Junxian He and Bryan Hooi},
  title={Can {LLMs} Express Their Uncertainty? An Empirical Evaluation of Confidence Elicitation in {LLMs}},
  year={2023}, eprinttype={arXiv}, eprint={2306.13063}, url={https://arxiv.org/abs/2306.13063}}
@online{wang2022selfconsistency, author={Xuezhi Wang and Jason Wei and Dale Schuurmans and Quoc Le and Ed Chi and Sharan Narang and Aakanksha Chowdhery and Denny Zhou},
  title={Self-Consistency Improves Chain of Thought Reasoning in Language Models},
  year={2022}, eprinttype={arXiv}, eprint={2203.11171}, url={https://arxiv.org/abs/2203.11171}}
@online{dhuliawala2023cove, author={Shehzaad Dhuliawala and Mojtaba Komeili and Jing Xu and Roberta Raileanu and Xian Li and Asli Celikyilmaz and Jason Weston},
  title={Chain-of-Verification Reduces Hallucination in Large Language Models},
  year={2023}, eprinttype={arXiv}, eprint={2309.11495}, url={https://arxiv.org/abs/2309.11495}}
@online{chu2024qwen2audio,  author={Yunfei Chu and Jin Xu and Qian Yang and Haojie Wei and Xipin Wei and Zhifang Guo and Yichong Leng and Yuanjun Lv and Jinzheng He and Junyang Lin and Chang Zhou and Jingren Zhou},
  title={{Qwen2-Audio} Technical Report},
  year={2024}, eprinttype={arXiv}, eprint={2407.10759}, url={https://arxiv.org/abs/2407.10759}}
@online{xu2025qwen25omni,   author={Jin Xu and Zhifang Guo and Jinzheng He and Hangrui Hu and Ting He and Shuai Bai and Keqin Chen and Jialin Wang and Yang Fan and Kai Dang and Bin Zhang and Xiong Wang and Yunfei Chu and Junyang Lin},
  title={{Qwen2.5-Omni} Technical Report},
  year={2025}, eprinttype={arXiv}, eprint={2503.20215}, url={https://arxiv.org/abs/2503.20215}}
@online{tang2023salmonn,    author={Changli Tang and Wenyi Yu and Guangzhi Sun and Xianzhao Chen and Tian Tan and Wei Li and Lu Lu and Zejun Ma and Chao Zhang},
  title={{SALMONN}: Towards Generic Hearing Abilities for Large Language Models},
  year={2023}, eprinttype={arXiv}, eprint={2310.13289}, url={https://arxiv.org/abs/2310.13289}}
@online{radford2022whisper, author={Alec Radford and Jong Wook Kim and Tao Xu and Greg Brockman and Christine McLeavey and Ilya Sutskever},
  title={Robust Speech Recognition via Large-Scale Weak Supervision},
  year={2022}, eprinttype={arXiv}, eprint={2212.04356}, url={https://arxiv.org/abs/2212.04356}}
@online{sakshi2024mmau,     author={S Sakshi and Utkarsh Tyagi and Sonal Kumar and Ashish Seth and Ramaneswaran Selvakumar and Oriol Nieto and Ramani Duraiswami and Sreyan Ghosh and Dinesh Manocha},
  title={{MMAU}: A Massive Multi-Task Audio Understanding and Reasoning Benchmark},
  year={2024}, eprinttype={arXiv}, eprint={2410.19168}, url={https://arxiv.org/abs/2410.19168}}
@online{wang2024audiobench, author={Bin Wang and Xunlong Zou and Geyu Lin and Shuo Sun and Zhuohan Liu and Wenyu Zhang and Zhengyuan Liu and AiTi Aw and Nancy F. Chen},
  title={{AudioBench}: A Universal Benchmark for Audio Large Language Models},
  year={2024}, eprinttype={arXiv}, eprint={2406.16020}, url={https://arxiv.org/abs/2406.16020}}
@online{yang2025sakura,     author={Chih-Kai Yang and Neo Ho and Yen-Ting Piao and Hung-yi Lee},
  title={{SAKURA}: On the Multi-hop Reasoning of Large Audio-Language Models Based on Speech and Audio Information},
  year={2025}, eprinttype={arXiv}, eprint={2505.13237}, url={https://arxiv.org/abs/2505.13237}}
@online{kuan2024understanding, author={Chun-Yi Kuan and Wei-Ping Huang and Hung-yi Lee},
  title={Understanding Sounds, Missing the Questions: The Challenge of Object Hallucination in Large Audio-Language Models},
  year={2024}, eprinttype={arXiv}, eprint={2406.08402}, url={https://arxiv.org/abs/2406.08402}}
@online{kuan2024trulyhear,  author={Chun-Yi Kuan and Hung-yi Lee},
  title={Can Large Audio-Language Models Truly Hear? Tackling Hallucinations with Multi-Task Assessment and Stepwise Audio Reasoning},
  year={2024}, eprinttype={arXiv}, eprint={2410.16130}, url={https://arxiv.org/abs/2410.16130}}
@online{ma2025reliable,     author={Ziyang Ma and Xiquan Li and Yakun Song and Wenxi Chen and Chenpeng Du and Jian Wu and Yuanzhe Chen and Zhuo Chen and Yuping Wang and Yuxuan Wang and Xie Chen},
  title={Towards Reliable Large Audio Language Model},
  year={2025}, eprinttype={arXiv}, eprint={2505.19294}, url={https://arxiv.org/abs/2505.19294}}
@online{kuan2026aquabench,  author={Chun-Yi Kuan and Hung-yi Lee},
  title={{AQUA-Bench}: Beyond Finding Answers to Knowing When There Are None in Audio Question Answering},
  year={2026}, eprinttype={arXiv}, eprint={2601.12248}, url={https://arxiv.org/abs/2601.12248}}
@online{zhao2026halluaudio, author={Feiyu Zhao and Yiming Chen and Wenhuan Lu and Daipeng Zhang and Xianghu Yue and Jianguo Wei},
  title={{HalluAudio}: A Comprehensive Benchmark for Hallucination Detection in Large Audio-Language Models},
  year={2026}, eprinttype={arXiv}, eprint={2604.19300}, url={https://arxiv.org/abs/2604.19300}}
```
