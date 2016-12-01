
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
import latus.preferences

LOG_FILE_NAME = 'latus.log'
LOGGER_NAME_BASE = 'latus'

log = None
g_fh = None
g_ch = None
g_dh = None
g_hh = None
g_appdata_folder = None
g_base_log_file_path = None


# unfortunately HTTPHandler can't use a formatter, so inserting the node_id still needs to be done by the log caller
class LatusFormatter(logging.Formatter):
    def format(self, record):
        global g_appdata_folder
        if g_appdata_folder:
            pref = latus.preferences.Preferences(g_appdata_folder)
            node_id = pref.get_node_id()
            return node_id + ' : ' + super().format(record)
        else:
            return super().format(record)

g_formatter = LatusFormatter('%(asctime)s - %(name)s - %(filename)s - %(funcName)s - %(levelname)s - %(message)s')


def init_from_args(args):
    global g_appdata_folder
    g_appdata_folder = None
    if args.appdatafolder:
        g_appdata_folder = args.appdatafolder
    if args.test:
        init(None, backup_count=0, param_appdata_folder=g_appdata_folder)
    else:
        init(None, param_appdata_folder=g_appdata_folder)
    if args.verbose:
        set_console_log_level(logging.WARN)
        set_file_log_level(logging.INFO)
    if args.test:
        set_file_log_level(logging.DEBUG)


def init(log_folder, delete_existing_log_files=False, backup_count=3, param_appdata_folder=None):
    """

    :param log_folder: folder where the log file will be written
    :param delete_existing_log_files: True to remove all log files before writing to them
    :param backup_count: number of files in the rotating backup (0=a single file, which is necessary for testing)
    :param http_handler: True to upload logs to the latus log server (typically error level and higher)
    :param parm_appdata_folder: appdata_folder
    :return: the log folder to be used
    """
    global g_fh, g_ch, g_dh, log, g_base_log_file_path, g_appdata_folder

    if param_appdata_folder:
        g_appdata_folder = param_appdata_folder

    if not log_folder:
        log_folder = appdirs.user_log_dir(latus.const.NAME, latus.const.COMPANY)

    if delete_existing_log_files:
        shutil.rmtree(log_folder, ignore_errors=True)
    os.makedirs(log_folder, exist_ok=True)

    logger_name = LOGGER_NAME_BASE
    log = logging.getLogger(logger_name)
    
    log.setLevel(logging.DEBUG)

    # create file handler
    g_base_log_file_path = os.path.join(log_folder, LOG_FILE_NAME)
    if backup_count > 0:
        max_bytes = 100*1E6  # normal usage
    else:
        max_bytes = 0  # no limit - used during testing
    g_fh = logging.handlers.RotatingFileHandler(g_base_log_file_path, maxBytes=max_bytes, backupCount=backup_count)
    g_fh.setFormatter(g_formatter)
    # see fh.setLevel() below for final level - we set this so we can put the log file path in the log file itself
    g_fh.setLevel(logging.INFO)
    log.addHandler(g_fh)

    # create console handler
    g_ch = logging.StreamHandler()
    g_ch.setFormatter(g_formatter)
    # see ch.setLevel() below for final level - we set this so we can display the log file path on the screen for debug
    g_ch.setLevel(logging.INFO)
    log.addHandler(g_ch)

    # create dialog box handler
    g_dh = DialogBoxHandlerAndExit()
    g_dh.setLevel(logging.FATAL)  # only pop this up as we're on the way out
    log.addHandler(g_dh)

    log.info('log_folder : %s' % os.path.abspath(log_folder))

    # real defaults
    g_fh.setLevel(logging.WARN)
    g_ch.setLevel(logging.ERROR)

    return log_folder


def add_http_handler(base_url='api.abel.co'):
    global g_hh
    log.info('adding http handler')
    g_hh = logging.handlers.HTTPHandler(base_url, 'latus/log', method='POST')
    g_hh.setLevel(logging.ERROR)
    log.addHandler(g_hh)


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
    g_fh.setLevel(new_level)


def set_console_log_level(new_level):
    g_ch.setLevel(new_level)


def get_base_log_file_path():
    return g_base_log_file_path
