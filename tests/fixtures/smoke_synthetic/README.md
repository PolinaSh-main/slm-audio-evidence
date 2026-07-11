# Synthetic smoke fixture (for M3's dry run — no models needed)

12 invented items with **known correct metrics**, so `src/run_eval.py` can be tested end-to-end
and the numbers checked by hand. Audio files do not exist (the evaluator never opens audio).

## How to run (M3)

Point `run_eval.py` at these two files (constants at the top, or `--manifest/--responses` once argparse is added):

```
MANIFEST_PATH  = tests/fixtures/smoke_synthetic/manifest.jsonl
RESPONSES_PATH = tests/fixtures/smoke_synthetic/responses.jsonl
```

## Expected numbers (if your judge + metrics are correct)

Composition: 4 A / 3 B / 5 C.

| Metric | Expected | From which items |
|---|---|---|
| hallucination_rate (C, label=answer) | **2/5 = 40.0%** | syn-c3, syn-c4 |
| correct_refusal_rate (C, abstain) | **2/5 = 40.0%** | syn-c1, syn-c2 |
| hedge_rate_on_c | **1/5 = 20.0%** | syn-c5 ("Perhaps…") |
| accuracy_a | **2/4 = 50.0%** | correct: syn-a1, syn-a2 · wrong: syn-a3 · abstained: syn-a4 |
| over_refusal_rate (abstain on A∪B) | **2/7 ≈ 28.6%** | syn-a4, syn-b2 |
| refusal_precision / recall / F1 | **0.50 / 0.40 / 0.444** | tp=2, fp=2, fn=3 |
| accuracy_b | with the current stub (`False`): 0% — misleading; after the agreed fix (`None` = pending manual grading) B is excluded from accuracy until graded | syn-b1 is actually correct, syn-b3 is a hedge |

Expected labels, if you want to check item by item: a1 answer · a2 answer · a3 answer · a4 abstain · b1 answer · b2 abstain · b3 hedge · c1 abstain · c2 abstain · c3 answer · c4 answer · c5 hedge.
