
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
import os
import win32event

import latus.const
import latus.config
import latus.crypto
import latus.util
import latus.sync


def main():
    parser = argparse.ArgumentParser(description="efficient and secure cloud-based folder sync")
    parser.add_argument('-l', '--latus', metavar='path', help="latus folder")
    parser.add_argument('-c', '--cloud', metavar='path', help="cloud folder")
    parser.add_argument('-v', '--verbose', action='store_true', help="output status messages during execution")
    args = parser.parse_args()

    # controls exit for CLI
    keyboard_event_handle = win32event.CreateEvent(None, 0, 0, None)

    # determine appdata folder
    latus_appdata_folder = os.path.join(latus.util.get_appdata_folder(), latus.const.NAME)
    if args.verbose:
        print('latus_appdata_folder', latus_appdata_folder)
    config = latus.config.Config(latus_appdata_folder)

    # determine crypto key
    key = config.crypto_get()
    if not key:
        key = latus.crypto.new_key()
        if args.verbose:
            print('new crypto key', key)
        config.crypto_set(key)

    if args.cloud:
        config.cloud_root_set(args.cloud)

    if args.latus:
        config.latus_folder_set(args.latus)

    cloud_root = config.cloud_root_get()
    latus_folder = config.latus_folder_get()

    if not cloud_root:
        print('no cloud folder set - please initialize with the --cloud option')
        exit()

    if not latus_folder:
        print('no latus folder set - please initialize with the --latus option')
        exit()

    sync = latus.sync.Sync(key, latus_folder, cloud_root, exit_event_handle=keyboard_event_handle, verbose=args.verbose)
    sync.start()
    input('hit enter to exit')
    win32event.PulseEvent(keyboard_event_handle)

if __name__ == "__main__":
    main()

