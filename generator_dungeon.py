"""Generate a dungeon archive compatible with ``dungeon/dungeon.bin``.

The tool rebuilds the binary container from individual dungeon JSON files.
Each JSON file is expected to live inside ``files/dungeon`` relative to the
script (configurable via ``--input-dir``) and contain two keys: ``spawns`` and
``blocks``. The output layout mirrors the decoded structure produced by
``extract_dungeon.py``: a date/entry-count header, fixed-size name table, an
offset table, and XOR-encoded payloads.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
import argparse
import json
import sys
from typing import Iterable

NAME_RECORD_SIZE = 260  # 256 bytes for the name + 4 bytes reserved
HEADER_UNITS = 4
ENCODING = "windows-1252"


@dataclass(frozen=True)
class DungeonScript:
    name: str
    data: dict


DUNGEON_NAMES: list[str] = [
    "lv01_training_ring",
    "lv03_base_camp",
    "lv06_camp_spike",
    "lv08_camp_escape",
    "lv10_planet_alderan",
    "lv13_mine_entrance",
    "lv16_mine_alderan",
    "lv18_inner_mine",
    "lv20_mine_exit",
    "lv23_lava_sea",
    "lv26_lava_sea_2",
    "lv28_lava_sea_3",
    "lv30_acurin_ruins",
    "lv33_acurin_ruins_2",
    "lv35_acurin_ruins_3",
    "lv36_planet_acurin",
    "lv38_planet_acurin_2",
    "lv40_port_acurin",
    "lv43_escape_acurin",
    "lv46_planet_meca",
    "lv48_planet_meca_2",
    "lv50_hidden_archive",
    "lv53_secret_passage",
    "lv56_destroy_meca",
    "lv58_destroy_meca_2",
    "lv60_escape_from_meca",
    "lv61_ship_takeover",
    "lv63_mera_mountain",
    "lv66_mera_mountain_2",
    "lv68_mera_mountain_3",
    "lv70_mera_mountain_4",
    "elite_lv08_the_fallen",
    "elite_lv18_lava_field",
    "elite_lv28_the_pirate",
    "elite_lv38_evil_port",
    "elite_lv48_bloodway",
    "mt01_d01.dun",
    "mt02_d01.dun",
    "mt03_d01.dun",
    "mt04_d01.dun",
    "p_elite01.dun",
    "p_elite02.dun",
    "p_elite03.dun",
    "p_elite04.dun",
    "p_elite05.dun",
    "p_elite06.dun",
    "p_elite07.dun",
    "p_elite08.dun",
    "p_elite09.dun",
    "p_elite10.dun",
    "p_elite32.dun",
    "p01_d01.dun",
    "p02_d01.dun",
    "p03_d01.dun",
    "p04_d01.dun",
    "p04_d02.dun",
    "p05_d01.dun",
    "p06_d01.dun",
    "p07_d01.dun",
    "p09_d01.dun",
    "p10_d01.dun",
    "p11_d01.dun",
    "p12_d01.dun",
    "p12_d02.dun",
    "p13_d01.dun",
    "p14_d01.dun",
    "p15_d01.dun",
    "p15_d02.dun",
    "p16_d01.dun",
    "p17_d01.dun",
    "p18_d01.dun",
    "p19_d01.dun",
    "p20_d01.dun",
    "puppers.dun",
    "spacestation.dun",
    "stalkerhome.dun",
    "strikejungle.dun",
    "summer_raid.dun",
    "survivalcorruptmode.dun",
    "survivalnormalmode.dun",
    "wasteland_br.dun",
    "xmasfactory.dun",
]


def load_scripts(input_dir: Path, names: Iterable[str]) -> list[DungeonScript]:
    scripts: list[DungeonScript] = []
    for name in names:
        script_path = input_dir / f"{name}.json"
        try:
            data = json.loads(script_path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise FileNotFoundError(
                f"Missing dungeon JSON: {script_path}. Provide all files before generation."
            ) from exc
        scripts.append(DungeonScript(name=name, data=data))
    return scripts


def _write_header(buffer: bytearray, today: date, script_count: int) -> None:
    for unit in (today.year, today.month, today.day, script_count):
        buffer.extend(int(unit).to_bytes(length=4, byteorder="little"))


def _write_name_table(buffer: bytearray, scripts: list[DungeonScript]) -> None:
    for script in scripts:
        encoded_name = script.name.encode(ENCODING, errors="replace")
        if len(encoded_name) > NAME_RECORD_SIZE:
            raise ValueError(f"Dungeon name too long for record: {script.name}")

        buffer.extend(encoded_name)
        buffer.extend(b"\x00" * (NAME_RECORD_SIZE - len(encoded_name)))


def _encode_script(script_obj: dict) -> bytes:
    spawns = script_obj["spawns"]
    blocks = script_obj["blocks"]

    script = bytearray()

    # Spawn table
    script.extend(str(len(spawns)).encode(ENCODING, errors="replace"))
    script.extend([0x0D, 0x0A])

    for idx, monster_id in enumerate(spawns):
        script.extend(str(idx).encode(ENCODING, errors="replace"))
        script.append(0x09)
        script.extend(str(monster_id).encode(ENCODING, errors="replace"))
        script.extend([0x0D, 0x0A])

    script.extend([0x0D, 0x0A])

    # Block table
    script.extend(str(len(blocks)).encode(ENCODING, errors="replace"))
    script.extend([0x0D, 0x0A])

    for block in blocks:
        for array_name in ["rect", "enemies", "respawn", "clear", "vip", "exceptional"]:
            if array_name != "rect":
                script.append(0x09)
                script.extend(str(len(block[array_name])).encode(ENCODING, errors="replace"))
                script.append(0x09)

            for value in block[array_name]:
                script.append(0x09)
                script.extend(str(value).encode(ENCODING, errors="replace"))
                script.append(0x09)

            script.extend([0x0D, 0x0A])

        for value_key in ["text", "countdown"]:
            script.extend(str(block[value_key]).encode(ENCODING, errors="replace"))
            script.extend([0x09, 0x0D, 0x0A])

    return bytes((byte ^ 0xFF) for byte in script)


def build_archive(scripts: list[DungeonScript], today: date | None = None) -> bytes:
    today = today or date.today()
    archive = bytearray()

    _write_header(archive, today, len(scripts))
    _write_name_table(archive, scripts)

    offset_table_pos = len(archive)
    offset_table_size = len(scripts) * 4
    archive.extend(b"\x00" * offset_table_size)

    offsets: list[int] = []
    for script in scripts:
        offsets.append(len(archive))

        body = _encode_script(script.data)
        archive.extend([0x01, 0x00, 0x00, 0x00])
        archive.extend(len(body).to_bytes(length=4, byteorder="little"))
        archive.extend(body)
        archive.extend([0x00, 0x00, 0x00, 0x00])

    for idx, offset in enumerate(offsets):
        start = offset_table_pos + idx * 4
        archive[start : start + 4] = offset.to_bytes(length=4, byteorder="little")

    return bytes(archive)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path(__file__).parent / "files" / "dungeon",
        help="Directory containing <name>.json dungeon definitions.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("dungeon/dungeon.bin"),
        help="Destination for the generated binary archive.",
    )
    parser.add_argument(
        "--names",
        nargs="*",
        default=DUNGEON_NAMES,
        help="Optional subset of dungeon names to build (defaults to the full list).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])

    scripts = load_scripts(args.input_dir, args.names)
    archive = build_archive(scripts)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(archive)
    print(f"Generated {args.output} with {len(scripts)} scripts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
