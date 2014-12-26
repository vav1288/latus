
import os
import win32event

import latus.const
import latus.config
import latus.crypto
import latus.util
import latus.sync

def wizard(args):
    print('Setup wizard not yet done.')

def main(args):
    if args.verbose:
        print('CLI mode.')

    if args.wizard:
        wizard(args)

    # determine appdata folder
    if args.appdata:
        # for testing purposes
        appdata = os.path.join(args.appdata)
    else:
        appdata = latus.util.get_appdata_folder()
    latus_appdata_folder = os.path.join(appdata, latus.const.NAME)
    config = latus.config.Config(latus_appdata_folder)
    if args.verbose:
        print('latus_appdata_folder', latus_appdata_folder)

    # determine crypto key
    key = config.crypto_get()
    if not key:
        key = latus.crypto.new_key()
        if args.verbose:
            print('New crypto key:', key)
        config.crypto_set(key)

    if args.cloud:
        config.cloud_root_set(args.cloud)

    if args.latus:
        config.latus_folder_set(args.latus)

    cloud_root = config.cloud_root_get()
    latus_folder = config.latus_folder_get()

    if not cloud_root:
        exit('No cloud folder set - please initialize with the --cloud option.')

    if not latus_folder:
        exit('No latus folder set - please initialize with the --latus option.')

    sync = latus.sync.Sync(key, latus_folder, cloud_root, verbose=args.verbose)
    sync.start()
    input('Hit enter to exit.')
    sync.request_exit()