
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
import uuid
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
    parser.add_argument('-i', '--id', nargs='?', help="Node ID value (omit value to automatically generate new one)",
                        default=None, const=True)
    parser.add_argument('-k', '--key', nargs='?', help="set crypto key (omit value to automatically generate new one)",
                        default=None, const=True)
    parser.add_argument('-cli', action='store_true', help="use command line interface (not GUI)")
    parser.add_argument('-v', '--verbose', action='store_true', help="output status messages during execution")
    args = parser.parse_args()

    latus_appdata_roaming_folder = set_from_args(args)
    if args.cli:
        latus.cli.main(latus_appdata_roaming_folder)
    else:
        latus.gui.main(latus_appdata_roaming_folder)

def set_from_args(args):
    """
    Setup config based on args from argparse
    :param args:
    :return:
    """

    if args.verbose:
        latus.logger.set_console_log_level(logging.INFO)
    latus.logger.log.info('log folder : %s' % latus.util.get_latus_log_folder())

    # determine appdata (roaming) folder
    if args.appdata:
        # particularly useful for testing ( args.ar is the appdata roaming folder )
        latus_appdata_roaming_folder = os.path.join(args.appdata, latus.const.NAME)
    else:
        latus_appdata_roaming_folder = latus.util.get_latus_appdata_roaming_folder()  # default

    latus.logger.log.info('latus_appdata_roaming_folder : %s' % latus_appdata_roaming_folder)
    config = latus.config.Config(latus_appdata_roaming_folder)

    # determine crypto key
    if args.key:
        # Key option specified - either with no value or with a key value.  If no value given we get True (the
        # default which tells us to generate a key).
        if args.key is True:
            key = latus.crypto.new_key()  # generate if no key parameter given
            config.crypto_set(key)
            latus.logger.log.info('New crypto key : %s' % config.crypto_get_string())
        else:
            config.crypto_set_string(args.key)  # command line is a string

    # determine node id
    if args.id:
        # node id option specified - either with no value or with an id.  If no value given we get True (the
        # default which tells us to generate a new node id).
        if args.id is True:
            node_id = str(uuid.uuid4())  # generate if no id given
            config.node_id_set(node_id)
            latus.logger.log.info('New node id : %s' % config.node_id_get())
        else:
            config.node_id_set(args.id)  # command line is a string


    # remember folder settings so the user doesn't have to specify them next time
    if args.latus:
        config.latus_folder_set(args.latus)
    if args.cloud:
        config.cloud_root_set(args.cloud)

    return latus_appdata_roaming_folder


if __name__ == "__main__":
    main()

