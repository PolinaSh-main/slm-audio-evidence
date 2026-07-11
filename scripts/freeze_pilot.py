"""Freeze data/manifests/pilot.jsonl from filled verification sheets (ROLE_M2 Task 3, step 5).

Reads verify_M1.csv + verify_M3.csv (verdicts filled), computes calibration
agreement, resolves verdicts (disagreement on a calibration item -> drop + report),
tops up to the final quotas, adds native A-questions, and writes the frozen
manifest in the PLAN.md section-2 schema.

Usage: py -3 scripts/freeze_pilot.py [--out data/manifests/pilot.jsonl]
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from collections import Counter
from pathlib import Path

SHEETS = [Path("data/generation/verification/verify_M1.csv"),
          Path("data/generation/verification/verify_M3.csv")]
PASSAGES_CSV = Path("data/generation/passages.csv")
QUESTIONS_A_CSV = Path("data/generation/questions_a.csv")
AUDIO_DIR = Path("data/audio/spoken_squad_test")
AUDIO_PATTERNS = ["{pid}.wav", "{pid}.WAV"]  # extend after checking real filenames

FINAL_QUOTAS = {
    ("B", "inference"): 30,
    ("C", "absent-entity"): 12,
    ("C", "missing-attribute"): 12,
    ("C", "false-presupposition"): 8,
    ("C", "off-topic"): 8,
}
N_A = 30  # native SQuAD questions (spot-check a handful by ear/eye before freezing)


def audio_path_for(passage_id: str) -> tuple[str, bool]:
    for pattern in AUDIO_PATTERNS:
        candidate = AUDIO_DIR / pattern.format(pid=passage_id)
        if candidate.exists():
            return candidate.as_posix(), True
    # write the conventional path anyway; the runner re-checks existence at run time
    return (AUDIO_DIR / AUDIO_PATTERNS[0].format(pid=passage_id)).as_posix(), False


def main() -> None:
    parser = argparse.ArgumentParser(description="Freeze the pilot manifest from verification sheets.")
    parser.add_argument("--out", type=Path, default=Path("data/manifests/pilot.jsonl"))
    parser.add_argument("--sheets", type=Path, nargs=2, default=SHEETS)
    args = parser.parse_args()

    rows_by_checker: dict[str, dict[str, dict]] = {}
    for sheet in args.sheets:
        with sheet.open("r", newline="", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
        checker = rows[0]["checker"] if rows else sheet.stem.split("_")[-1]
        rows_by_checker[checker] = {r["id"]: r for r in rows}
        empty = [r["id"] for r in rows if not r["verdict"].strip()]
        if empty:
            raise SystemExit(f"{sheet}: {len(empty)} rows still have an empty verdict, e.g. {empty[:5]}")

    checkers = sorted(rows_by_checker)
    # --- calibration agreement ---
    calib_ids = [rid for rid, r in rows_by_checker[checkers[0]].items()
                 if r["calibration"] == "yes" and rid in rows_by_checker[checkers[1]]]
    agree = sum(
        rows_by_checker[checkers[0]][rid]["verdict"].strip().lower()
        == rows_by_checker[checkers[1]][rid]["verdict"].strip().lower()
        for rid in calib_ids
    )
    disagreements = [rid for rid in calib_ids
                     if rows_by_checker[checkers[0]][rid]["verdict"].strip().lower()
                     != rows_by_checker[checkers[1]][rid]["verdict"].strip().lower()]
    if calib_ids:
        pct = 100 * agree / len(calib_ids)
        print(f"Calibration agreement: {agree}/{len(calib_ids)} = {pct:.0f}%"
              + (" — BELOW 80%: discuss the guideline before trusting the rest!" if pct < 80 else ""))
        if disagreements:
            print(f"Disagreements (auto-dropped, adjudicate + rerun if needed): {disagreements}")

    # --- resolve verdicts ---
    resolved: dict[str, dict] = {}
    for checker, rows in rows_by_checker.items():
        for rid, r in rows.items():
            if rid in disagreements:
                continue
            verdict = r["verdict"].strip().lower()
            if rid in resolved:
                continue  # calibration duplicate, same verdict
            if verdict == "drop":
                continue
            if verdict == "fix" and not r["fixed_question"].strip():
                raise SystemExit(f"{rid}: verdict=fix but fixed_question is empty")
            resolved[rid] = r

    # --- fill final quotas ---
    rng = random.Random(42)
    kept_ids = list(resolved)
    rng.shuffle(kept_ids)
    taken: list[dict] = []
    counts: Counter = Counter()
    for rid in kept_ids:
        r = resolved[rid]
        key = (r["category"], r["subtype"])
        if counts[key] < FINAL_QUOTAS.get(key, 0):
            counts[key] += 1
            taken.append(r)
    for key, quota in FINAL_QUOTAS.items():
        if counts[key] < quota:
            print(f"[!] {key}: only {counts[key]}/{quota} verified items survived — freezing with fewer")

    with PASSAGES_CSV.open("r", newline="", encoding="utf-8-sig") as f:
        transcripts = {r["id"]: r["transcript"] for r in csv.DictReader(f)}

    manifest: list[dict] = []
    missing_audio = 0

    for r in taken:
        path, found = audio_path_for(r["passage_id"])
        missing_audio += not found
        question = r["fixed_question"].strip() if r["verdict"].strip().lower() == "fix" else r["question"]
        manifest.append({
            "id": r["id"], "audio_path": path,
            "transcript": transcripts.get(r["passage_id"], ""),
            "question": question, "category": r["category"], "subtype": r["subtype"],
            "gold_answer": r["gold_answer"] or "UNANSWERABLE",
            "source": "spoken-squad", "generator": "manual-chat/v2",
            "verified_by": r["checker"],
        })

    with QUESTIONS_A_CSV.open("r", newline="", encoding="utf-8-sig") as f:
        a_rows = list(csv.DictReader(f))
    rng.shuffle(a_rows)
    for q in a_rows[:N_A]:
        path, found = audio_path_for(q["passage_id"])
        missing_audio += not found
        manifest.append({
            "id": q["question_id"], "audio_path": path,
            "transcript": transcripts.get(q["passage_id"], ""),
            "question": q["question"], "category": "A", "subtype": "stated",
            "gold_answer": q["answer"],
            "source": "spoken-squad", "generator": "native", "verified_by": "M2",
        })

    rng.shuffle(manifest)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        for row in manifest:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"\nFroze {len(manifest)} items -> {args.out}")
    for key, n in sorted(Counter((m['category'], m['subtype']) for m in manifest).items()):
        print(f"  {key}: {n}")
    if missing_audio:
        print(f"[!] {missing_audio} audio files not found locally (paths written by convention; "
              f"run data/setup_dataset.py or adapt AUDIO_PATTERNS before the real run)")
    print("Next: PR tagged 'pilot-freeze'; log the freeze + agreement % in docs/decisions.md; "
          "after freeze the file is append-only (fixes -> pilot_v2.jsonl).")


if __name__ == "__main__":
    main()
