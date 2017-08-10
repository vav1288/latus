
import os
import logging
import time
import shutil

import latus.const
import latus.util
import latus.logger
import latus.crypto
import latus.preferences
from test_latus.tstutil import get_latus_folder, get_file_name, wait_for_file, logger_init, get_data_root, write_preferences, write_to_file, SyncProc

test_name = "move_into_latus"


def get_move_into_latus_root():
    return os.path.join(get_data_root(), test_name)


def test_move_into_latus(session_setup, module_setup):

    nodes = ['a', 'b']
    sleep_time = latus.const.FILTER_TIME_OUT * 2

    log_folder = os.path.join(get_move_into_latus_root(), 'log')
    logger_init(log_folder)
    latus.logger.set_console_log_level(logging.INFO)

    # write preferences
    key = latus.crypto.new_key()
    app_data_folders = [write_preferences(node, get_move_into_latus_root(), key) for node in nodes]

    # get list of folders and files, and write to them
    local_folders = []
    for node in nodes:
        latus_folder = get_latus_folder(get_move_into_latus_root(), node)
        os.makedirs(latus_folder, exist_ok=True)
        local_folders.append(latus_folder)
    file_name = 'a.txt'
    src = write_to_file(os.path.join('temp', test_name), file_name, test_name)

    time.sleep(sleep_time)

    # start the sync
    syncs = [SyncProc(app_data_folder, log_folder=log_folder) for app_data_folder in app_data_folders]
    [sync.start() for sync in syncs]

    time.sleep(sleep_time)

    shutil.move(src, os.path.join(local_folders[0], file_name))

    time.sleep(sleep_time)

    # wait for files to sync
    for local_folder in local_folders:
        wait_for_file(os.path.join(local_folder, file_name))

    time.sleep(sleep_time)

    # stop the syncs
    [sync.request_exit() for sync in syncs]

    time.sleep(sleep_time)

    # check the results
    for local_folder in local_folders:
        assert(os.path.exists(os.path.join(local_folder, file_name)))

    latus.logger.log.info('test_move_into_latus exiting')

    return
