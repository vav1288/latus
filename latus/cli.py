import sys

import latus.const
import latus.preferences
import latus.crypto
import latus.util
import latus.sync
import latus.logger
import latus.folders
import latus.patch_crypto_be_discovery


def main(latus_appdata_roaming_folder):

    latus.logger.log.info('cli')

    latus.patch_crypto_be_discovery.patch_crypto_be_discovery()  # remove this when cryptography discovery gets fixed

    pref = latus.preferences.Preferences(latus_appdata_roaming_folder)

    # make sure we have a crypto key before proceeding
    key = pref.get_crypto_key()
    if not key:
        sys.exit('No crypto key found in preferences.  Please use -k to provide or generate one.')

    latus_folder = pref.get_latus_folder()
    if not latus_folder:
        sys.exit('No latus folder set - please initialize with the --latus option.')

    cloud_root = pref.get_cloud_root()
    if not cloud_root:
        sys.exit('No cloud folder set - please initialize with the --cloud option.')

    node_id = pref.get_node_id()
    if not node_id:
        sys.exit('No node id - please initialize with the --id option')

    sync = latus.sync.Sync(latus_appdata_roaming_folder)
    sync.start()
    input('Hit enter to exit.')
    sync.request_exit()
