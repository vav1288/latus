import sys

import latus.const
import latus.config
import latus.crypto
import latus.util
import latus.sync
import latus.logger
import latus.folders


def main(latus_appdata_roaming_folder):

    latus.logger.log.info('cli')

    config = latus.config.Config(latus_appdata_roaming_folder)

    # make sure we have a crypto key before proceeding
    key = config.crypto_get()
    if not key:
        sys.exit('No crypto key found in preferences.  Please use -k to provide or generate one.')

    latus_folder = config.latus_folder_get()
    if not latus_folder:
        sys.exit('No latus folder set - please initialize with the --latus option.')

    cloud_root = config.cloud_root_get()
    if not cloud_root:
        sys.exit('No cloud folder set - please initialize with the --cloud option.')

    node_id = config.node_id_get()
    if not node_id:
        sys.exit('No node id - please initialize with the --id option')

    cloud_folders = latus.folders.CloudFolders(cloud_root)

    sync = latus.sync.Sync(key, latus_folder, cloud_root, node_id, cloud_folders.comm, config.verbose_get())
    sync.start()
    input('Hit enter to exit.')
    sync.request_exit()
