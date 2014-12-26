
import logging
import latus.logger


def print_all_levels(msg):
    latus.logger.log.error('error test_latus message %s', msg)
    latus.logger.log.warning('warning test_latus message %s', msg)
    latus.logger.log.info('info test_latus message %s', msg)
    latus.logger.log.debug('debug test_latus message %s', msg)


def test_logger():
    latus.logger.init()

    print()
    print_all_levels("default level")

    latus.logger.set_console_log_level(logging.DEBUG)
    print()
    print_all_levels("debug level")

if __name__ == '__main__':
    test_logger()