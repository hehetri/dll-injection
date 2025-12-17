"""Decode and unpack dungeon.bin-style archives.

The extractor applies XOR 0xFF to the input file, optionally removes a map-style
8-byte header, and tries to split packed entries if the file contains a simple
name/size table. If no table is detected, the fully decoded payload is written
as a single blob for manual inspection.
"""

from __future__ import annotations

import argparse
import os
import struct
from pathlib import Path
from typing import Iterable, Tuple

DEFAULT_INPUT_PATHS = [Path("dungeon/dungeon.bin"), Path("dungeon.bin")]
DEFAULT_OUTPUT_DIR = Path("output/dungeon")
HEADER_SIZE = 8


def xor_decode(data: bytes) -> bytes:
    return bytes(b ^ 0xFF for b in data)


def strip_map_header(decoded: bytes) -> bytes:
    """Remove an 8-byte header when it matches the common map format.

    The header is removed when the first four bytes are zero and the following
    four bytes equal the remaining payload length.
    """

    if len(decoded) < HEADER_SIZE:
        return decoded

    leading_zero = decoded[:4] == b"\x00\x00\x00\x00"
    declared_size = struct.unpack_from("<I", decoded, 4)[0]
    payload = decoded[HEADER_SIZE:]
    if leading_zero and declared_size == len(payload):
        return payload
    return decoded


def parse_table(decoded: bytes) -> Iterable[Tuple[str, bytes]]:
    """Attempt to parse a simple name/size table archive.

    Expected layout:
    - 4-byte little-endian entry count
    - For each entry: 4-byte name length, name bytes, 4-byte data length, data.

    If parsing fails, an empty iterator is returned, signaling the caller to
    fall back to writing a single blob.
    """

    offset = 0
    if len(decoded) < 4:
        return []

    entry_count = struct.unpack_from("<I", decoded, offset)[0]
    offset += 4
    entries = []
    try:
        for _ in range(entry_count):
            if offset + 8 > len(decoded):
                return []
            name_len = struct.unpack_from("<I", decoded, offset)[0]
            offset += 4
            if offset + name_len > len(decoded):
                return []
            name_bytes = decoded[offset : offset + name_len]
            offset += name_len
            data_len = struct.unpack_from("<I", decoded, offset)[0]
            offset += 4
            if offset + data_len > len(decoded):
                return []
            data = decoded[offset : offset + data_len]
            offset += data_len
            entries.append((name_bytes.decode(errors="replace"), data))
    except struct.error:
        return []

    return entries if entries else []


def write_blob(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    print(f"wrote {path.relative_to(Path.cwd())} ({len(data)} bytes)")


def decode_file(input_path: Path, output_dir: Path) -> None:
    raw = input_path.read_bytes()
    decoded = xor_decode(raw)
    decoded = strip_map_header(decoded)

    entries = list(parse_table(decoded))
    if entries:
        for name, content in entries:
            safe_name = name.strip() or "entry"
            write_blob(output_dir / safe_name, content)
    else:
        blob_path = output_dir / f"{input_path.stem}.decoded"
        write_blob(blob_path, decoded)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input",
        nargs="?",
        type=Path,
        default=None,
        help="Path to dungeon.bin (defaults to dungeon/dungeon.bin or dungeon.bin)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory to write extracted files (default: {DEFAULT_OUTPUT_DIR})",
    )
    args = parser.parse_args()

    if args.input:
        input_path = args.input
    else:
        input_candidates = [p for p in DEFAULT_INPUT_PATHS if p.exists()]
        if not input_candidates:
            raise FileNotFoundError(
                "No dungeon.bin found. Provide a path or place it under dungeon/."
            )
        input_path = input_candidates[0]

    decode_file(input_path, args.output)


if __name__ == "__main__":
    main()
