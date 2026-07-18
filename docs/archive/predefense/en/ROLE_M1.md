# Role M1 — Team Lead: make everything run and fit together

**How to read this file:** it explains your tasks step by step and explains every technical word the first time it appears. You can start working from this file alone. Links are only for going deeper: [full proposal](PROPOSAL.md) · [execution plan](PLAN.md) · [glossary](../../../en/GLOSSARY.md) · [papers guide](../../../../papers/README.md) · [русская версия](../ru/ROLE_M1.md).

## The project in plain words

- A **Speech LLM** is an AI model. You give it a sound recording plus a written question. It answers in text.
- Problem: when the recording does not contain the answer, these models still answer — they invent facts. Audio: "I like apples." Question: "What color was the jacket?" Model: "Blue." An invented answer like this is called a **hallucination**.
- We build a test set of recordings with three kinds of questions: **A** — the answer is spoken in the recording; **B** — the answer is not spoken, but can be figured out from what was said; **C** — the answer is not in the recording at all. A good model answers A and B, and on C it says "the audio does not provide that information" — this is called **abstaining**.
- We measure how often models hallucinate on C, and whether a better instruction (a **prompt** — the text we send to the model together with the question) fixes it.
- Deliverable: a code repository + slides by **July 12, 23:00 UTC+3**, then a short Zoom defense of the plan.

## Words used in this file

| Word | Plain meaning |
|---|---|
| GitHub | A website where teams store code together |
| Repository (repo) | One project's folder on GitHub, with the full history of changes |
| Commit | One saved change in the repo |
| Branch | Your personal working copy inside the repo; you merge it into the shared `main` copy when ready |
| Pull request (PR) | A request to merge your branch into `main`; a teammate reads the change first (a "review") |
| pip / requirements.txt | Python's installer for libraries / the file listing which libraries our project needs |
| Terminal | The window where you type commands |
| Harness | Our runner script: takes each test item, sends it to a model, saves the answer to a file |
| Wrapper | A small piece of code that hides one model's quirks behind functions common to all models |
| Hugging Face (HF) | A website with ready AI models and datasets; `transformers` is its Python library that downloads and runs them |
| JSONL | A text file where every line is one record like `{"id": "x", "question": "…"}` |
| Manifest | The JSONL file listing all our test items |
| Schema | The agreed set of fields every record must have; changing it silently breaks teammates' code |
| Whisper / ASR | A speech-recognition model: audio in → written text out (ASR = automatic speech recognition) |
| Transcript | The written text of what is said in a recording |
| Cascade | Our two-step comparison system: Whisper writes the transcript, then a normal text model answers from it |
| int8 | Storing the model's numbers in a compact 8-bit format so it fits into less memory |
| GPU / VRAM | The graphics processor that runs models / its memory |
| Colab | Google's free service that runs Python notebooks on their GPUs — our only computing power for now |
| Temperature | A randomness dial; above 0 the model can answer differently each time it is asked |
| Smoke test | The quickest possible run that proves the pipeline works at all |
| Tag | A named snapshot of the repo, e.g. `v0.1-predefense` |

## Your mission

You make the machinery: the shared repo, the harness, the prompt files, and the final slide deck. You also coordinate: a 15-minute call every evening, a decisions log, and unblocking teammates. Important: **M3 cannot run the experiment until your harness works** (needed by July 9) **and M2's data is ready** (July 10) — check both every day.

---

## Task 1 — Create the repository · finish **July 8**

**Why:** everyone needs one shared place for code from day one.

