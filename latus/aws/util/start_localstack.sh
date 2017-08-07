#!/usr/bin/env bash
# start up the localstack AWS emulator for testing (this is in a separate project that merely has a venv with localstack installed)
pushd .
cd ~/projects/latus_localstack/
venv/bin/localstack start
popd
