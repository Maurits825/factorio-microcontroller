#!/bin/sh
. venv/Scripts/activate
cd "python scripts"
python binary_to_rom_blueprint.py --help
$SHELL
