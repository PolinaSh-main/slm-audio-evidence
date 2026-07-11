"""Collect the audio files referenced by a manifest (or by passages.csv) into one zip.

Run on the machine that has data/audio/ exported (M2's). The zip unpacks into the
repo root in Colab so that manifest audio_path values resolve as-is.

Usage:
  py -3 scripts/collect_pilot_audio.py                                          # from data/manifests/pilot.jsonl
  py -3 scripts/collect_pilot_audio.py --passages data/generation/passages.csv  # BEFORE the freeze: all 40 passages
"""

from __future__ import annotations

import argparse
import csv
import json
import zipfile
from pathlib import Path

AUDIO_DIR = "data/audio/spoken_squad_test"


def main() -> None:
    parser = argparse.ArgumentParser(description="Zip the audio files a manifest needs.")
    parser.add_argument("--manifest", type=Path, default=Path("data/manifests/pilot.jsonl"))
    parser.add_argument("--passages", type=Path, default=None,
                        help="Zip audio for every passage id in this CSV instead of a manifest (works before the freeze).")
    parser.add_argument("--out", type=Path, default=Path("pilot_audio.zip"))
    args = parser.parse_args()

    paths: set[str] = set()
    if args.passages:
        with args.passages.open("r", newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                paths.add(f"{AUDIO_DIR}/{row['id']}.wav")
    else:
        for line in args.manifest.read_text(encoding="utf-8").splitlines():
            if line.strip():
                paths.add(json.loads(line)["audio_path"])

    missing: list[str] = []
    with zipfile.ZipFile(args.out, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(paths):
            path = Path(p)
            if path.exists():
                zf.write(path, arcname=p)  # keep repo-relative layout
            else:
                missing.append(p)

    print(f"Zipped {len(paths) - len(missing)}/{len(paths)} files -> {args.out}")
    if missing:
        print(f"[!] {len(missing)} missing locally, e.g. {missing[:3]}")
    print("In Colab: unzip into the repo root, e.g.  !unzip -q pilot_audio.zip -d .")


if __name__ == "__main__":
    main()
