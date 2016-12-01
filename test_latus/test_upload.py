
import os
import logging

from test_latus.tstutil import get_data_root, write_preferences, logger_init
import latus.logger


def get_test_upload_root():
    return os.path.join(get_data_root(), "test_upload")


def test_log_upload():
    logger_init(os.path.join(get_data_root(), 'log'))
    app_data_folder = write_preferences('testnode', get_test_upload_root(), 'test_key')
    latus.logger.set_appdata_folder(app_data_folder)
    latus.logger.set_console_log_level(logging.INFO)
    latus.logger.log.error('test_upload_error_message')
