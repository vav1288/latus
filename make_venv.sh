#!/usr/bin/env bash
/usr/local/bin/pyvenv --clear venv
venv/bin/pip install -U pip
venv/bin/pip install -U setuptools
venv/bin/pip install -r requirements.txt
