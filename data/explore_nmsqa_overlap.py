"""Measure how many SQuAD 2.0 dev A/C questions have natural NMSQA audio.

The unit of overlap is a normalized full paragraph. If an NMSQA test paragraph
matches a SQuAD 2.0 dev paragraph, every SQuAD question attached to that
paragraph can reuse the corresponding natural full-context recording.
"""

from __future__ import annotations

import argparse
import csv
import json
import time
import unicodedata
import urllib.request
from collections import defaultdict
from pathlib import Path


NMSQA_TEST_URL = (
    "https://huggingface.co/datasets/voidful/NMSQA/resolve/main/data/"
    "test-00000-of-00001-e59cc4b2d3e13fe2.parquet?download=true"
)
SQUAD2_DEV_URL = (
    "https://raw.githubusercontent.com/rajpurkar/SQuAD-explorer/"
    "master/dataset/dev-v2.0.json"
)

DEFAULT_RAW_DIR = Path("data/raw/nmsqa_overlap")
DEFAULT_REPORT = Path("data/nmsqa_overlap_report.json")
DEFAULT_DATA_CSV = Path("data/generation/data.csv")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Count SQuAD 2.0 dev A/C questions covered by NMSQA test audio."
    )
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--data-csv", type=Path, default=DEFAULT_DATA_CSV)
    parser.add_argument(
        "--force-download",
        action="store_true",
        help="Download source metadata again even when local files exist.",
    )
    return parser.parse_args()


def download(url: str, destination: Path, force: bool, attempts: int = 4) -> None:
    if destination.is_file() and not force:
        print(f"Using cached file: {destination}")
        return

    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": "slm-audio-evidence/1.0"})

    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                with partial.open("wb") as output:
                    while chunk := response.read(1024 * 1024):
                        output.write(chunk)
            partial.replace(destination)
            print(f"Downloaded: {destination} ({destination.stat().st_size:,} bytes)")
            return
        except Exception:
            if attempt == attempts:
                raise
            wait_seconds = 2**attempt
            print(f"Download attempt {attempt}/{attempts} failed; retrying in {wait_seconds}s")
            time.sleep(wait_seconds)


