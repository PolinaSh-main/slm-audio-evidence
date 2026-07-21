# ROLE M2 — Experiments: scale set + runs

Русская версия: [../ru/ROLE_M2.md](../ru/ROLE_M2.md) · Plan: [PLAN.md](PLAN.md) · Paper: [PAPER_OUTLINE.md](PAPER_OUTLINE.md)

**Mission.** You are the main computational force: all of A1 (the native SQuAD 2.0 scale set and the runs on it) and the runs for A2, whose core is led by M1. Everything runs on DataSphere.

**Context in 3 bullets:** the harness already works end-to-end (`src/inference.py` + wrappers, 4 pilot runs done in Colab); pilot-100 is frozen — we never expand it; the probing method we transfer is paper 24 (transfer owner — M1; you need it at method level to understand what you are running).

## Stage A (Jul 19–29)

1. **A0 · DataSphere (Jul 19–20).** Adapt `notebooks/colab_run.ipynb` to DataSphere (M1 gives access). Smoke test: 5 pilot items through Qwen2-Audio. *Done when:* one full run reproduces on DataSphere.
2. **A1 · Native SQuAD 2.0 scale set (Jul 20–23).** We scale in-domain: SQuAD 2.0 has ~6k human-written unanswerable questions **for the same paragraphs** already in your `data.csv` pool.
   - **NMSQA recon (~1 h, Mon Jul 20):** pull the metadata of [voidful/NMSQA](https://huggingface.co/datasets/voidful/NMSQA) — its *test* split is the same SQuAD paragraphs read by 60 human speakers. Intersect its test paragraphs with SQuAD 2.0 dev unanswerables and report the counts to M1: how many C and A land on natural audio.
   - **Script `data/make_scale_manifest.py` (Jul 20–21):** download dev-v2.0.json → normalize contexts → join with `data.csv` (the clean SQuAD contexts are already there) → sample ~200 C (`is_impossible=true`, `gold_answer: "UNANSWERABLE"`) + ~200 A (answer = `answers[0].text`) across passages → manifest per PLAN §2: `generator: "native-squad2"`, C `subtype: "native-unanswerable"`, `source: "spoken-squad"` or `"nmsqa"`. If natural C ≥ ~100 — make the set two-part (e.g. ~200 TTS + ~150 natural). Spot-check 30 rows: audio matches paragraph. Composition approved by M1 (Decision 1, Mon–Tue).
   - **Runs (Jul 21–23):** both systems (Qwen2-Audio, cascade) × {plain, S1} on the scale set. Hand responses to M4 for judging.
   - *Done when:* manifest in `data/manifests/`, 4 runs in `results/`, M4 has the files. Wrappers, harness, and judge are unchanged.
3. **A2 · Computational runs supporting M1 (Jul 22–29).** The A2 core (design, probes, analysis) is led end-to-end by M1; your part is the compute on DataSphere:
   - **Representation capture (Jul 22–23):** run M1's capture code over pilot-100 (+ scale-set items), tensors → `results/probing/` **by Jul 23**.
   - **Sampling (Jul 23–24):** k≈10 answers per item (temperature > 0 — reuse the harness `samples` field); files to M4 for grading **by Jul 24**. The Fri Jul 24 checkpoint depends on these two deadlines.
   - **On M1's request (Jul 25–29):** runs and debugging for the attention probe and the mitigation measurements.
   - Insurance: if M1 is unavailable, you train the linear probes yourself from his spec.
   - *Done when:* tensors (Jul 23) and samples (Jul 24) delivered; M1's requests closed.
4. **Stop Wed Jul 29** — freeze all result files; no new runs after this.

## Stage B — two sections

- **Task & Dataset (draft Jul 23–29):** pilot-100 as diagnostic set (construction, A/B/C, 80% agreement, freeze) + scale-set construction (native SQuAD 2.0, NMSQA slice, spot-check).
- **Experiments & Results (Jul 29–31, with M4):** all tables and plots; every number reproducible from `results/`.

## Reading (by Wed Jul 22)

| Paper | Read for | Depth |
|---|---|---|
| 24 — attention probing | understanding what you are running for M1 | method + results |
| 01 — AQUA-Bench | positioning (closest work; not our validation set) | skim |
| 16 — Qwen2-Audio | running the capture code (encoder → LLM interface) | skim |

**If stuck:** >half a day on one bug → write M1 + try the fallback (Colab/Kaggle path still works). Design doubts → paper 24 first, then M1.
