from __future__ import annotations

import argparse
import csv
import json
import wave
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


REPO_ID = "AudioLLMs/spoken_squad_test"
REVISION = "b55aab98726d0eab95eeef1ee9992a0532b3226e"

RAW_DIR = Path("data/raw/spoken_squad_test")
RAW_DATA_DIR = RAW_DIR / "data"
AUDIO_DIR = Path("data/audio/spoken_squad_test")
GENERATION_DIR = Path("data/generation")
INDEX_PATH = GENERATION_DIR / "spoken_squad_audio_index.csv"
MATCHED_INDEX_PATH = GENERATION_DIR / "spoken_squad_audio_index_with_transcripts.csv"
DRAFT_DATA_PATH = GENERATION_DIR / "data.csv"

MIN_SECONDS = 20.0
MAX_SECONDS = 60.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare a Spoken-SQuAD subset: download audio, export WAV files, "
            "attach clean SQuAD transcripts, and create data/generation/data.csv."
        )
    )
    parser.add_argument("--all", action="store_true", help="Run download, export, match, and build.")
    parser.add_argument("--download", action="store_true", help="Download AudioLLMs/spoken_squad_test parquet shards.")
    parser.add_argument("--export-audio", action="store_true", help="Export WAV files and write the audio index.")
    parser.add_argument("--match-transcripts", action="store_true", help="Join audio rows with original SQuAD contexts.")
    parser.add_argument(
        "--build-passages",
        action="store_true",
        help="Build draft data.csv with all matched rows that pass the duration filter.",
    )
    parser.add_argument("--limit-rows", type=int, default=None, help="Optional max rows to export for a quick test.")
    parser.add_argument("--min-seconds", type=float, default=MIN_SECONDS)
    parser.add_argument("--max-seconds", type=float, default=MAX_SECONDS)
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--audio-dir", type=Path, default=AUDIO_DIR)
    parser.add_argument("--generation-dir", type=Path, default=GENERATION_DIR)
    return parser.parse_args()


def wav_duration_seconds(path: Path) -> float:
    with wave.open(str(path), "rb") as wav_file:
        return wav_file.getnframes() / float(wav_file.getframerate())


def download_dataset(raw_dir: Path) -> None:
    from huggingface_hub import HfApi, snapshot_download

    raw_dir.mkdir(parents=True, exist_ok=True)

    api = HfApi()
    parquet_files = [
        item.path
        for item in api.list_repo_tree(
            REPO_ID,
            repo_type="dataset",
            revision=REVISION,
            recursive=True,
        )
        if item.path.startswith("data/test-") and item.path.endswith(".parquet")
    ]
    parquet_files.sort()

    local_path = snapshot_download(
        repo_id=REPO_ID,
        repo_type="dataset",
        revision=REVISION,
        allow_patterns=["README.md", "data/test-*.parquet"],
        local_dir=raw_dir,
    )

    metadata = {
        "repo_id": REPO_ID,
        "revision": REVISION,
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "local_path": str(Path(local_path).resolve()),
        "parquet_files": parquet_files,
        "split": "test",
    }
    metadata_path = raw_dir / "download_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Downloaded {len(parquet_files)} parquet shards to {raw_dir}")


def export_audio(raw_data_dir: Path, audio_dir: Path, index_path: Path, limit_rows: int | None) -> None:
    import pyarrow.parquet as pq

    parquet_files = sorted(raw_data_dir.glob("test-*.parquet"))
    if not parquet_files:
        raise FileNotFoundError(f"No test-*.parquet files found in {raw_data_dir}")

    audio_dir.mkdir(parents=True, exist_ok=True)
    index_path.parent.mkdir(parents=True, exist_ok=True)

    exported = 0
    with index_path.open("w", newline="", encoding="utf-8") as index_file:
        writer = csv.DictWriter(
            index_file,
            fieldnames=[
                "id",
                "audio_path",
                "duration_seconds",
                "instruction",
                "answer",
                "source_shard",
                "row_in_shard",
            ],
        )
        writer.writeheader()

        for shard_number, parquet_path in enumerate(parquet_files, start=1):
            table = pq.read_table(parquet_path, columns=["context", "instruction", "answer"])
            for row_idx, row in enumerate(table.to_pylist()):
                audio_bytes = row["context"]["bytes"]
                if not audio_bytes:
                    continue

                item_id = f"sq-{exported:04d}"
                audio_path = audio_dir / f"{item_id}.wav"
                audio_path.write_bytes(audio_bytes)
                duration = wav_duration_seconds(audio_path)

                writer.writerow(
                    {
                        "id": item_id,
                        "audio_path": audio_path.as_posix(),
                        "duration_seconds": f"{duration:.3f}",
                        "instruction": row["instruction"],
                        "answer": row["answer"],
                        "source_shard": parquet_path.name,
                        "row_in_shard": row_idx,
                    }
                )

                exported += 1
                if limit_rows is not None and exported >= limit_rows:
                    print(f"Exported {exported} WAV files to {audio_dir}")
                    return

            print(f"Processed shard {shard_number}/{len(parquet_files)}: {parquet_path.name}")

    print(f"Exported {exported} WAV files to {audio_dir}")


def normalize_text(value: str) -> str:
    return " ".join(value.casefold().strip().split())