def normalize_context(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return " ".join(normalized.split())


def load_nmsqa_test(path: Path) -> tuple[int, dict[str, dict[str, set[str]]]]:
    import pyarrow.parquet as pq

    table = pq.read_table(
        path,
        columns=["context", "content_full_audio_path", "content_audio_speaker"],
    )
    contexts: dict[str, dict[str, set[str]]] = defaultdict(
        lambda: {"texts": set(), "audio_paths": set(), "speakers": set()}
    )
    for row in table.to_pylist():
        key = normalize_context(row["context"])
        contexts[key]["texts"].add(row["context"])
        if row.get("content_full_audio_path"):
            contexts[key]["audio_paths"].add(row["content_full_audio_path"])
        if row.get("content_audio_speaker"):
            contexts[key]["speakers"].add(row["content_audio_speaker"])
    return table.num_rows, dict(contexts)


def load_squad2_dev(path: Path) -> tuple[dict[str, list[dict]], dict[str, int]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    paragraphs: dict[str, list[dict]] = defaultdict(list)
    stats = {"paragraphs": 0, "questions": 0, "A": 0, "C": 0}

    for article in payload["data"]:
        for paragraph in article["paragraphs"]:
            stats["paragraphs"] += 1
            key = normalize_context(paragraph["context"])
            for qa in paragraph["qas"]:
                category = "C" if qa["is_impossible"] else "A"
                stats["questions"] += 1
                stats[category] += 1
                paragraphs[key].append(
                    {
                        "id": qa["id"],
                        "category": category,
                        "question": qa["question"],
                    }
                )
    return dict(paragraphs), stats


def load_data_csv(path: Path) -> tuple[int, set[str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as source:
        rows = list(csv.DictReader(source))
    contexts = {normalize_context(row["transcript"]) for row in rows}
    return len(rows), contexts


def count_questions(keys: set[str], squad_contexts: dict[str, list[dict]]) -> dict[str, int]:
    questions = [qa for key in keys for qa in squad_contexts[key]]
    return {
        "matched_contexts": len(keys),
        "A_questions": sum(qa["category"] == "A" for qa in questions),
        "C_questions": sum(qa["category"] == "C" for qa in questions),
    }


def measure_overlap(
    nmsqa_contexts: dict[str, dict[str, set[str]]],
    squad_contexts: dict[str, list[dict]],
    allowed_contexts: set[str] | None = None,
) -> dict:
    matched = set(nmsqa_contexts) & set(squad_contexts)
    if allowed_contexts is not None:
        matched &= allowed_contexts
    matched_keys = sorted(matched)
    matched_questions = [qa for key in matched_keys for qa in squad_contexts[key]]

    audio_paths = {
        path
        for key in matched_keys
        for path in nmsqa_contexts[key]["audio_paths"]
    }
    speakers = {
        speaker
        for key in matched_keys
        for speaker in nmsqa_contexts[key]["speakers"]
    }
    question_ids = {qa["id"] for qa in matched_questions}
    if len(question_ids) != len(matched_questions):
        raise ValueError("Duplicate SQuAD question IDs found in the overlap")

    return {
        "matched_contexts": len(matched_keys),
        "natural_audio_files": len(audio_paths),
        "speakers": len(speakers),
        "A_questions": sum(qa["category"] == "A" for qa in matched_questions),
        "C_questions": sum(qa["category"] == "C" for qa in matched_questions),
    }


def main() -> None:
    args = parse_args()
    nmsqa_path = args.raw_dir / "nmsqa_test.parquet"
    squad_path = args.raw_dir / "dev-v2.0.json"

    download(NMSQA_TEST_URL, nmsqa_path, args.force_download)
    download(SQUAD2_DEV_URL, squad_path, args.force_download)

    nmsqa_rows, nmsqa_contexts = load_nmsqa_test(nmsqa_path)
    squad_contexts, squad_stats = load_squad2_dev(squad_path)
    data_csv_rows, pool_contexts = load_data_csv(args.data_csv)

    pool_squad_keys = pool_contexts & set(squad_contexts)
    pool_squad_overlap = count_questions(pool_squad_keys, squad_contexts)
    natural_pool_overlap = measure_overlap(
        nmsqa_contexts,
        squad_contexts,
        allowed_contexts=pool_contexts,
    )

    report = {
        "pool": {
            "data_csv_contexts": len(pool_contexts),
            "matched_squad2_contexts": pool_squad_overlap["matched_contexts"],
            "A": pool_squad_overlap["A_questions"],
            "C": pool_squad_overlap["C_questions"],
        },
        "natural_nmsqa_slice": {
            "contexts": natural_pool_overlap["matched_contexts"],
            "audio_files": natural_pool_overlap["natural_audio_files"],
            "speakers": natural_pool_overlap["speakers"],
            "A": natural_pool_overlap["A_questions"],
            "C": natural_pool_overlap["C_questions"],
        },
    }

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print("\ndata.csv x SQuAD 2.0 dev")
    print(f"data.csv rows:          {data_csv_rows}")
    print(f"Pool unique contexts:   {len(pool_contexts)}")
    print(f"Matched contexts:       {pool_squad_overlap['matched_contexts']}")
    print(f"A questions covered:    {pool_squad_overlap['A_questions']}")
    print(f"C questions covered:    {pool_squad_overlap['C_questions']}")

    print("\ndata.csv x NMSQA test x SQuAD 2.0 dev")
    print(f"Matched contexts:       {natural_pool_overlap['matched_contexts']}")
    print(f"Natural audio files:    {natural_pool_overlap['natural_audio_files']}")
    print(f"Unique speakers:        {natural_pool_overlap['speakers']}")
    print(f"A questions covered:    {natural_pool_overlap['A_questions']}")
    print(f"C questions covered:    {natural_pool_overlap['C_questions']}")
    print(f"Report:                 {args.report}")


if __name__ == "__main__":
    main()
