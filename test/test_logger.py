
import logging
from core import logger


def print_all_levels(log, msg = ""):
    log.error('"error test_latus message %s"', msg)
    log.warning('"warning test_latus message %s"', msg)
    log.info('"info test_latus message %s"', msg)
    log.debug('"debug test_latus message %s"', msg)

def test_logger():
    log = logger.log

    print_all_levels(log, "default level")

    logger.set_log_level(logging.DEBUG)
    print_all_levels(log, "debug level")

    logger.set_log_level()
    print_all_levels(log, "back to default level")

if __name__ == '__main__':
    test_logger()