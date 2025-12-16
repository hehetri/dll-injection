"""Decode ``dungeon/p_monai.bin`` into a readable text asset.

The file appears to use the standard XOR ``0xFF`` encoding used by other
resources. The decoded data begins with an 8-byte header and ends with ``0xFF``
padding, both of which are stripped to expose the plain text content.
"""
from __future__ import annotations

from pathlib import Path

INPUT_FILE = Path("dungeon/p_monai.bin")
OUTPUT_DIR = Path("output/dungeon")
OUTPUT_FILE = OUTPUT_DIR / "p_monai.txt"
HEADER_PREFIX = b"\xfe\xff\xff\xff"


def xor_decode(data: bytes) -> bytes:
    """Return the bytes in ``data`` XOR-ed with ``0xFF``."""

    return bytes(b ^ 0xFF for b in data)


def strip_header(decoded: bytes) -> bytes:
    """Remove the leading 8-byte header if present."""

    if len(decoded) >= 8 and decoded.startswith(HEADER_PREFIX):
        return decoded[8:]
    return decoded


def strip_padding(decoded: bytes) -> bytes:
    """Trim trailing ``0xFF`` padding bytes."""

    end = len(decoded)
    while end > 0 and decoded[end - 1] == 0xFF:
        end -= 1
    return decoded[:end]


def main() -> None:
    if not INPUT_FILE.exists():
        raise SystemExit(f"Input file not found: {INPUT_FILE}")

    cleaned = strip_padding(strip_header(xor_decode(INPUT_FILE.read_bytes())))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_bytes(cleaned)

    print(f"Decoded {INPUT_FILE} -> {OUTPUT_FILE} ({len(cleaned)} bytes)")


if __name__ == "__main__":
    main()
