"""Convenient viewer for ``p_monai`` data in text or encoded binary form.

The application can open either the decrypted ``p_monai.txt`` or the raw
``p_monai.bin`` resource (decoding it automatically) and prints the content to
stdout. Optionally, it can also save the decoded text to a specified output
path.
"""
from __future__ import annotations

import argparse
from pathlib import Path

HEADER_PREFIX = b"\xfe\xff\xff\xff"
DEFAULT_BIN_PATH = Path("dungeon/p_monai.bin")
DEFAULT_TXT_PATH = Path("output/dungeon/p_monai.txt")


def xor_decode(data: bytes) -> bytes:
    """Return ``data`` XOR-ed with ``0xFF``."""

    return bytes(b ^ 0xFF for b in data)


def strip_header(decoded: bytes) -> bytes:
    """Remove the leading 8-byte header when present."""

    if len(decoded) >= 8 and decoded.startswith(HEADER_PREFIX):
        return decoded[8:]
    return decoded


def strip_padding(decoded: bytes) -> bytes:
    """Trim trailing ``0xFF`` padding bytes."""

    end = len(decoded)
    while end > 0 and decoded[end - 1] == 0xFF:
        end -= 1
    return decoded[:end]


def load_p_monai_text(path: Path) -> str:
    """Load ``p_monai`` data from ``path`` and return it as text."""

    raw_bytes = path.read_bytes()
    if path.suffix.lower() == ".bin":
        raw_bytes = strip_padding(strip_header(xor_decode(raw_bytes)))
    return raw_bytes.decode("utf-8", errors="replace")


def pick_default_path() -> Path:
    """Choose a sensible default input path for ``p_monai`` data."""

    if DEFAULT_BIN_PATH.exists():
        return DEFAULT_BIN_PATH
    if DEFAULT_TXT_PATH.exists():
        return DEFAULT_TXT_PATH
    raise FileNotFoundError(
        "Could not find default p_monai sources. Provide --input explicitly."
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Open the p_monai table from a text file or decode it from the "
            "original binary resource."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help=(
            "Path to p_monai.txt or p_monai.bin. If omitted, the tool searches "
            "for dungeon/p_monai.bin first, then output/dungeon/p_monai.txt."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "Optional path to save the decoded text. When omitted, the tool only "
            "prints to stdout."
        ),
    )
    parser.add_argument(
        "--no-print",
        action="store_true",
        help="Do not print the decoded content to stdout.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path: Path = args.input or pick_default_path()

    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    text = load_p_monai_text(input_path)

    if not args.no_print:
        print(text)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(f"Saved decoded text to: {args.output}")


if __name__ == "__main__":
    main()
