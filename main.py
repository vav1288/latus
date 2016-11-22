
"""
    latus (www.lat.us) - efficient and secure cloud-based folder sync
    Copyright (C) 2014-2015  James C. Abel

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

import sys
import argparse
import appdirs
import logging

import latus
import latus.gui
import latus.util
import latus.const
import latus.preferences
import latus.crypto
import latus.logger


def main():
    latus.logger.init()

    # ensure the frozen app is execution on the version it needs.
    is_64bits = sys.maxsize > 2**32
    if not is_64bits:
        not_64_bit_message = 'error:not a 64 bit interpreter - exiting'
        print(not_64_bit_message)
        sys.exit(not_64_bit_message)
    req_version = (3,4)
    if sys.version_info < req_version:
        old_version_message = 'expected python version %s or better, got %s - exiting' % (str(req_version), str(sys.version))
        print(old_version_message)
        sys.exit(old_version_message)

    args = latus.util.arg_parse()

    try:
        latus.gui.main(args.appdatafolder)
    except Exception:
        latus.logger.log.exception("Fatal error")


if __name__ == "__main__":
    main()

