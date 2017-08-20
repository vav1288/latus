
import os
import sys
import appdirs
import logging
import logging.handlers
import subprocess
import shutil
import copy
import time

import requests

import raven
from raven.handlers.logging import SentryHandler

import keys.sentry
import latus
import latus.util
import latus.messagedialog
import latus.preferences

LOGGER_NAME_BASE = 'latus'
LOG_FILE_NAME = LOGGER_NAME_BASE + '.log'

log = None  # code that uses this module uses this logger

g_fh = None  # file handler
g_ch = None  # console handler
g_dh = None  # dialog handler
g_hh = None  # HTTP (log server) handler
g_sh = None  # Sentry handler
g_appdata_folder = None
g_base_log_file_path = None  # 'base' since the file rotator can create files based on this file name
g_sentry_client = None
g_start_time = None


class LatusFormatter(logging.Formatter):
    def format(self, record):
        """
        adds in the node_id, if available
        """
        global g_appdata_folder, g_start_time
        s = '{:12.6f}'.format(time.time() - g_start_time) + ' : ' + super().format(record)
        if latus.preferences.preferences_db_exists(g_appdata_folder):
            pref = latus.preferences.Preferences(g_appdata_folder)
            node_id = pref.get_node_id()
            if node_id:
                s = node_id + ' : ' + s
            else:
                s = '    ' + s  # lines up if node_id is 1 char
        else:
            s = '.   ' + s  # lines up if node_id is 1 char
        return s

g_formatter = LatusFormatter('%(asctime)s - %(name)s - %(filename)s - %(lineno)s - %(funcName)s - %(levelname)s - %(message)s')


class DialogBoxHandlerAndExit(logging.Handler):
    def emit(self, record):
        msg = self.format(record)
        args = [sys.executable, '-c', latus.messagedialog.program, msg]
        print(str(args))
        subprocess.check_call(args)


class LatusHttpHandler(logging.Handler):
    """
    send the log up to the log server
    """
    def __init__(self, latus_logging_url):
        self.latus_logging_url = latus_logging_url
        super().__init__()

    def emit(self, record):
        try:
            info = copy.deepcopy(record.__dict__)
        except TypeError:
            info = None
        if info:
            try:
                # record.__dict__ is essentially what HTTPHandler uses
                # (doesn't use the string formatter)
                if latus.preferences.preferences_db_exists(g_appdata_folder):
                    pref = latus.preferences.Preferences(g_appdata_folder)
                    info['nodeid'] = pref.get_node_id()
                requests.post(self.latus_logging_url, data=info)
            except requests.ConnectionError:
                # drop the log on the floor if we have connection problems (it's still in the log file)
                pass


def init_from_args(args):
    if args.appdatafolder:
        set_appdata_folder(args.appdatafolder)
    if args.test:
        init(log_folder = args.logfolder, backup_count=0)
    else:
        init(log_folder = args.logfolder)
    if args.verbose:
        set_console_log_level(logging.INFO)
        set_file_log_level(logging.DEBUG)
    if args.test:
        set_console_log_level(logging.INFO)
        set_file_log_level(logging.DEBUG)


def init(log_folder=None, delete_existing_log_files=False, backup_count=3, node_id=None, use_latus_server=True,
         use_sentry=True):
    """

    :param log_folder: folder where the log file will be written (None to take the default)
    :param delete_existing_log_files: True to remove all log files before writing to them
    :param backup_count: number of files in the rotating backup (0=a single file, which is necessary for testing)
    :param http_handler: True to upload logs to the latus log server (typically error level and higher)
    :param appdata_folder: appdata_folder
    :param node_id: node_id
    :return: the log folder to be used
    """
    global g_fh, g_ch, g_dh, log, g_base_log_file_path, g_appdata_folder, g_start_time

    g_start_time = time.time()

    if not log_folder:
        log_folder = appdirs.user_log_dir(latus.__application_name__, latus.__author__)

    logger_name = LOGGER_NAME_BASE
    log = logging.getLogger(logger_name)

    if use_sentry:
        add_sentry_handler(node_id)
    
    log.setLevel(logging.DEBUG)

    # create file handler
    if delete_existing_log_files:
        shutil.rmtree(log_folder, ignore_errors=True)
    os.makedirs(log_folder, exist_ok=True)
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

    if False:
        # create dialog box handler
        g_dh = DialogBoxHandlerAndExit()
        g_dh.setLevel(logging.FATAL)  # only pop this up as we're on the way out
        log.addHandler(g_dh)

    if use_latus_server:
        add_http_handler()

    log.info('log_folder : %s' % os.path.abspath(log_folder))
    if g_appdata_folder:
        log.info('preferences : %s' % latus.preferences.Preferences(g_appdata_folder).get_db_path())

    # real defaults
    set_file_log_level(logging.INFO)
    set_console_log_level(logging.WARN)

    return log_folder


def add_http_handler():
    global g_hh
    url = 'http://api.abel.co/latus/log'
    log.info('adding http handler %s' % url)
    g_hh = LatusHttpHandler(url)
    g_hh.setLevel(logging.ERROR)
    log.addHandler(g_hh)


def add_sentry_handler(node_id):
    global g_sh
    global g_sentry_client

    g_sh = SentryHandler()
    log.addHandler(g_sh)

    g_sentry_client = raven.Client(dsn=keys.sentry.DSN, include_paths=[__name__.split('.', 1)[0]],
                                   release=latus.__version__)

    if node_id:
        # use the node_id as the username in Sentry
        g_sentry_client.context.merge({'user': {'username': node_id}})


def set_verbose():
    set_file_log_level(logging.DEBUG)
    set_console_log_level(logging.INFO)


def set_file_log_level(new_level):
    if g_fh:
        # log the new level twice so we will likely see one of them, regardless if it's going up or down
        log.info('setting file logging to %s' % logging.getLevelName(new_level))
        g_fh.setLevel(new_level)
        log.info('setting file logging to %s' % logging.getLevelName(new_level))


def set_console_log_level(new_level):
    if g_ch:
        # log the new level twice so we will likely see one of them, regardless if it's going up or down
        log.info('setting console logging to %s' % logging.getLevelName(new_level))
        g_ch.setLevel(new_level)
        log.info('setting console logging to %s' % logging.getLevelName(new_level))


def set_appdata_folder(appdata_folder):
    global g_appdata_folder
    g_appdata_folder = appdata_folder


def get_base_log_file_path():
    global g_base_log_file_path
    return g_base_log_file_path

