#!/bin/bash

export FLASK_APP=app.py
source /home/pi/med-tracker/venv/bin/activate

cd /home/pi/med-tracker

/home/pi/med-tracker/venv/bin/python /home/pi/med-tracker/app.py
