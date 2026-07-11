"""Build a small manifest (data/manifests/mini.jsonl) from M2's committed files.

Joins data/generation/questions_a.csv (category-A questions) with
data/generation/passages.csv (transcripts) and locally exported audio.
Audio must exist locally first: python data/setup_dataset.py --all [--limit-rows 100]

Usage: python scripts/make_mini_manifest.py [--n 5]
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

AUDIO_DIR = Path("data/audio/spoken_squad_test")
# Filename candidates tried per passage id; extend after checking real names:
#   ls data/audio/spoken_squad_test | head
AUDIO_PATTERNS = ["{pid}.wav", "{pid}.WAV"]

PASSAGES_CSV = Path("data/generation/passages.csv")
QUESTIONS_CSV = Path("data/generation/questions_a.csv")
OUT_PATH = Path("data/manifests/mini.jsonl")


def find_audio(passage_id: str) -> Path | None:
    for pattern in AUDIO_PATTERNS:
        candidate = AUDIO_DIR / pattern.format(pid=passage_id)
        if candidate.exists():
            return candidate
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a mini manifest for harness smoke tests.")
    parser.add_argument("--n", type=int, default=5, help="Number of items (default 5).")
    parser.add_argument("--out", type=Path, default=OUT_PATH)
    args = parser.parse_args()

    with PASSAGES_CSV.open("r", newline="", encoding="utf-8-sig") as f:
        passages = {row["id"]: row for row in csv.DictReader(f)}

    rows, skipped_no_audio = [], 0
    with QUESTIONS_CSV.open("r", newline="", encoding="utf-8-sig") as f:
        for q in csv.DictReader(f):
            passage = passages.get(q["passage_id"])
            if not passage:
                continue
            audio = find_audio(q["passage_id"])
            if audio is None:
                skipped_no_audio += 1
                continue
            rows.append(
                {
                    "id": q["question_id"],
                    "audio_path": audio.as_posix(),
                    "transcript": passage["transcript"],
                    "question": q["question"],
                    "category": "A",
                    "subtype": "stated",
                    "gold_answer": q["answer"],
                    "source": "spoken-squad",
                    "generator": "native",
                    "verified_by": "M2",
                }
            )
            if len(rows) == args.n:
                break

    if not rows:
        hint = sorted(p.name for p in AUDIO_DIR.glob("*"))[:5] if AUDIO_DIR.exists() else []
        raise SystemExit(
            f"No items built ({skipped_no_audio} skipped for missing audio). "
            f"Audio dir {AUDIO_DIR} sample: {hint or 'MISSING — run data/setup_dataset.py first'}. "
            "Adapt AUDIO_PATTERNS at the top of this script to the real filenames."
        )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as out_file:
        for row in rows:
            out_file.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Wrote {len(rows)} items to {args.out} (skipped without audio: {skipped_no_audio})")


if __name__ == "__main__":
    main()
