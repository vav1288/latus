
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


def get_move_out_of_latus_root():
    return os.path.join(get_data_root(), "move_out_of_latus")


def test_move_out_of_latus_root(setup):

    nodes = ['a', 'b']

    log_folder = os.path.join(get_move_out_of_latus_root(), 'log')
    logger_init(log_folder)
    latus.logger.set_console_log_level(logging.INFO)

    # write preferences
    key = latus.crypto.new_key()
    app_data_folders = [write_preferences(node, get_move_out_of_latus_root(), key) for node in nodes]

    # get list of folders and files, and write to them
    local_folders = []
    for node in nodes:
        latus_folder = get_latus_folder(get_move_out_of_latus_root(), node)
        local_folders.append(latus_folder)

    file_name = 'a.txt'
    write_to_file(local_folders[0], file_name, 'move_out_of_latus', '')

    # start the sync
    syncs = [SyncProc(app_data_folder) for app_data_folder in app_data_folders]
    [sync.start() for sync in syncs]

    time.sleep(5)  # todo: something more sophisticated

    temp_folder = os.path.join('temp', 'move_out_of_latus')
    os.makedirs(temp_folder, mode=latus.const.MAKE_DIRS_MODE, exist_ok=True)
    temp_path = os.path.join(temp_folder, file_name)
    # make sure there's not already something in the dest (e.g. from another test)
    try:
        os.remove(temp_path)
    except FileNotFoundError:
        pass
    shutil.move(os.path.join(local_folders[0], file_name), temp_path)

    time.sleep(5)

    # wait for files to sync
    for local_folder in local_folders:
        wait_for_file(os.path.join(local_folder, file_name), False)

    # stop the syncs
    [sync.request_exit() for sync in syncs]

    time.sleep(2)

    # check the results
    for local_folder in local_folders:
        assert(not os.path.exists(os.path.join(local_folder, file_name)))

    latus.logger.log.info('test_move_out_of_latus_root exiting')

    return