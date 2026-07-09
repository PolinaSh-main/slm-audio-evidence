from __future__ import annotations

import argparse
import csv
import difflib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


PASSAGES_PATH = Path("data/generation/passages.csv")
RESPONSES_DIR = Path("data/generation/responses")

YES_NO_START_RE = re.compile(
    r"^(?:is|are|was|were|am|do|does|did|can|could|would|will|has|have|had|should|may|might|must)\b",
    re.IGNORECASE,
)
WORD_RE = re.compile(r"[A-Za-z0-9']+")
NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")
STOPWORDS = {
    "a",
    "about",
    "after",
    "all",
    "an",
    "and",
    "any",
    "are",
    "as",
    "at",
    "be",
    "before",
    "between",
    "by",
    "can",
    "could",
    "did",
    "do",
    "does",
    "during",
    "for",
    "from",
    "had",
    "has",
    "have",
    "how",
    "in",
    "into",
    "is",
    "it",
    "its",
    "many",
    "much",
    "of",
    "on",
    "or",
    "than",
    "that",
    "the",
    "their",
    "them",
    "there",
    "these",
    "this",
    "to",
    "was",
    "were",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",
    "would",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Filter generated B/C question candidates.")
    parser.add_argument("--passages", type=Path, default=PASSAGES_PATH)
    parser.add_argument(
        "--input-jsonl",
        type=Path,
        default=None,
        help="Filter one merged JSONL file. If omitted, all *.jsonl files in --responses-dir are used.",
    )
    parser.add_argument("--responses-dir", type=Path, default=RESPONSES_DIR)
    parser.add_argument(
        "--mode",
        choices=["auto", "b", "c"],
        default="auto",
        help="Expected candidate category. Default: infer from input filename.",
    )
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--log", type=Path, default=None)
    parser.add_argument("--min-words", type=int, default=5)
    parser.add_argument("--max-words", type=int, default=25)
    parser.add_argument("--fuzzy-threshold", type=float, default=0.88)
    return parser.parse_args()


def infer_label(args: argparse.Namespace) -> str:
    if args.input_jsonl:
        return args.input_jsonl.stem
    return "all"


def infer_mode(args: argparse.Namespace, label: str) -> str | None:
    if args.mode != "auto":
        return args.mode.upper()
    if label.startswith("b"):
        return "B"
    if label.startswith("c"):
        return "C"
    return None


def default_out_path(label: str) -> Path:
    return Path(f"data/generation/candidates_{label}.jsonl")


def default_log_path(label: str) -> Path:
    return Path(f"data/generation/filter_log_{label}.csv")


def normalize(value: str) -> str:
    return NON_ALNUM_RE.sub(" ", value.casefold()).strip()


def word_list(value: str) -> list[str]:
    return WORD_RE.findall(value)


def content_words(value: str) -> list[str]:
    words = [normalize(word) for word in word_list(value)]
    return [word for word in words if len(word) >= 4 and word not in STOPWORDS]


def load_passages(path: Path) -> dict[str, str]:
    with path.open("r", newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        return {row["id"]: row["transcript"] for row in reader}


def iter_jsonl_file(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            rows.append(
                {
                    "_source_file": path.name,
                    "_line": line_number,
                    "_parse_error": str(exc),
                    "_raw": line,
                }
            )
            continue
        row["_source_file"] = path.name
        row["_line"] = line_number
        rows.append(row)
    return rows


def iter_response_rows(responses_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(responses_dir.glob("*.jsonl")):
        rows.extend(iter_jsonl_file(path))
    return rows


def transcript_contains_fuzzy_word(word: str, transcript_words: set[str], threshold: float) -> bool:
    if word in transcript_words:
        return True
    if len(word) < 5:
        return False
    matches = difflib.get_close_matches(word, transcript_words, n=1, cutoff=threshold)
    return bool(matches)


def c_question_overlap(row: dict[str, Any], transcript: str, threshold: float) -> tuple[list[str], list[str]]:
    subtype = str(row.get("subtype", ""))
    if subtype == "false-presupposition":
        # C3 must overlap with the transcript enough to create a contradiction.
        return [], []

    transcript_words = set(content_words(transcript))
    ignored_words: set[str] = set()
    if subtype == "missing-attribute":
        ignored_words.update(content_words(str(row.get("entity", ""))))

    overlaps = []
    novel = []
    for word in content_words(str(row.get("question", ""))):
        if word in ignored_words:
            continue
        if transcript_contains_fuzzy_word(word, transcript_words, threshold):
            overlaps.append(word)
        else:
            novel.append(word)
    return sorted(set(overlaps)), sorted(set(novel))


def b_answer_is_direct(row: dict[str, Any], transcript: str) -> bool:
    answer = normalize(str(row.get("gold_answer", "")))
    if not answer or answer == "unanswerable":
        return False
    return answer in normalize(transcript)


def reject_reasons(
    row: dict[str, Any],
    passages: dict[str, str],
    seen_questions: dict[str, set[str]],
    min_words: int,
    max_words: int,
    fuzzy_threshold: float,
    expected_category: str | None,
) -> list[str]:
    if row.get("_parse_error"):
        return [f"json_parse_error:{row['_parse_error']}"]

    reasons: list[str] = []
    passage_id = str(row.get("passage_id", ""))
    question = str(row.get("question", "")).strip()
    category = str(row.get("category", "")).strip()
    transcript = passages.get(passage_id, "")

    if not passage_id or passage_id not in passages:
        reasons.append("unknown_passage_id")
    if not question:
        reasons.append("missing_question")
    if category not in {"B", "C"}:
        reasons.append("bad_category")
    if expected_category and category and category != expected_category:
        reasons.append(f"wrong_mode_expected_{expected_category}")

    word_count = len(word_list(question))
    if word_count < min_words:
        reasons.append(f"too_short:{word_count}")
    if word_count > max_words:
        reasons.append(f"too_long:{word_count}")

    if YES_NO_START_RE.match(question):
        reasons.append("yes_no_question")

    question_key = normalize(question)
    if question_key in seen_questions[passage_id]:
        reasons.append("duplicate_within_passage")
    seen_questions[passage_id].add(question_key)

    if category == "B" and transcript and b_answer_is_direct(row, transcript):
        reasons.append("b_answer_directly_in_transcript")

    if category == "C" and transcript:
        overlaps, novel = c_question_overlap(row, transcript, fuzzy_threshold)
        # For C, topic words may overlap with the transcript. Reject only when the
        # question has no new content words left after removing transcript overlap
        # (and, for C2, after ignoring the mentioned entity).
        if overlaps and not novel:
            reasons.append("c_keyword_overlap_no_new_focus:" + "|".join(overlaps[:8]))

    return reasons


def clean_row(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if not key.startswith("_")}


def add_candidate_ids(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counters: dict[tuple[str, str], int] = defaultdict(int)
    output = []
    for row in rows:
        clean = dict(row)
        if not clean.get("id"):
            passage_id = str(clean.get("passage_id", ""))
            category = str(clean.get("category", ""))
            counters[(passage_id, category)] += 1
            clean["id"] = f"{passage_id}-{category}{counters[(passage_id, category)]}"
        output.append(clean)
    return output


def main() -> None:
    args = parse_args()
    label = infer_label(args)
    expected_category = infer_mode(args, label)
    out_path = args.out or default_out_path(label)
    log_path = args.log or default_log_path(label)

    passages = load_passages(args.passages)
    rows = iter_jsonl_file(args.input_jsonl) if args.input_jsonl else iter_response_rows(args.responses_dir)
    seen_questions: dict[str, set[str]] = defaultdict(set)
    kept: list[dict[str, Any]] = []
    log_rows: list[dict[str, Any]] = []

    for row in rows:
        reasons = reject_reasons(
            row,
            passages,
            seen_questions,
            args.min_words,
            args.max_words,
            args.fuzzy_threshold,
            expected_category,
        )
        status = "rejected" if reasons else "kept"
        if not reasons:
            kept.append(clean_row(row))
        log_rows.append(
            {
                "status": status,
                "reasons": ";".join(reasons),
                "source_file": row.get("_source_file", ""),
                "line": row.get("_line", ""),
                "passage_id": row.get("passage_id", ""),
                "category": row.get("category", ""),
                "subtype": row.get("subtype", ""),
                "question": row.get("question", row.get("_raw", "")),
            }
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    kept_with_ids = add_candidate_ids(kept)
    with out_path.open("w", encoding="utf-8") as out_file:
        for row in kept_with_ids:
            out_file.write(json.dumps(row, ensure_ascii=False) + "\n")

    with log_path.open("w", newline="", encoding="utf-8") as log_file:
        writer = csv.DictWriter(
            log_file,
            fieldnames=["status", "reasons", "source_file", "line", "passage_id", "category", "subtype", "question"],
        )
        writer.writeheader()
        writer.writerows(log_rows)

    print(f"Input rows: {len(rows)}")
    print(f"Kept rows: {len(kept)}")
    print(f"Rejected rows: {len(rows) - len(kept)}")
    print(f"Wrote {out_path}")
    print(f"Wrote {log_path}")


if __name__ == "__main__":
    main()