1. The repo already exists: `slm-audio-evidence` ([github.com/ladnlav/slm-audio-evidence](https://github.com/ladnlav/slm-audio-evidence)). Decide with the team: private or public; write the decision into `docs/decisions.md` — a simple text file where we log every decision: date, what, why.
2. Commit the folder skeleton and say in README what each folder is for:
   `data/manifests` (test items) · `data/generation` (data-building scripts) · `src/models` (model wrappers) · `src/prompts` (prompt text files) · `configs` · `notebooks` · `results` (model outputs) · `docs`.
3. Add `requirements.txt` with: `torch, transformers, soundfile, librosa, pandas, matplotlib, jsonlines`. Anyone sets up with one command: `pip install -r requirements.txt`.
4. Add `.gitignore` — the list of files git must NOT store (audio files, `results/**/*.jsonl`, model checkpoints). Reason: they are big and change often.
5. Set the workflow rules: everyone works in own branches named `m1/…`, `m2/…`, `m3/…`; merging into `main` only through a PR with one review; no direct pushes.
6. Create a task board (columns: Backlog / In progress / Done) and add the tasks from all three role files.

**You are done when:** M2 and M3 have each merged a tiny test PR, and the board shows all tasks.

## Task 2 — Build the harness · finish **July 9** ⚠ M3 waits for this

**Goal in one sentence:** one terminal command runs a chosen model over all test items with a chosen prompt style and writes the answers to a file.

```
python -m src.inference --model qwen2audio --strategy plain --data data/manifests/pilot.jsonl --out results/
```

1. `src/models/base.py` — the common interface (a promise about what functions exist): every model wrapper implements
   `answer(audio_path, question, prompt_template, gen_kwargs) -> str` (give it a sound file and a question, get the model's text answer).
2. `src/models/qwen2_audio.py` — wrapper for [Qwen2-Audio-7B-Instruct](https://huggingface.co/Qwen/Qwen2-Audio-7B-Instruct), our main model. Use the `transformers` library. Copy the message format ("chat template") from the model's HF page **exactly** — small deviations quietly make answers worse. Support int8 loading so it fits Colab.
3. `src/models/cascade.py` — the cascade: Whisper (`openai/whisper-large-v3`) turns audio into a transcript, then the text model `Qwen/Qwen2.5-7B-Instruct` answers reading only that transcript. Why we need it: if even the cascade invents answers, the problem is in reasoning, not in hearing.
4. `src/inference.py` — the runner: read the manifest line by line, ask the model, append each answer to `results/<run_id>/responses.jsonl` (`run_id` = model_strategy_date). Make it resumable: if it crashes, restarting skips items already answered. Add `--limit N` to run only the first N items (for quick tests).
5. `--strategy` picks a prompt file from `src/prompts/` (Task 3) and any extra logic (see S4 there).

**The two record formats (schemas). Copy them exactly; if you must change a field, tell everyone the same day via `docs/decisions.md`.**

What you read (M2 makes this file):
```json
{"id": "sq-0421-C2",               // unique item id
 "audio_path": "data/audio/….wav", // the sound file
 "transcript": "…",                // what is said in it
 "question": "…",
 "category": "C",                  // A, B or C (see top of file)
 "subtype": "absent-attribute",    // finer label inside the category
 "gold_answer": "UNANSWERABLE",    // correct answer; the word UNANSWERABLE for category C
 "source": "spoken-squad", "generator": "…", "verified_by": "M3"}
```
What you write (M3 reads this file):
```json
{"id": "sq-0421-C2", "model": "qwen2audio", "strategy": "plain",
 "response": "…",                  // the model's answer text
 "samples": null,                  // list of 5 answers when strategy is s4 (else null)
 "latency_s": 3.1, "ts": "2026-07-11T14:02:11", "prompt_version": "plain.txt"}
```

**You are done when:** both models run end-to-end on 5 real items; a restart resumes instead of redoing; M3 confirms they can read your output file.

## Task 3 — Prompt files · finish **July 10**

**Why files, not code:** prompts as small text files can be versioned and compared; nothing is hidden inside the program.

- `src/prompts/plain.txt` (the neutral baseline):
  `Listen to the audio and answer the question. Question: {question}`
- `src/prompts/s1_idk.txt` (the "allowed to say I-don't-know" prompt — our first fix):
  `Listen to the audio and answer the question using ONLY information from the audio. If the audio does not contain the information needed, reply exactly: "The audio does not provide that information." Question: {question}`
- Stubs (files with only a comment saying what they will be): `s2_option.txt`, `s3_verify.txt`, `s5_confidence.txt` — implemented later or by M4.
- **S4 (self-consistency)** is logic, not a file: `--strategy s4_consistency` asks the same plain question **5 times with temperature 0.7** and saves all 5 answers into `samples`. Idea: if the 5 answers disagree, the model was guessing. M3 does the comparing.

**You are done when:** `--strategy plain | s1_idk | s4_consistency` all produce valid result files, and each response line records which prompt file was used.

## Task 4 — Colab notebook · finish **July 10**

**Why:** we have no GPU of our own until the project is approved — and a live notebook is strong "it already works" evidence at the defense.

1. Notebook `notebooks/colab_smoke_test.ipynb`: clone the repo → `pip install -r requirements.txt` → load 5 sample items (commit a small `mini.jsonl` + 5 short wav files) → run plain and s1 → print a small table.
2. Target: runs top-to-bottom in under 15 minutes on Colab's free GPU (T4).
3. Save the notebook **with outputs visible** and link it from the README.

## Task 5 — Final assembly · **July 12**

Merge all open PRs, write the real README (what the project is / how to install / how to run / team / pilot results table), create tag `v0.1-predefense`, submit the link. **Done when:** a fresh `git clone` plus the README steps reproduce the mini-table.

## Task 6 — Story and slides · **July 9–12**

1. Into `docs/related_work.md` write 3–5 plain bullets on papers 01, 02, 16, 19 from the [papers guide](../../../../papers/README.md). The one sentence you must own at the defense: *"The closest work, AQUA-Bench, tests multiple-choice unanswerability on general sounds; we test open-ended answers on spoken content, and we compare fixes, not just measure."*
2. Deck skeleton, 10 slides: problem+example → research questions → what exists / our gap → dataset (M2 fills) → models → experiments → how we measure → pilot numbers (M3 fills) → timeline+tiers → team.
3. You present the framing, the plan and the methods slide (methods goes to M4 only if they join by July 10). Rehearse July 12.

## Every day

Run the evening 15-minute sync; keep `docs/decisions.md`; watch the chain **your harness → M2's frozen data → M3's big run**; on **July 10 evening** call the tier decision (rules in [PLAN.md §4](PLAN.md): if data or harness isn't ready — we shrink scope to Tier 1, nothing else changes).

## Your days

| Jul 8 | Jul 9 | Jul 10 | Jul 11 | Jul 12 |
|---|---|---|---|---|
| Task 1; start Task 2 | finish Task 2; related-work bullets | Task 3; Task 4; deck skeleton; tier decision | merge PRs; README; help M3 | Task 5; rehearse; **submit** |

## Reading order

Papers 01 and 02 (everyone, by the July 8 sync) → 16 and 19 (for Task 2) → 13–15 (for Task 3) → 07–08 (deeper background).

## Traps to avoid

- Qwen2-Audio's chat template is strict — copy it from the model page, don't improvise.
- Models expect 16 kHz mono audio — convert inside the wrapper, not in the dataset.
- In Colab load the model once and loop over items; loading twice = out-of-memory.
- Clips longer than 30 seconds: cut them and note it in the response line.
- On July 11, pin exact library versions in `requirements.txt` — a surprise library update the night before the deadline is the classic demo killer.
