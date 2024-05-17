#!/bin/bash
app_path=/home/user/apps/med-tracker-hh

export FLASK_APP=app.py
source $app_path/venv/bin/activate

cd $app_path

$app_path/venv/bin/python $app_path/app.py
