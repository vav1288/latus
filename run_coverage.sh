#!/usr/bin/env bash
#
mkdir temp/coverage
venv/bin/coverage report > temp/coverage/report.txt
venv/bin/coverage annotate -d temp/coverage