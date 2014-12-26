
import latus.const
import latus.config
import latus.crypto
import latus.util
import latus.sync
import latus.logger


def main(latus_appdata_folder):

    config = latus.config.Config(latus_appdata_folder)
    key = config.crypto_get()
    latus_folder = config.latus_folder_get()
    cloud_root = config.cloud_root_get()
    verbose = config.verbose_get()

    latus.logger.log.info('cli mode')

    if not cloud_root:
        exit('No cloud folder set - please initialize with the --cloud option.')

    if not latus_folder:
        exit('No latus folder set - please initialize with the --latus option.')

    sync = latus.sync.Sync(key, latus_folder, cloud_root, verbose)
    sync.start()
    input('Hit enter to exit.')
    sync.request_exit()