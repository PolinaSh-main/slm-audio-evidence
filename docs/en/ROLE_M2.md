# ROLE M2 — Experiments: AQUA runs + probing

Русская версия: [../ru/ROLE_M2.md](../ru/ROLE_M2.md) · Plan: [PLAN.md](PLAN.md) · Paper: [PAPER_OUTLINE.md](PAPER_OUTLINE.md)

**Mission.** You are the main computational force: all of A1 (scaling the pilot finding to AQUA-Bench) and the runs for A2, whose core is led by M1. Everything runs on DataSphere.

**Context in 3 bullets:** the harness already works end-to-end (`src/inference.py` + wrappers, 4 pilot runs done in Colab); pilot-100 is frozen — we never expand it; the probing method we transfer is paper 24 (transfer owner — M1; you need it at method level to understand what you are running).

## Stage A (Jul 19–29)

1. **A0 · DataSphere (Jul 19–20).** Adapt `notebooks/colab_run.ipynb` to DataSphere (M1 gives access). Smoke test: 5 pilot items through Qwen2-Audio. *Done when:* one full run reproduces on DataSphere.
2. **A1 · AQUA-Bench (Jul 20–23).**
   - Get the AQUA-Bench data (paper 01 links its repo/HF page).
   - Pick a speech-relevant subset (~200–400 items, answerable + unanswerable), convert into our manifest schema (PLAN §2, `source: "aqua-bench"`).
   - **Propose to M1 (Mon Jul 20):** keep MCQ / convert free-form / both — one short message with your recommendation.
   - Run **both systems** (Qwen2-Audio, cascade) × {plain, S1}. Hand responses to M4 for judging.
   - *Done when:* 4 runs × AQUA subset exist in `results/`, M4 has the files.
3. **A2 · Computational runs supporting M1 (Jul 22–29).** The A2 core (design, probes, analysis) is led end-to-end by M1; your part is the compute on DataSphere:
   - **Representation capture (Jul 22–23):** run M1's capture code over pilot-100 (+ AQUA items), tensors → `results/probing/` **by Jul 23**.
   - **Sampling (Jul 23–24):** k≈10 answers per item (temperature > 0 — reuse the harness `samples` field); files to M4 for grading **by Jul 24**. The Fri Jul 24 checkpoint depends on these two deadlines.
   - **On M1's request (Jul 25–29):** runs and debugging for the attention probe and the mitigation measurements.
   - Insurance: if M1 is unavailable, you train the linear probes yourself from his spec.
   - *Done when:* tensors (Jul 23) and samples (Jul 24) delivered; M1's requests closed.
4. **Stop Wed Jul 29** — freeze all result files; no new runs after this.

## Stage B — two sections

- **Task & Dataset (draft Jul 23–29):** pilot-100 as diagnostic set (construction, A/B/C, 80% agreement, freeze) + AQUA conversion procedure.
- **Experiments & Results (Jul 29–31, with M4):** all tables and plots; every number reproducible from `results/`.

## Reading (by Wed Jul 22)

| Paper | Read for | Depth |
|---|---|---|
| 24 — attention probing | understanding what you are running for M1 | method + results |
| 01 — AQUA-Bench | conversion decisions | data + eval sections |
| 16 — Qwen2-Audio | running the capture code (encoder → LLM interface) | skim |

**If stuck:** >half a day on one bug → write M1 + try the fallback (Colab/Kaggle path still works). Design doubts → paper 24 first, then M1.
