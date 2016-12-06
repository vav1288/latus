#!/usr/bin/env bash
sudo rm -rf /Applications/latus.app
./make_venv.sh
# only if osnap PyPI is not up to date enough
# ./install_osnap.sh
./make_osnapy.sh
./make_installer.sh
