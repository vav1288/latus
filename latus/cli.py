
import latus.const
import latus.config
import latus.crypto
import latus.util
import latus.sync
import latus.logger


def main(latus_appdata_folder):

    latus.logger.log.info('cli')

    config = latus.config.Config(latus_appdata_folder)

    # make sure we have a crypto key before proceeding
    key = config.crypto_get()
    if not key:
        exit('No crypto key found in preferences.  Please use -k to provide or generate one.')

    latus_folder = config.latus_folder_get()
    cloud_root = config.cloud_root_get()
    verbose = config.verbose_get()

    if not cloud_root:
        exit('No cloud folder set - please initialize with the --cloud option.')

    if not latus_folder:
        exit('No latus folder set - please initialize with the --latus option.')

    sync = latus.sync.Sync(key, latus_folder, cloud_root, verbose)
    sync.start()
    input('Hit enter to exit.')
    sync.request_exit()