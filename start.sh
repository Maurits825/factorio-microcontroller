#!/bin/sh
. venv/Scripts/activate
cd "python scripts"
python program_to_rom_blueprint.py --help
$SHELL
