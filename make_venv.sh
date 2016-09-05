#!/usr/bin/env bash
/usr/local/Cellar/python3/3.5.2_1/Frameworks/Python.framework/Versions/3.5/bin/pyvenv --clear venv
chmod 555 venv/bin/activate
venv/bin/pip install -U pip
venv/bin/pip install -U setuptools
