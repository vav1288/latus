
import os
import logging
import time
import shutil

import latus.const
import latus.sync
import latus.util
import latus.logger
import latus.folders
import latus.crypto
import latus.preferences
from test_latus.tstutil import get_latus_folder, get_file_name, wait_for_file, logger_init, get_data_root, write_preferences, write_to_file, SyncProc


def get_move_into_latus_root():
    return os.path.join(get_data_root(), "move_into_latus")


def test_move_into_latus_root(setup):

    nodes = ['a', 'b']

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
        local_folders.append(latus_folder)

    temp_folder = os.path.join('temp', 'move_to_latus')
    file_name = 'a.txt'
    write_to_file(temp_folder, file_name, 'move_to_latus', '')

    # start the sync
    syncs = [SyncProc(app_data_folder) for app_data_folder in app_data_folders]
    [sync.start() for sync in syncs]

    time.sleep(3)  # todo: something more sophisticated

    shutil.move(os.path.join(temp_folder, file_name), os.path.join(local_folders[0], file_name))

    # wait for files to sync
    for local_folder in local_folders:
        wait_for_file(os.path.join(local_folder, file_name))

    # stop the syncs
    [sync.request_exit() for sync in syncs]

    # check the results
    for local_folder in local_folders:
        assert(os.path.exists(os.path.join(local_folder, file_name)))

    latus.logger.log.info('test_move_into_latus_root exiting')

    return