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


def main() -> None:
    if not INPUT_FILE.exists():
        raise SystemExit(f"Input file not found: {INPUT_FILE}")

    decoded = xor_decode(INPUT_FILE.read_bytes())

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_bytes(decoded)
    print(f"Decoded {INPUT_FILE} -> {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
