"""Decode ``map_battle.bin`` into a readable text asset."""
from __future__ import annotations

from pathlib import Path

INPUT_FILE = Path("map_battle.bin")
OUTPUT_DIR = Path("output")
OUTPUT_FILE = OUTPUT_DIR / "map_battle.txt"


def xor_decode(data: bytes) -> bytes:
    """Return bytes XOR-ed with ``0xFF``."""

    return bytes(b ^ 0xFF for b in data)


def strip_header(decoded: bytes) -> bytes:
    """Drop the leading 8-byte header if present.

    The decoded payload begins with two 32-bit integers followed by a ``;`` that
    starts the textual records. Stripping the binary header yields clean,
    newline-delimited content for inspection.
    """

    if len(decoded) >= 9 and decoded[:4] == b"\xfe\xff\xff\xff" and decoded[8:9] == b";":
        return decoded[8:]
    return decoded


def main() -> None:
    if not INPUT_FILE.exists():
        raise SystemExit(f"Input file not found: {INPUT_FILE}")

    decoded = xor_decode(INPUT_FILE.read_bytes())
    cleaned = strip_header(decoded)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_bytes(cleaned)
    print(f"Decoded {INPUT_FILE} -> {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
