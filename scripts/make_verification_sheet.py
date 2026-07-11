"""Build verification sheets for the pilot freeze (ROLE_M2 Task 3).

Samples a balanced subset of generated B/C candidates (with a buffer over the
final quotas), assigns every item to a NON-AUTHOR checker (M1 or M3), and
duplicates the first CALIBRATION items into both sheets to measure agreement.

Checkers fill three columns in their CSV:
  verdict         ok | fix | drop
  fixed_question  only when verdict=fix — the corrected question text
  comment         optional, why

Checker questions per item (from docs/ru|en/ROLE_M2.md):
  (a) category/subtype label correct?  (b) B: inference valid, single answer?
  (c) C: truly unanswerable FROM THE TRANSCRIPT (not stated AND not inferable)?
  (d) question sounds natural?

Usage: py -3 scripts/make_verification_sheet.py
"""

from __future__ import annotations

import csv
import json
import random
from pathlib import Path

CANDIDATES = Path("data/generation/candidates.jsonl")
PASSAGES_CSV = Path("data/generation/passages.csv")
OUT_DIR = Path("data/generation/verification")  # gitignored (whitelist pattern) — working files

CHECKERS = ["M1", "M3"]  # M2 generated everything, so M2 never checks own items
CALIBRATION = 20         # first N items go to BOTH checkers to measure agreement

# Verify ~2x the final freeze quotas (final: B 30 · C1 12 · C2 12 · C3 8 · C4 8)
VERIFY_QUOTAS = {
    ("B", "inference"): 45,
    ("C", "absent-entity"): 18,
    ("C", "missing-attribute"): 18,
    ("C", "false-presupposition"): 12,
    ("C", "off-topic"): 12,
}

FIELDS = [
    "id", "passage_id", "category", "subtype", "question", "gold_answer",
    "support",       # B: evidence + why_not_A · C: why_unanswerable (generator's own justification)
    "transcript",
    "calibration",   # yes = item is in both sheets
    "checker",
    "verdict", "fixed_question", "comment",
]


def main() -> None:
    rng = random.Random(42)

    with PASSAGES_CSV.open("r", newline="", encoding="utf-8-sig") as f:
        transcripts = {r["id"]: r["transcript"] for r in csv.DictReader(f)}

    by_bucket: dict[tuple[str, str], list[dict]] = {k: [] for k in VERIFY_QUOTAS}
    seen_ids: set[str] = set()
    for line in CANDIDATES.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        key = (row.get("category"), row.get("subtype"))
        rid = row.get("id") or f"{row.get('passage_id')}-{row.get('category')}?"
        if key in by_bucket and rid not in seen_ids:
            seen_ids.add(rid)
            by_bucket[key].append(row)

    sampled: list[dict] = []
    for key, quota in VERIFY_QUOTAS.items():
        pool = by_bucket[key]
        rng.shuffle(pool)
        take = pool[:quota]
        if len(take) < quota:
            print(f"[!] only {len(take)}/{quota} candidates for {key}")
        sampled.extend(take)
    rng.shuffle(sampled)  # mix categories so calibration covers all types

    def to_sheet_row(row: dict, checker: str, calibration: bool) -> dict:
        support = (
            f"EVIDENCE: {row.get('evidence', '')} | WHY_NOT_A: {row.get('why_not_A', '')}"
            if row.get("category") == "B"
            else f"WHY_UNANSWERABLE: {row.get('why_unanswerable', '')}"
        )
        return {
            "id": row.get("id", ""),
            "passage_id": row.get("passage_id", ""),
            "category": row.get("category", ""),
            "subtype": row.get("subtype", ""),
            "question": row.get("question", ""),
            "gold_answer": row.get("gold_answer", ""),
            "support": support,
            "transcript": transcripts.get(str(row.get("passage_id")), "TRANSCRIPT NOT FOUND"),
            "calibration": "yes" if calibration else "",
            "checker": checker,
            "verdict": "", "fixed_question": "", "comment": "",
        }

    sheets: dict[str, list[dict]] = {c: [] for c in CHECKERS}
    for i, row in enumerate(sampled):
        if i < CALIBRATION:
            for checker in CHECKERS:
                sheets[checker].append(to_sheet_row(row, checker, calibration=True))
        else:
            checker = CHECKERS[i % len(CHECKERS)]
            sheets[checker].append(to_sheet_row(row, checker, calibration=False))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for checker, rows in sheets.items():
        out = OUT_DIR / f"verify_{checker}.csv"
        with out.open("w", newline="", encoding="utf-8-sig") as f:  # utf-8-sig -> opens clean in Excel
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        print(f"{out}: {len(rows)} items ({CALIBRATION} calibration + {len(rows) - CALIBRATION} own)")

    print(f"\nTotal sampled: {len(sampled)} · each checker grades ~{len(sheets['M1'])} rows (~40 min)")
    print("Fill 'verdict' (ok/fix/drop); for 'fix' also fill 'fixed_question'. Then run scripts/freeze_pilot.py")


if __name__ == "__main__":
    main()
