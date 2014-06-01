import sys
import pprint

from latus import logger
from repo_ignore.old import settings


if __name__ == '__main__':

    logger.setup()
    logger.set_log_level('info')

    if len(sys.argv) > 1:
        my_settings = settings.Settings(sys.argv[1])
    else:
        my_settings = settings.Settings()
    print(my_settings.get_settings_file_path())
    pprint.pprint(my_settings.get_all())


