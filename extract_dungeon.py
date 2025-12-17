"""Extract and decrypt the level entries embedded in ``dungeon/dungeon.bin``.

The archive stores a short header followed by fixed-size name records, an offset
 table, a zero-filled placeholder block, and the encrypted payloads. Each
 payload uses the same XOR 0xFF encoding as the other game assets and typically
 starts with an 8-byte binary header that can be stripped to reveal the text
 records.
"""
from __future__ import annotations

from pathlib import Path
import struct

INPUT_FILE = Path("dungeon/dungeon.bin")
OUTPUT_DIR = Path("output/dungeon")

ENTRY_SIZE = 0x104  # 256-byte name + 4-byte unused field
HEADER_FORMAT = "<IIII"


def xor_decode(data: bytes) -> bytes:
    """Decode ``data`` by XOR-ing every byte with ``0xFF``."""

    return bytes(b ^ 0xFF for b in data)


def strip_header(decoded: bytes) -> bytes:
    """Remove the 8-byte binary header when present."""

    if len(decoded) >= 8 and decoded[:4] == b"\xfe\xff\xff\xff":
        return decoded[8:]
    return decoded


def strip_padding(decoded: bytes) -> bytes:
    """Trim trailing ``0xFF`` padding bytes from ``decoded``."""

    end = len(decoded)
    while end > 0 and decoded[end - 1] == 0xFF:
        end -= 1
    return decoded[:end]


def parse_names(data: bytes, count: int) -> tuple[list[str], int]:
    """Return entry names and the offset immediately after the table."""

    names: list[str] = []
    position = struct.calcsize(HEADER_FORMAT)

    for _ in range(count):
        entry = data[position : position + ENTRY_SIZE]
        name = entry[:0x100].split(b"\x00", 1)[0].decode("ascii", "replace")
        names.append(name)
        position += ENTRY_SIZE

    return names, position


def parse_offsets(data: bytes, start: int, count: int) -> tuple[list[int], int]:
    """Return the absolute payload offsets and the position after the table."""

    size = struct.calcsize("<" + "I" * count)
    end = start + size
    offsets = list(struct.unpack("<" + "I" * count, data[start:end]))
    return offsets, end


def main() -> None:
    if not INPUT_FILE.exists():
        raise SystemExit(f"Input file not found: {INPUT_FILE}")

    data = INPUT_FILE.read_bytes()
    _, _, _, entry_count = struct.unpack(HEADER_FORMAT, data[: struct.calcsize(HEADER_FORMAT)])

    names, after_names = parse_names(data, entry_count)
    offsets, _ = parse_offsets(data, after_names, entry_count)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for idx, name in enumerate(names):
        start = offsets[idx]
        end = offsets[idx + 1] if idx + 1 < len(offsets) else len(data)
        payload = data[start:end]

        decoded = strip_padding(strip_header(xor_decode(payload)))
        output_path = OUTPUT_DIR / f"{name}.txt"
        output_path.write_bytes(decoded)

        print(f"Extracted {name} ({start:#x}-{end:#x}) -> {output_path}")


if __name__ == "__main__":
    main()
