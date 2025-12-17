"""Decode ``string.bin`` and emit its textual payload."""
from __future__ import annotations

from pathlib import Path

INPUT_FILE = Path("string.bin")
OUTPUT_DIR = Path("output")
OUTPUT_FILE = OUTPUT_DIR / "string.txt"


def xor_decode(data: bytes) -> bytes:
    """Return ``data`` with every byte XOR-ed by ``0xFF``."""

    return bytes(b ^ 0xFF for b in data)


def strip_header(decoded: bytes) -> bytes:
    """Drop the leading 8-byte header when it matches the known pattern."""

    if len(decoded) >= 9 and decoded[:4] == b"\xfe\xff\xff\xff":
        return decoded[8:]
    return decoded


def strip_padding(decoded: bytes) -> bytes:
    """Remove any trailing ``0xFF`` bytes used as padding."""

    idx = len(decoded)
    while idx > 0 and decoded[idx - 1] == 0xFF:
        idx -= 1
    return decoded[:idx]


def main() -> None:
    if not INPUT_FILE.exists():
        raise SystemExit(f"Input file not found: {INPUT_FILE}")

    decoded = xor_decode(INPUT_FILE.read_bytes())
    cleaned = strip_padding(strip_header(decoded))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_bytes(cleaned)
    print(f"Decoded {INPUT_FILE} -> {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
