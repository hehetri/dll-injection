"""Re-encrypts assets by applying the XOR 0xFF transformation.

The script mirrors ``decrypt.py``: it can handle a single file or every
``.bin`` file in a directory, writing output with a configurable suffix so the
original resources remain untouched unless explicitly overwritten.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List


def xor_transform(data: bytes) -> bytes:
    """Apply the XOR 0xFF transformation used by the game assets."""

    return bytes(byte ^ 0xFF for byte in data)


def process_file(input_path: Path, output_path: Path) -> None:
    """Read ``input_path``, XOR its bytes, and write ``output_path``."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    transformed = xor_transform(input_path.read_bytes())
    output_path.write_bytes(transformed)


def derive_output_path(path: Path, suffix: str) -> Path:
    stem = path.stem
    extension = path.suffix
    return path.with_name(f"{stem}{suffix}{extension}")


def iter_input_files(target: Path) -> Iterable[Path]:
    if target.is_file():
        yield target
        return

    for file_path in sorted(target.glob("*.bin")):
        if file_path.is_file():
            yield file_path


def run(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Encrypt repository assets with XOR 0xFF.")
    parser.add_argument(
        "target",
        nargs="?",
        default=Path("."),
        type=Path,
        help="Single file or directory containing .bin assets (defaults to current directory).",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Optional output file when encrypting a single source file.",
    )
    parser.add_argument(
        "--suffix",
        default="_encrypted",
        help="Suffix to append to encrypted files when output is not specified (default: _encrypted).",
    )

    args = parser.parse_args(argv)

    files = list(iter_input_files(args.target))
    if not files:
        raise SystemExit(f"No .bin files found under {args.target!s}.")

    for file_path in files:
        if args.output and len(files) == 1:
            output_path = args.output
        else:
            output_path = derive_output_path(file_path, args.suffix)

        print(f"Encrypting {file_path} -> {output_path}")
        process_file(file_path, output_path)


if __name__ == "__main__":
    run()
