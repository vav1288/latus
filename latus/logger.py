
import os
import logging
import logging.handlers

import latus.util

LOG_FILE_NAME = 'latus.log'
LOGGER_NAME_BASE = 'latus'

fh = None
ch = None
log = None


def init(log_folder = None):
    global fh, ch, log

    if not log_folder:
        log_folder = latus.util.get_latus_log_folder()

    latus.util.make_dirs(log_folder)

    logger_name = LOGGER_NAME_BASE
    log = logging.getLogger(logger_name)
    
    log.setLevel(logging.DEBUG)

    # todo: put these logs in the program data area

    # create file handler
    fh = logging.handlers.RotatingFileHandler(os.path.join(log_folder, LOG_FILE_NAME),
                                              maxBytes=20*1E6, backupCount=3)
    #fh = logging.FileHandler(LOG_FILE_NAME)
    fh.setLevel(logging.INFO)

    # create console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)

    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(filename)s - %(funcName)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # add the handlers to the logger
    log.addHandler(fh)
    log.addHandler(ch)

    return log_folder


def set_file_log_level(new_level):
    fh.setLevel(new_level)


def set_console_log_level(new_level):
    ch.setLevel(new_level)