from __future__ import annotations

import argparse
import json
from pathlib import Path


RESPONSES_DIR = Path("data/generation/responses")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge manual LLM batch JSONL responses.")
    parser.add_argument("--responses-dir", type=Path, default=RESPONSES_DIR)
    parser.add_argument(
        "--patterns",
        nargs="+",
        required=True,
        help="Glob patterns relative to responses-dir, for example b_batch_*.jsonl c*_batch_*.jsonl.",
    )
    parser.add_argument("--out", type=Path, required=True, help="Merged JSONL output path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    paths: list[Path] = []
    for pattern in args.patterns:
        paths.extend(sorted(args.responses_dir.glob(pattern)))
    paths = sorted(set(paths))
    if not paths:
        raise FileNotFoundError(f"No response files matched patterns: {args.patterns}")

    rows = []
    for path in paths:
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON in {path}:{line_number}: {exc}") from exc

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as out_file:
        for row in rows:
            out_file.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Merged {len(paths)} files")
    print(f"Wrote {len(rows)} rows to {args.out}")


if __name__ == "__main__":
    main()
