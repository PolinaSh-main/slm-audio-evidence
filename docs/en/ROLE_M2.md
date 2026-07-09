# Role M2 — Data Lead: build the test set

**How to read this file:** it explains your tasks step by step and explains every technical word the first time it appears. You can start working from this file alone. Links are only for going deeper: [full proposal](PROPOSAL.md) · [execution plan](PLAN.md) · [glossary](GLOSSARY.md) · [papers guide](../../papers/README.md) · [русская версия](../ru/ROLE_M2.md).

## The project in plain words

- A **Speech LLM** is an AI model: sound recording + written question in, text answer out.
- Problem: when the recording does not contain the answer, models invent one (a **hallucination**). Audio: "I like apples." Question: "What color was the jacket?" Model: "Blue."
- We test this with recordings and three kinds of questions: **A** — the answer is spoken in the recording; **B** — not spoken, but can be figured out from what was said; **C** — not in the recording at all (the model should refuse to answer).
- **Everything the team measures runs on the data you build.** If a "C" question is secretly answerable, every number downstream is wrong. Your care = the project's quality.
- Deliverable: a code repository + slides by **July 12, 23:00 UTC+3**; your frozen dataset is due **July 10**.

## Words used in this file

| Word | Plain meaning |
|---|---|
| Dataset | A collection of test examples |
| Test split | The ready-made "testing" part of a public dataset |
| Hugging Face (HF) | A website with ready AI models and datasets; `datasets` is its Python library for downloading them |
| Passage | One short spoken text (20–60 seconds of audio) |
| Transcript | The written text of what is said in a recording |
| TTS | Text-to-speech: a program that reads text aloud into an audio file |
| wav, 16 kHz mono | A standard audio format models expect (one channel, 16,000 measurements per second) |
| CSV | A simple table saved as text (rows and commas); opens in Excel |
| Prompt / prompt template | The instruction text we send to an AI model / its reusable version with blanks like `{transcript}` |
| Oversample (3×) | Generate three times more candidates than needed, so you can throw away the bad ones |
| Filter | A script that automatically rejects bad candidates by simple rules |
| Fuzzy match | Comparing two texts approximately, so small wording differences still count as "same" |
| JSONL | A text file where every line is one record like `{"id": "x", "question": "…"}` |
| Manifest | The JSONL file listing all test items — your main product |
| Schema | The agreed set of fields every record must have; never change it silently |
| Annotator / verification | A person who checks an item / the checking process |
| Agreement | The % of items where two checkers give the same verdict — shows the labels can be trusted |
| Freeze | Declaring the dataset final: after this, no edits, only documented new versions |
| Data card | A one-page document describing a dataset: what's inside, how it was built, what its limits are |
| Validator | A small script that checks every record has all fields, ids are unique, files exist |

## Your mission

Build a test set where every label can be trusted. Take ready-made audio, generate B and C questions with a chat AI **from transcripts** (never from audio), filter them mechanically, then have every item checked by a teammate who didn't create it. Deliver the frozen manifest and a data card.

---

## The record format (the whole team depends on this)

Your product is `data/manifests/pilot.jsonl`. One line = one test item:

```json
{"id": "sq-0421-C2",               // unique id: source–passage number–category+number
 "audio_path": "data/audio/….wav", // the sound file
 "transcript": "…",                // exact text of what is said
 "question": "What color was the speaker's jacket?",
 "category": "C",                  // A, B or C
 "subtype": "absent-attribute",    // A: "stated" · B: "inference" · C: see Task 2
 "gold_answer": "UNANSWERABLE",    // the correct answer; for C always the word UNANSWERABLE
 "source": "spoken-squad",         // where the audio came from: spoken-squad or tts
 "generator": "gpt-4o-mini/b-v2",  // which model/prompt-version made the question ("native" = original dataset question)
 "verified_by": "M3"}              // who checked it — never the person who made it
```

If a field must change, tell everyone the same day via `docs/decisions.md` (our decisions log).

---

## Task 1 — Get audio and passages · finish **July 8**

**Why:** we don't record anything ourselves — a ready dataset gives us audio + transcripts + A-questions for free.

