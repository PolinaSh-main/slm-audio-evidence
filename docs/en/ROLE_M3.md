# ROLE M3 — Literature & the paper's text

Русская версия: [../ru/ROLE_M3.md](../ru/ROLE_M3.md) · Plan: [PLAN.md](PLAN.md) · Paper: [PAPER_OUTLINE.md](PAPER_OUTLINE.md)

**Mission.** You turn the papers nobody has read yet into the Related Work section, write the Introduction, and own terminology consistency and the quality of the final text.

**Context in 3 bullets:** the paper's story is fixed (PLAN §1: "the bottleneck is epistemic reasoning, not hearing" + probing as mitigation); your notes go to [../related_work.md](../related_work.md) — the Related Work section is assembled *from them*; nobody has read anything yet, so your conveyor is the team's knowledge supply.

## Stage A — reading conveyor (Jul 19–25, ~1 paper/day)

Order matters — closest work first: **01 → 02 → 03 → 26 → 27 → 25**, then skim 09. All PDFs are in `papers/` ([guide](../../papers/README.md)).

For each paper add to related_work.md **3–5 plain bullets**: (1) what task, (2) what they did in one sentence, (3) headline number, (4) how we differ / what we take. Not summaries — takeaways. How to read one paper: abstract → conclusions → method → results tables; **every number you carry into the notes must be found in the PDF itself** — never copy a number you haven't seen in the paper.

| # | Paper | Why you're reading it |
|---|---|---|
| 01 | AQUA-Bench | closest benchmark; we validate on it (A1) |
| 02 | Towards Reliable LALM | IDK-prompting + RGI metric — our S1's lineage |
| 03 | HalluAudio | another hallucination benchmark — one Related Work paragraph |
| 26 | LISTEN ("what does not hear") | *training-based* mitigation — our contrast: we are training-free |
| 27 | BALSa | same lab's alignment method — same contrast paragraph as 26 |
| 25 | Walking Through Uncertainty | the neighbor-lab work on *output-level* uncertainty; we are *pre-generation* — this contrast is the paper's key positioning sentence |
| 09 | abstention survey (skim) | vocabulary + citations for Introduction |

**Two extra tasks:**
- **Metrics naming table (by Jul 24):** map our metric names (hallucination rate, correct-abstain, over-refusal) to classic terms (FPR/recall/precision on the abstain class, selective-prediction terms). The mentor asked for this; it becomes a paper table. M2 checks the math reading.
- **Claim verification (rolling):** when a mentor/paper claim sounds off, check the primary source and note it in related_work.md. You already have one catch to record: "BALSa" and "what does not hear" are two different papers (27 vs 26) from the same lab.

## Stage B — your sections

- **Jul 23–29: Introduction + Related Work draft** in the paper repo (`paper/`): Intro = problem → pilot finding → gap → our contributions (3 bullets); RW = 4 paragraphs (audio-QA hallucination benchmarks · mitigation for audio LLMs · text-LLM probing/uncertainty · what nobody did = pre-generation probing for Speech LLMs).
- **Jul 30–Aug 1: consistency pass** over the whole paper: terms used identically everywhere (GLOSSARY is the reference — you maintain it), abbreviations expanded at first use, no orphan claims without citations.
- **Contribution section:** send M1 your 2–4 sentences by Jul 30.

## Done when

related_work.md has bullets for 01, 02, 03, 26, 27, 25 · metrics table exists · Intro+RW draft handed to M1 by Jul 29 · consistency pass done Aug 1.

**If stuck:** a paper is impenetrable → 30 minutes max, take abstract + conclusion + one results table, mark "needs M2's eyes" and move on. Better six papers at 80% than two at 100%.
