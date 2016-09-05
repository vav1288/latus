
import os
import appdirs
import logging
import logging.handlers

import latus.util
import latus.const

LOG_FILE_NAME = 'latus.log'
LOGGER_NAME_BASE = 'latus'

fh = None
ch = None
log = None
log_folder = None

# the general log message format is:
# < message_type > : [ node id ] , ...
#
# message_type is things like sync, file_write, etc.

def init(log_folder_param=None):
    global fh, ch, log, log_folder
    log_folder = log_folder_param

    if not log_folder:
        log_folder = appdirs.user_log_dir(latus.const.NAME, latus.const.COMPANY)

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


def get_log_folder():
    return log_folder


def set_file_log_level(new_level):
    fh.setLevel(new_level)


def set_console_log_level(new_level):
    ch.setLevel(new_level)


# the sync log functions

def sync_log(node_id, file_system_event, miv, file_path, detection_source, size, local_hash, mtime):
    log.info('sync : %s , %s , %s , "%s" , %s , %s , %s , %s' %
             (node_id, str(file_system_event), str(miv), file_path, detection_source, size, local_hash, mtime))


def sync_filtered_log(node_id, file_path):
    log.info('sync : %s , filtered, %s' % (node_id, file_path))