1. Download the Spoken-SQuAD test split from HF: [AudioLLMs/spoken_squad_test](https://huggingface.co/datasets/AudioLLMs/spoken_squad_test) (in Python: `datasets.load_dataset(...)`). Backups: [alinet/spoken_squad](https://huggingface.co/datasets/alinet/spoken_squad), [official GitHub](https://github.com/Chia-Hsuan-Lee/Spoken-SQuAD) — careful, the full GitHub audio is ~50 GB; take only what you need.
2. Pick **40 passages**: 20–60 s long, clear voice, and the transcript contains at least 3 concrete facts (names, numbers, dates) — facts are the raw material for questions. Save the list as `data/generation/passages.csv` (id, transcript, duration, number of facts).
3. Category A for free: for each passage keep 1 original question with its answer from the dataset.
4. Write `data/generation/tts_fallback.py` using [edge-tts](https://github.com/rany2/edge-tts) (free, no registration): give it text, get a 16 kHz mono wav. This is your backup if some audio file is broken.

**You are done when:** passages.csv has 40 rows, the audio plays, each passage has an A-question, and the TTS script produces a playable wav from any sentence.

## Task 2 — Generate B and C questions · finish **July 9**

Use any capable chat AI (ChatGPT-like). Always paste the **transcript**, never the audio. Generate **3× more than needed** (target after filtering: 30–40 per category). Save the exact prompt texts in `data/generation/prompts/` with version names (`b-v1.txt`, `c1-v1.txt`, …) — if you improve a prompt, save it as v2, don't overwrite.

The prompts (copy-paste ready):

- **B — answer must be figured out, not quoted** (`b-v1.txt`):
  > Here is a transcript of a short audio passage: "{transcript}". Write ONE question whose answer is NOT stated word-for-word but CAN be logically inferred from the transcript (negation, comparison, simple arithmetic, cause/effect). Also give the correct answer and quote the sentence(s) the inference rests on. Do not ask yes/no questions. Format: QUESTION: … ANSWER: … EVIDENCE: …
- **C1 — about a thing never mentioned** (`c1-v1.txt`):
  > …Write ONE natural question about a person, object, or place that is NEVER mentioned in the transcript but plausibly could appear in such a passage. The transcript must contain NO information to answer it. Not a yes/no question. Format: QUESTION: …
- **C2 — thing mentioned, property not given** (`c2-v1.txt`):
  > …Pick an entity that IS mentioned. Ask about one of its attributes (color, size, age, price, reason, time…) that the transcript does NOT give. Not a yes/no question. Format: QUESTION: … ENTITY: …
- **C3 — false premise** (`c3-v1.txt`): a question that assumes something the transcript contradicts (the right reaction is to object). *Only in the default Tier 2 scope.*
- **C4 — off-topic** (`c4-v1.txt`): a question from a completely different subject. *Tier 2 only.*

Then run your filter script `data/generation/filter.py`, which automatically rejects: yes/no questions; C-questions whose key words appear in the transcript (plain match + fuzzy match — they might be answerable!); duplicates within a passage; questions shorter than 5 or longer than 25 words.

**You are done when:** `candidates.jsonl` holds ≥90 B and ≥180 C candidates, each with `generator` filled in, and the filter log shows what was rejected and why.

## Task 3 — Verification and freeze · finish **July 10** ⚠ M3's experiment waits for this

**Why:** an AI generated the questions, so an AI also made mistakes. Humans catch them. This protocol also goes into the data card.

1. Give every candidate to a checker who **did not create it** (you generated → M1 and M3 check; split evenly, ~60–90 items each ≈ 30–45 minutes).
2. The checker answers four questions per item: (a) is the category/subtype label right? (b) for B — does the reasoning really work, with one clear answer? (c) for C — is it truly unanswerable **from the transcript** (not stated AND not inferable)? (d) does the question sound natural?
3. Verdicts: `ok` / `fix` (edit, then same person re-checks) / `drop`. Record verdicts in `data/generation/verification.csv`.
4. **Calibration:** on the first 20 items M1 and M3 check independently, and you compute the % of items where they agree. Below 80% → the three of you discuss the rules, align, and only then continue. Report this agreement number in the data card and on your slide — it is your credibility proof.
5. Balance and freeze: 90–120 items total, at least 30 per category, C spread over subtypes, `verified_by` filled everywhere. Commit as `data/manifests/pilot.jsonl` in a PR labeled `pilot-freeze`. After the freeze: no edits; fixes become a new file `pilot_v2.jsonl` plus a decisions-log entry.

**You are done when:** your validator script `data/generation/validate.py` passes (all fields present, ids unique, audio files exist) and the agreement number is computed.

## Task 4 — Data card · finish **July 11**

One page, `docs/data_card.md`: what this dataset is; the schema table (copy from above); each category/subtype defined with one real example; how it was built (source → prompts+versions → filters → verification → agreement number); a counts table; honest limitations (synthetic voice only, English only, one domain, small); how to extend it later.

**You are done when:** a stranger could read it and produce a compatible new item.

## Task 5 — Your slides · **July 9–11**

- Into `docs/related_work.md`: 3–5 plain bullets each on papers 04, 06 (this one is the ancestor of your C-questions — read its §2–3), 22, 23 from the [papers guide](../../papers/README.md).
- The "Dataset" slide: the A/B/C table with your real examples, the counts, and the verification story. **You present this slide.** Likely question: "how do you know the C-questions are really unanswerable?" — your answer: the non-author check + the agreement number.

## If plans shrink or grow

- **Fallback (decided July 10 evening):** freeze at 60 items (20/20/20), C = C1+C2 only. Nothing else changes for you.
- **Stretch:** natural (non-TTS) audio from LibriSpeech, questions about *how* speech sounds (emotion, speaker), noisy/cut audio versions — see [PLAN.md §4](PLAN.md).

## Your days

| Jul 8 | Jul 9 | Jul 10 | Jul 11 | Jul 12 |
|---|---|---|---|---|
| Task 1 | Task 2; related-work bullets | Task 3: verify + **freeze** | Task 4; dataset slide | buffer; re-run validator; rehearse |

## Reading order

Papers 01 and 02 (everyone, by the July 8 sync) → 06 (the unanswerable-question recipe) → 23, 22 → 04.

## Traps to avoid

- The #1 project killer: **a C-question the transcript actually implies.** When in doubt — `drop`; you generated 3× extra exactly for this.
- Chat AIs love making yes/no and vague "why" questions for C — the filter catches yes/no; vague "why" you catch by hand.
- Don't let B slide into A: a paraphrase of a spoken fact is A, not B.
- After the freeze never rename audio files — results reference them by path.
