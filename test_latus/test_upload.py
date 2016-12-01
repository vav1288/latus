
import os
import logging

from test_latus.tstutil import get_data_root
import latus.logger


def get_test_upload_root():
    return os.path.join(get_data_root(), "test_upload")


def test_log_upload():
    latus.logger.init(os.path.join(get_test_upload_root(), 'log'))
    latus.logger.set_console_log_level(logging.INFO)
    if True:
        # local testing
        url = 'localhost:5000'
        latus.logger.add_http_handler(url)
        latus.logger.log.info('adding handler : %s' % url)
    else:
        latus.logger.add_http_handler()
    latus.logger.log.error('test_upload_error_message')
