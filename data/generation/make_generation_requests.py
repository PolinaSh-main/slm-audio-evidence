from __future__ import annotations

import argparse
import csv
from pathlib import Path


PASSAGES_PATH = Path("data/generation/passages.csv")
PROMPTS_DIR = Path("data/generation/prompts")
OUT_DIR = Path("data/generation/requests")

CATEGORY_CONFIG = {
    "b": {
        "prompt": "b-v2.txt",
        "category": "B",
        "subtype": "inference",
        "per_passage": 3,
        "schema": (
            '{"passage_id":"...","category":"B","subtype":"inference",'
            '"inference_type":"...","question":"...","gold_answer":"...",'
            '"evidence":"...","why_not_A":"...","generator":"manual-chat/b-v2"}'
        ),
    },
    "c1": {
        "prompt": "c1-v2.txt",
        "category": "C",
        "subtype": "absent-entity",
        "per_passage": 3,
        "schema": (
            '{"passage_id":"...","category":"C","subtype":"absent-entity",'
            '"question":"...","missing_focus":"...","gold_answer":"UNANSWERABLE",'
            '"why_unanswerable":"...","generator":"manual-chat/c1-v2"}'
        ),
    },
    "c2": {
        "prompt": "c2-v2.txt",
        "category": "C",
        "subtype": "missing-attribute",
        "per_passage": 3,
        "schema": (
            '{"passage_id":"...","category":"C","subtype":"missing-attribute",'
            '"question":"...","entity":"...","missing_attribute":"...",'
            '"gold_answer":"UNANSWERABLE","why_unanswerable":"...",'
            '"generator":"manual-chat/c2-v2"}'
        ),
    },
    "c3": {
        "prompt": "c3-v2.txt",
        "category": "C",
        "subtype": "false-presupposition",
        "per_passage": 1,
        "schema": (
            '{"passage_id":"...","category":"C","subtype":"false-presupposition",'
            '"question":"...","false_premise":"...","contradicting_evidence":"...",'
            '"gold_answer":"UNANSWERABLE","generator":"manual-chat/c3-v2"}'
        ),
    },
    "c4": {
        "prompt": "c4-v2.txt",
        "category": "C",
        "subtype": "off-topic",
        "per_passage": 1,
        "schema": (
            '{"passage_id":"...","category":"C","subtype":"off-topic",'
            '"question":"...","off_topic_domain":"...",'
            '"gold_answer":"UNANSWERABLE","why_unanswerable":"...",'
            '"generator":"manual-chat/c4-v2"}'
        ),
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create copy-paste request batches for manual LLM question generation."
    )
    parser.add_argument("--passages", type=Path, default=PASSAGES_PATH)
    parser.add_argument("--prompts-dir", type=Path, default=PROMPTS_DIR)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    parser.add_argument(
        "--categories",
        nargs="+",
        default=["b", "c1", "c2"],
        choices=sorted(CATEGORY_CONFIG),
        help="Prompt categories to prepare. Default: b c1 c2.",
    )
    parser.add_argument("--batch-size", type=int, default=5, help="Passages per request file.")
    return parser.parse_args()


def read_passages(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as csv_file:
        rows = list(csv.DictReader(csv_file))
    if not rows:
        raise ValueError(f"No passages found in {path}")
    for field in ["id", "transcript"]:
        if field not in rows[0]:
            raise ValueError(f"Missing required column {field!r} in {path}")
    return rows


def chunks(rows: list[dict[str, str]], size: int) -> list[list[dict[str, str]]]:
    if size < 1:
        raise ValueError("--batch-size must be >= 1")
    return [rows[index : index + size] for index in range(0, len(rows), size)]


def render_request(category_key: str, prompt_text: str, batch: list[dict[str, str]]) -> str:
    config = CATEGORY_CONFIG[category_key]
    prompt_name = config["prompt"]
    per_passage = config["per_passage"]
    total_items = per_passage * len(batch)

    parts = [
        "# Manual LLM generation request",
        "",
        f"Prompt version: `{prompt_name}`",
        f"Target items: {per_passage} per passage, {total_items} total",
        "",
        "Use the prompt template below for EACH passage. Return JSONL only: one JSON object per line, no markdown.",
        "Do not reuse the same question wording within a passage.",
        "Every JSON object must include the exact `passage_id` from the passage block.",
        "Replace `{passage_id}` with the passage id shown in each passage block.",
        "Replace `{transcript}` with that passage transcript.",
        "",
        "Expected JSONL schema:",
        "",
        "```json",
        config["schema"],
        "```",
        "",
        "Prompt template:",
        "",
        "```text",
        prompt_text.strip(),
        "```",
        "",
        "Passages:",
        "",
    ]

    for row in batch:
        parts.extend(
            [
                f"## passage_id: {row['id']}",
                "",
                "```text",
                row["transcript"].strip(),
                "```",
                "",
            ]
        )

    return "\n".join(parts).rstrip() + "\n"


def main() -> None:
    args = parse_args()
    passages = read_passages(args.passages)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    for category_key in args.categories:
        config = CATEGORY_CONFIG[category_key]
        prompt_path = args.prompts_dir / config["prompt"]
        prompt_text = prompt_path.read_text(encoding="utf-8")

        for batch_number, batch in enumerate(chunks(passages, args.batch_size), start=1):
            out_path = args.out_dir / f"{category_key}_batch_{batch_number:02d}.md"
            out_path.write_text(render_request(category_key, prompt_text, batch), encoding="utf-8")
            print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
