import sys
import logging
import logging.handlers

from latus import const


"""
Logging capability.

Good rules of thumb on using logging levels:
http://en.wikipedia.org/wiki/Log4j
"""

handlers = {}
log = logging.getLogger(const.NAME)

def remove_handlers(handlers):
    for handler in handlers:
        log.removeHandler(handler)

def set_log_level(level = logging.WARNING):
    """
    level is from logging module.  e.g. logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, etc.
    """
    log.setLevel(level)
    log.info('"level","%s"', level_to_str(level))
    return level

def level_to_str(level):
    s = { logging.DEBUG : 'DEBUG',
          logging.INFO : 'INFO',
          logging.WARNING : 'WARNING',
          logging.ERROR : 'ERROR',
          logging.FATAL : 'FATAL'
    }
    return s[level]

"""
setup log stuff
"""

log_file_path = const.LOG_FILE
max_bytes = 1000000
stream_out = sys.stdout # vs. sys.stderr

# note that (message) is not pre-quoted, in case there are multiple fields
console_format_string = '%(message)s'
file_format_string = '"%(asctime)s","%(name)s","%(levelname)s","module","%(module)s","line","%(lineno)d","%(message)s"'

log.setLevel(logging.WARNING)

# create console handler
console_handler = logging.StreamHandler(stream_out)
console_formatter = logging.Formatter(console_format_string)
console_handler.setFormatter(console_formatter)
console_handler.setLevel(logging.WARN)
log.addHandler(console_handler)
handlers['console'] = console_handler

# create file handler
file_handler = logging.handlers.RotatingFileHandler(log_file_path, maxBytes=max_bytes)
file_formatter = logging.Formatter(file_format_string)
file_handler.setFormatter(file_formatter)
log.addHandler(file_handler)
handlers['file'] = file_handler