import argparse
import datetime
import json
import os
import sys


def _strip_block_comments(text):
    """Remove C-style /* */ comments from a text block."""

    result = []
    in_comment = False
    i = 0
    while i < len(text):
        if not in_comment and text.startswith("/*", i):
            in_comment = True
            i += 2
            continue

        if in_comment and text.startswith("*/", i):
            in_comment = False
            i += 2
            continue

        if not in_comment:
            result.append(text[i])

        i += 1

    return "".join(result)


def _load_dungeon_json(dungeon_name, base_path):
    path = os.path.join(base_path, f"{dungeon_name}.json")
    with open(path, "r", encoding="utf-8") as handle:
        content = handle.read()

    # Remove UTF-8 BOM if present and strip C-style comments early so regular JSON parsing
    # has the best chance of succeeding.
    content = _strip_block_comments(content.lstrip("\ufeff"))

    # Remove line comments and trailing whitespace-only lines before decoding.
    cleaned_lines = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("//") or stripped.startswith("#"):
            continue
        cleaned_lines.append(stripped)

    cleaned_content = "\n".join(cleaned_lines).strip()

    if not cleaned_content:
        raise ValueError(
            f"Erro ao ler {path}: o arquivo parece vazio ou contém apenas comentários."
        )

    decoder = json.JSONDecoder()
    try:
        obj, end = decoder.raw_decode(cleaned_content)
    except json.JSONDecodeError as exc:
        if exc.pos == 0:
            raise ValueError(
                f"Erro ao ler {path}: não há JSON válido (linha {exc.lineno} coluna {exc.colno})."
            ) from exc
        raise ValueError(
            f"Erro ao ler {path}: {exc.msg} (linha {exc.lineno} coluna {exc.colno})"
        ) from exc

    remainder = cleaned_content[end:].strip()
    if remainder:
        print(
            f"Aviso: Dados adicionais ignorados em {path} após a posição {end}. Verifique a formatação JSON."
        )

    return obj


