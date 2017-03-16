#!/usr/bin/env bash
#
# this uses the pytest coverage files (run pytest first)
mkdir temp/coverage
venv/bin/coverage report > temp/coverage/report.txt
venv/bin/coverage annotate -d temp/coverage