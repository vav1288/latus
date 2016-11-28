#!/usr/bin/env bash
pushd .
cd ..
export PYTHONPATH=.
venv/bin/python3 systst/systst.py
popd
