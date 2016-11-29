
import os
import sys
import appdirs
import logging
import logging.handlers
import subprocess
import shutil

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
base_log_file_path = None


def init_from_args(args):
    if args.test:
        init(args.appdatafolder, backup_count=0)
    else:
        init(args.appdatafolder)
    if args.verbose:
        set_console_log_level(logging.WARN)
        set_file_log_level(logging.INFO)


def init(log_folder, delete_existing_log_files=False, backup_count=3):
    """

    :param log_folder: folder where the log file will be written
    :param delete_existing_log_files: True to remove all log files before writing to them
    :param backup_count: number of files in the rotating backup (0=a single file, which is necessary for testing)
    :return: the log folder to be used
    """
    global fh, ch, dh, log, base_log_file_path

    if not log_folder:
        log_folder = appdirs.user_log_dir(latus.const.NAME, latus.const.COMPANY)

    if delete_existing_log_files:
        shutil.rmtree(log_folder, ignore_errors=True)
    os.makedirs(log_folder, exist_ok=True)

    logger_name = LOGGER_NAME_BASE
    log = logging.getLogger(logger_name)
    
    log.setLevel(logging.DEBUG)

    # create file handler
    base_log_file_path = os.path.join(log_folder, LOG_FILE_NAME)
    if backup_count > 0:
        max_bytes = 100*1E6  # normal usage
    else:
        max_bytes = 0  # no limit - used during testing
    fh = logging.handlers.RotatingFileHandler(base_log_file_path, maxBytes=max_bytes, backupCount=backup_count)
    # see fh.setLevel() below for final level - we set this so we can put the log file path in the log file itself
    fh.setLevel(logging.INFO)

    # create console handler
    ch = logging.StreamHandler()
    # see ch.setLevel() below for final level - we set this so we can display the log file path on the screen for debug
    ch.setLevel(logging.INFO)

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

    log.info('log_folder : %s' % os.path.abspath(log_folder))

    # real defaults
    fh.setLevel(logging.WARN)
    ch.setLevel(logging.ERROR)

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


def get_base_log_file_path():
    return base_log_file_path
