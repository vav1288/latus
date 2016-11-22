
import os
import sys
import appdirs
import logging
import logging.handlers
import subprocess

import latus.util
import latus.const
import latus.gui
import latus.messagedialog

LOG_FILE_NAME = 'latus.log'
LOGGER_NAME_BASE = 'latus'

fh = None
ch = None
dh = None
log = None

# the general log message format is:
# < message_type > : [ node id ] , ...
#
# message_type is things like sync, file_write, etc.


def init(log_folder=None):
    global fh, ch, dh, log

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
    fh.setLevel(logging.INFO)

    # create console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)

    # create dialog box handler
    dh = DialogBoxHandlerAndExit()
    dh.setLevel(logging.FATAL)  # only pop this up as we're on the way out

    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(filename)s - %(funcName)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # add the handlers to the logger
    log.addHandler(fh)
    log.addHandler(ch)
    log.addHandler(dh)

    log.info('log_folder : %s' % log_folder)

    return log_folder


class DialogBoxHandlerAndExit(logging.Handler):
    def emit(self, record):
        msg = self.format(record)
        cmd = '%s -c "%s" "%s"' % (sys.executable,  latus.messagedialog.program, msg)
        try:
            subprocess.call(cmd, shell=True)
            sys.exit(msg)
        except OSError:
            # If the Python executable isn't actually accessible we should get this exception.
            # We don't have the exit() here since we don't want to merely exit silently.
            print(msg)  # at least try to communicate this message


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