def run(args=None):
    parser = argparse.ArgumentParser(
        description="Generate dungeon.bin from individual dungeon JSON definitions."
    )
    parser.add_argument(
        "output",
        help="Caminho onde o dungeon.bin será gerado",
    )
    parser.add_argument(
        "--input-dir",
        default=os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "files", "dungeon"),
        help="Diretório contendo os arquivos .json de cada dungeon (padrão: files/dungeon ao lado do script)",
    )

    parsed = parser.parse_args(args)
    output = parsed.output

    try:
        dungeon_object = {}

        dungeons = [
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

        if not os.path.isdir(parsed.input_dir):
            raise FileNotFoundError(
                f"Diretório de entrada não encontrado: {parsed.input_dir}. Crie-o ou informe o caminho correto com --input-dir."
            )

        for dungeon in dungeons:
            dungeon_object[dungeon] = _load_dungeon_json(dungeon, parsed.input_dir)

        # Allocate a byte array for our file
        file = bytearray()

        # Read all dungeon script names
        scripts = dungeon_object.keys()
        print("Parsing the following scripts: {0}".format(scripts))

        # Construct the file header. The file header consists of the current year, month and day and the amount of scripts
        date = datetime.datetime.now().date()
        for unit in [date.year, date.month, date.day, len(scripts)]:
            file.extend(int(unit).to_bytes(length=4, byteorder="little"))

        # Construct array of script names. Each instance has 260 bytes allocated to it
        for script_name in scripts:
            file.extend(script_name.encode("windows-1252", errors="replace"))

            # Ensure that each instance has 260 bytes. We'll fill the remaining bytes with null
            for _ in range(260 - len(script_name)):
                file.append(0x00)

        """ We're going to allocate 380 bytes for the offset map. We will mutate this after we have generated
            all scripts because then we know all the offsets. """

        # Get offset map's offset, for later mutation
        offset_map_position = len(file)

        # Allocate 380 bytes. We're going to use this later
        for _ in range(380):
            file.append(0x00)

        print(
            "Allocated 380 bytes for the offset map. The offset for the map is: {0} ({1})".format(
                offset_map_position,
                hex(offset_map_position),
            )
        )

        # Create offset list for later use
        offsets = []

        # Generate dungeon scripts and add the script to the file
        for idx, script_name in enumerate(dungeon_object):
            # Read script object and get offset
            script_object = dungeon_object[script_name]
            offset = len(file)
            offsets.append(offset)

            # Generate dungeon script, allocate a bytearray for the script content
            script = bytearray()

            # Retrieve the amount of spawns and the number of blocks
            num_spawns, num_blocks = len(script_object["spawns"]), len(script_object["blocks"])

            # Initialize min_mobs number - the amount of mobs a player actually needs to kill
            min_mobs = 0

            # Add number of spawns to the script and add 0x09, 0x0D 0x0A to the end of it
            script.extend(str(num_spawns).encode("windows-1252", errors="replace"))
            script.extend([0x0D, 0x0A])

            # Write monster spawns to the script. The two values are separated with 0x09 and ends with 0x09, 0x0D, 0x0A
            for _idx, monster_id in enumerate(script_object["spawns"]):
                script.extend(str(_idx).encode("windows-1252", errors="replace"))
                script.append(0x09)
                script.extend(str(script_object["spawns"][_idx]).encode("windows-1252", errors="replace"))
                script.extend([0x0D, 0x0A])

            # I think this is just a comment that is needed. For some reason.
            script.extend([0x0D, 0x0A])

            # Add number of blocks to the script and add 0x09, 0x0D 0x0A to the end of it
            script.extend(str(num_blocks).encode("windows-1252", errors="replace"))
            script.extend([0x0D, 0x0A])

            # Begin parsing of blocks
            for block in script_object["blocks"]:
                # Parse all the arrays
                for array in ["rect", "enemies", "respawn", "clear", "vip", "exceptional"]:
                    # Add array length for these scopes
                    if array != "rect":
                        script.append(0x09)
                        script.extend(str(len(block[array])).encode("windows-1252", errors="replace"))
                        script.append(0x09)

                    # If the array is clear, we want to get its length and add it to min_mobs
                    if array == "clear":
                        for value in block["clear"]:
                            monster_idx = script_object["spawns"][value]
                            if monster_idx != -1:
                                min_mobs += 1

                    # Add array value to the array in question
                    for value in block[array]:
                        script.append(0x09)
                        script.extend(str(value).encode("windows-1252", errors="replace"))
                        script.append(0x09)

                    # End the array with 0x0D, 0x0A
                    script.extend([0x0D, 0x0A])

                # Add the block text and countdown value to the block
                for value in ["text", "countdown"]:
                    script.extend(str(block[value]).encode("windows-1252", errors="replace"))
                    script.extend([0x09, 0x0D, 0x0A])

            # We have generated the script now. It is time to begin writing the script header
            # The script header includes the length of the script we have just generated
            file.extend([0x01, 0x00, 0x00, 0x00])
            file.extend(len(script).to_bytes(length=4, byteorder="little"))

            # Xor the script's content
            for i in range(len(script)):
                script[i] = script[i] ^ 0xFF

            # Append the script to the file
            file.extend(script)

            # Write script footer to file
            file.extend([0x00, 0x00, 0x00, 0x00])

            print(
                "Parsed script {0} at offset {1} ({2}) - spawns: {3} - blocks: {4} - min_mobs: {5} ... ".format(
                    script_name,
                    offset,
                    hex(offset),
                    num_spawns,
                    num_blocks,
                    min_mobs,
                )
            )

        # Parse offset array by adding each offset into a separate array
        offsets_array = bytearray()
        for offset in offsets:
            offsets_array.extend(int(offset).to_bytes(length=4, byteorder="little"))

        # Write the offset array into the offset map position
        for idx, byte in enumerate(offsets_array):
            file[offset_map_position + idx] = byte

        # Write file buffer to output file
        with open(output, "wb") as handle:
            handle.write(file)

        print(f"dungeon.bin gerado com sucesso em: {output}")

    except Exception as e:
        print("An error occurred while generating dungeon.bin: ", e)


if __name__ == "__main__":
    run()
