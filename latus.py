
"""
    latus (www.lat.us) - efficient and secure cloud-based folder sync
    Copyright (C) 2014  James C. Abel

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import argparse

import latus.cli
import latus.gui

def main():
    parser = argparse.ArgumentParser(description="efficient and secure cloud-based folder sync")
    parser.add_argument('-l', '--latus', metavar='path', help="latus folder")
    parser.add_argument('-c', '--cloud', metavar='path', help="cloud folder")
    parser.add_argument('-a', '--appdata', metavar='path', help="OS's appdata folder")
    parser.add_argument('-cli', action='store_true', help="use command line interface (not GUI)")
    parser.add_argument('-w', '--wizard', action='store_true', help="run configuration wizard")
    parser.add_argument('-v', '--verbose', action='store_true', help="output status messages during execution")
    args = parser.parse_args()

    if args.cli:
        latus.cli.main(args)
    else:
        latus.gui.main(args)

if __name__ == "__main__":
    main()

