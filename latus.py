
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

import os
import logging
import argparse

import latus.cli
import latus.gui
import latus.util
import latus.const
import latus.config
import latus.crypto
import latus.logger

def main():
    latus.logger.init()
    parser = argparse.ArgumentParser(description="efficient and secure cloud-based folder sync")
    parser.add_argument('-l', '--latus', metavar='path', help="latus folder")
    parser.add_argument('-c', '--cloud', metavar='path', help="cloud folder")
    parser.add_argument('-a', '--appdata', metavar='path', help="OS's appdata folder")
    parser.add_argument('-cli', action='store_true', help="use command line interface (not GUI)")
    parser.add_argument('-v', '--verbose', action='store_true', help="output status messages during execution")
    args = parser.parse_args()

    latus_appdata_folder = set_from_args(args)
    if args.cli:
        latus.cli.main(latus_appdata_folder)
    else:
        latus.gui.main(latus_appdata_folder)

def set_from_args(args):
    """
    Setup config based on args from argparse
    :param args:
    :return:
    """

    if args.verbose:
        latus.logger.set_console_log_level(logging.INFO)
    latus.logger.log.info('log folder : %s' % latus.util.get_latus_log_folder())

    # determine appdata folder
    if args.appdata:
        # particularly useful for testing ( args.appdata is the OS appdata folder )
        latus_appdata_folder = os.path.join(args.appdata, latus.const.NAME)
    else:
        latus_appdata_folder = latus.util.get_latus_appdata_folder()  # default
    config = latus.config.Config(latus_appdata_folder)
    if args.cli and args.verbose:
        print('latus_appdata_folder', latus_appdata_folder)

    # determine crypto key
    key = config.crypto_get()
    if not key:
        key = latus.crypto.new_key()
        if args.verbose:
            print('New crypto key:', key)
        config.crypto_set(key)

    # remember folder settings so the user doesn't have to specify them next time
    if args.latus:
        config.latus_folder_set(args.latus)
    if args.cloud:
        config.cloud_root_set(args.cloud)

    return latus_appdata_folder


if __name__ == "__main__":
    main()

