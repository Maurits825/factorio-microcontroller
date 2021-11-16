#!/bin/sh
python -m venv ./venv
. venv/Scripts/activate
cd "python scripts"
pip install -r requirements.txt
$SHELL
