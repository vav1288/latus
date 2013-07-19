
import logging
from latus import settings, logger

if __name__ == '__main__':

    logger.setup()
    logger.set_log_level('info')

    my_settings = settings.Settings()
    print(my_settings.settings_file_path)
    print(my_settings.get('folder', 'cloud'))
    print(my_settings.get_all())
    my_settings.get('badsection', 'badkey')
    my_settings.set('folder', 'cloud', 'dropbox')
    my_settings.set('folder', 'local', 'latus')
    print(my_settings.get_all())
    print(my_settings.get('folder', 'cloud'))