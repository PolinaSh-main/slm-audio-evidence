"""Generate a 16 kHz mono WAV fallback audio file with edge-tts.

Examples:
    python data\generation\tts_fallback.py --text "Your passage text here" --out data\generation\fallback.wav
    python data/generation/tts_fallback.py --text-file passage.txt --out data\generation\fallback.wav
"""

from __future__ import annotations

import argparse
import asyncio
import wave
from pathlib import Path


DEFAULT_VOICE = "en-US-JennyNeural"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate WAV fallback audio from text using free edge-tts."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--text", help="Text to synthesize.")
    source.add_argument("--text-file", type=Path, help="UTF-8 text file to synthesize.")
    parser.add_argument("--out", type=Path, required=True, help="Output .wav path.")
    parser.add_argument("--voice", default=DEFAULT_VOICE, help=f"edge-tts voice, default: {DEFAULT_VOICE}.")
    parser.add_argument("--rate", default="+0%", help="Speech rate, for example -10%% or +15%%.")
    parser.add_argument("--volume", default="+0%", help="Speech volume, for example -10%% or +0%%.")
    parser.add_argument("--pitch", default="+0Hz", help="Speech pitch, for example -5Hz or +0Hz.")
    return parser.parse_args()


def read_text(args: argparse.Namespace) -> str:
    if args.text_file:
        text = args.text_file.read_text(encoding="utf-8").strip()
    else:
        text = args.text.strip()
    if not text:
        raise ValueError("Input text is empty.")
    return text


async def synthesize_edge_mp3(text: str, args: argparse.Namespace) -> bytes:
    try:
        import edge_tts
    except ImportError as exc:
        raise RuntimeError("edge-tts is not installed. Run: python -m pip install -r requirements.txt") from exc

    kwargs = {
        "voice": args.voice,
        "rate": args.rate,
        "volume": args.volume,
        "pitch": args.pitch,
    }
    communicate = edge_tts.Communicate(text, **kwargs)
    chunks: list[bytes] = []
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            chunks.append(chunk["data"])
    if not chunks:
        raise RuntimeError("edge-tts did not return audio data.")
    return b"".join(chunks)


def is_wav_16khz_mono(path: Path) -> bool:
    try:
        with wave.open(str(path), "rb") as wav:
            return (
                wav.getframerate() == 16000
                and wav.getnchannels() == 1
                and wav.getsampwidth() == 2
            )
    except wave.Error:
        return False


def convert_mp3_to_wav(mp3_data: bytes, out_path: Path) -> None:
    try:
        import miniaudio
    except ImportError as exc:
        raise RuntimeError("miniaudio is not installed. Run: python -m pip install -r requirements.txt") from exc

    decoded = miniaudio.decode(
        mp3_data,
        output_format=miniaudio.SampleFormat.SIGNED16,
        nchannels=1,
        sample_rate=16000,
    )

    with wave.open(str(out_path), "wb") as wav:
        wav.setnchannels(decoded.nchannels)
        wav.setsampwidth(2)
        wav.setframerate(decoded.sample_rate)
        wav.writeframes(decoded.samples)


async def main() -> None:
    args = parse_args()
    text = read_text(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)

    mp3_data = await synthesize_edge_mp3(text, args)
    convert_mp3_to_wav(mp3_data, args.out)

    if not is_wav_16khz_mono(args.out):
        raise RuntimeError(f"Output is not a valid 16 kHz mono 16-bit WAV: {args.out}")

    print(f"Wrote {args.out}")


if __name__ == "__main__":
    asyncio.run(main())
