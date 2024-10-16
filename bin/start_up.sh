#!/bin/sh

venv_name="/home/mattia/Documents/Git/super-duper-bot/.venv"
python_program="/home/mattia/Documents/Git/super-duper-bot/bin/main.py"
requirements_file="/home/mattia/Documents/Git/super-duper-bot/requirements.txt"

if ! [[ -d $venv_name]]; then
	python3 -m venv $venv_name
fi

source $venv_name/bin/activate

pip3 install -r $requirements_file

python3 $python_program
