
import os

import logging
import latus.logger
import test_latus.tstutil


def get_logger_root():
    return os.path.join(test_latus.tstutil.get_data_root(), "logger")


def print_all_levels(msg):
    latus.logger.log.error('error test_latus message %s' % msg)
    latus.logger.log.warning('warning test_latus message %s' % msg)
    latus.logger.log.info('info test_latus message %s' % msg)
    latus.logger.log.debug('debug test_latus message %s' % msg)


def test_logger(setup):

    latus.logger.init(get_logger_root())

    print()
    print_all_levels("default level")

    latus.logger.set_console_log_level(logging.DEBUG)
    print()
    print_all_levels("debug level")

