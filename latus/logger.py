
import sys
import logging
import logging.handlers
from . import const

""" General logging capability.

Good rules of thumb on using logging levels:
http://en.wikipedia.org/wiki/Log4j
"""

# Only one call should be made to this per program invocation (or else you'll get repeated lines in the log)
#
# We default stream_out to sys.stdout so the "nose" testing framework can consume the output, but
# in normal operation logs still get sent to the console.  If this over-use of stdout is not the desired
# behavior, users of these functions can set it 'back' to None so it'll use the default StreamHandler stream,
# which is currently sys.stderr.
#

# don't call logging.<level>(msg) directly - use logger.get_log().<level>(msg) instead
def get_log():
    return logging.getLogger(const.NAME)

def setup(log_file_path = const.LOG_FILE, max_bytes = 1000000, stream_out = sys.stdout):
    # note that (message) is not pre-quoted, in case there are multiple fields
    console_format_string = '%(message)s'
    file_format_string = '"%(asctime)s","%(name)s","%(levelname)s","module","%(module)s","line","%(lineno)d",%(message)s'
    handlers = {}

    log = get_log()

    log.setLevel(logging.INFO)

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

    return handlers

def remove_handlers(handlers):
    for handler in handlers:
        get_log().removeHandler(handler)

def set_log_level(choice):
    choice = choice[0].lower()
    level = logging.WARNING
    if choice[0] == 'd':
        level = logging.DEBUG
    elif choice[0] == 'i':
        level = logging.INFO
    elif choice[0] == 'w':
        level = logging.WARNING
    elif choice[0] == 'e':
        level = logging.ERROR
    elif choice[0] == 'f':
        level = logging.FATAL
    get_log().setLevel(level)
    get_log().info('"level","%s"', level_to_str(level))
    return level

def level_to_str(level):
    s = { logging.DEBUG : 'DEBUG',
          logging.INFO : 'INFO',
          logging.WARNING : 'WARNING',
          logging.ERROR : 'ERROR',
          logging.FATAL : 'FATAL'
    }
    return s[level]