def load_squad_validation_by_question() -> dict[str, list[dict]]:
    from datasets import load_dataset

    by_question: dict[str, list[dict]] = defaultdict(list)
    dataset = load_dataset("rajpurkar/squad", split="validation")
    transcript_source = "rajpurkar/squad/validation/original_context"

    for row in dataset:
        row = dict(row)
        row["_transcript_source"] = transcript_source
        by_question[row["question"]].append(row)
    return by_question


def choose_squad_match(audio_row: dict[str, str], candidates: list[dict]) -> tuple[dict | None, str]:
    if not candidates:
        return None, "no_question_match"

    answer = normalize_text(audio_row.get("answer", ""))
    if answer:
        exact_answer_matches = [
            row
            for row in candidates
            if any(normalize_text(text) == answer for text in row["answers"]["text"])
        ]
        if len(exact_answer_matches) == 1:
            return exact_answer_matches[0], "question_and_answer"
        if len(exact_answer_matches) > 1:
            return exact_answer_matches[0], "question_and_answer_first_duplicate"

    if len(candidates) == 1:
        return candidates[0], "question_only"
    return candidates[0], "question_first_duplicate"


def match_transcripts(index_path: Path, matched_index_path: Path) -> None:
    with index_path.open("r", newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        rows = list(reader)
        input_fields = reader.fieldnames or []

    squad_rows = load_squad_validation_by_question()
    output_fields = [
        *input_fields,
        "transcript",
        "transcript_source",
        "source_dataset_id",
        "source_title",
        "source_question",
        "source_answers",
        "match_method",
    ]

    matched = 0
    unmatched = 0
    with matched_index_path.open("w", newline="", encoding="utf-8") as out_file:
        writer = csv.DictWriter(out_file, fieldnames=output_fields)
        writer.writeheader()

        for row in rows:
            match, method = choose_squad_match(row, squad_rows.get(row["instruction"], []))
            output_row = dict(row)
            if match is None:
                unmatched += 1
                output_row.update(
                    {
                        "transcript": "",
                        "transcript_source": "",
                        "source_dataset_id": "",
                        "source_title": "",
                        "source_question": "",
                        "source_answers": "",
                        "match_method": method,
                    }
                )
            else:
                matched += 1
                output_row.update(
                    {
                        "transcript": match["context"],
                        "transcript_source": match.get(
                            "_transcript_source", "rajpurkar/squad/validation/original_context"
                        ),
                        "source_dataset_id": match["id"],
                        "source_title": match["title"],
                        "source_question": match["question"],
                        "source_answers": json.dumps(match["answers"], ensure_ascii=False),
                        "match_method": method,
                    }
                )
            writer.writerow(output_row)

    print(f"Matched transcripts: {matched}")
    print(f"Unmatched transcripts: {unmatched}")
    print(f"Wrote {matched_index_path}")


def build_passages(
    matched_index_path: Path,
    passages_path: Path,
    min_seconds: float,
    max_seconds: float,
) -> None:
    with matched_index_path.open("r", newline="", encoding="utf-8-sig") as csv_file:
        rows = list(csv.DictReader(csv_file))

    kept: list[dict[str, str]] = []
    for row in rows:
        if not row.get("transcript"):
            continue
        duration = float(row["duration_seconds"])
        if not min_seconds <= duration <= max_seconds:
            continue
        kept.append(row)

    passages_path.parent.mkdir(parents=True, exist_ok=True)
    with passages_path.open("w", newline="", encoding="utf-8") as out_file:
        writer = csv.DictWriter(
            out_file,
            fieldnames=[
                "id",
                "audio_path",
                "duration_seconds",
                "transcript",
                "question",
                "answer",
                "source_title",
                "source_dataset_id",
                "source_answers",
                "match_method",
            ],
        )
        writer.writeheader()
        for row in kept:
            writer.writerow(
                {
                    "id": row["id"],
                    "audio_path": row["audio_path"],
                    "duration_seconds": row["duration_seconds"],
                    "transcript": row["transcript"],
                    "question": row["instruction"],
                    "answer": row["answer"],
                    "source_title": row["source_title"],
                    "source_dataset_id": row["source_dataset_id"],
                    "source_answers": row["source_answers"],
                    "match_method": row["match_method"],
                }
            )

    print(f"Rows with matched transcripts and {min_seconds:g}-{max_seconds:g}s audio: {len(kept)}")
    print(f"Wrote draft pool to {passages_path}")
    print("Manual selection is expected: choose the final 40 rows and save them as data/generation/passages.csv.")


def main() -> None:
    args = parse_args()
    if not any([args.all, args.download, args.export_audio, args.match_transcripts, args.build_passages]):
        args.all = True

    raw_dir = args.raw_dir
    raw_data_dir = raw_dir / "data"
    audio_dir = args.audio_dir
    generation_dir = args.generation_dir
    index_path = generation_dir / INDEX_PATH.name
    matched_index_path = generation_dir / MATCHED_INDEX_PATH.name
    passages_path = generation_dir / DRAFT_DATA_PATH.name

    if args.all or args.download:
        download_dataset(raw_dir)
    if args.all or args.export_audio:
        export_audio(raw_data_dir, audio_dir, index_path, args.limit_rows)
    if args.all or args.match_transcripts:
        match_transcripts(index_path, matched_index_path)
    if args.all or args.build_passages:
        build_passages(
            matched_index_path,
            passages_path,
            args.min_seconds,
            args.max_seconds,
        )


if __name__ == "__main__":
    main()
