"""Specialized unpacker for ``map_planet.bin``.

The file contents are XOR-obfuscated with ``0xFF``. This helper decodes the
payload and writes the readable text into ``output/map_planet.txt`` for
inspection or further tooling.
"""
from __future__ import annotations

from pathlib import Path

INPUT_FILE = Path("map_planet.bin")
OUTPUT_DIR = Path("output")
OUTPUT_FILE = OUTPUT_DIR / "map_planet.txt"


def xor_decode(data: bytes) -> bytes:
    """Return bytes XOR-ed with ``0xFF``."""

    return bytes(b ^ 0xFF for b in data)


def strip_header(decoded: bytes) -> bytes:
    """Drop the leading 8-byte binary header when present.

    ``map_planet`` follows the same layout as the other map bins: two 32-bit
    integers precede the tab-delimited text rows. Removing the header yields a
    clean text file instead of a binary-looking payload.
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
