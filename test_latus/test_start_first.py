
import os
import logging
import time

import latus.const
import latus.sync
import latus.util
import latus.logger
import latus.folders
import latus.crypto
import latus.preferences
from test_latus.tstutil import get_latus_folder, get_file_name, wait_for_file, logger_init, get_data_root, write_preferences, write_to_file, SyncProc


def get_start_first_root():
    return os.path.join(get_data_root(), "start_first")


def test_start_first(setup):
    """
    test a simple sync of 2 files across 2 nodes
    """

    nodes = ['a', 'b']

    log_folder = os.path.join(get_start_first_root(), 'log')
    logger_init(log_folder)
    latus.logger.set_console_log_level(logging.INFO)

    # write preferences
    key = latus.crypto.new_key()
    app_data_folders = [write_preferences(node, get_start_first_root(), key) for node in nodes]

    # start the sync BEFORE we have any files
    syncs = [SyncProc(app_data_folder) for app_data_folder in app_data_folders]
    [sync.start() for sync in syncs]

    time.sleep(2)

    # get list of folders and files, and write to them
    local_folders = []
    file_names = []
    for node in nodes:
        latus_folder = get_latus_folder(get_start_first_root(), node)
        file_name = get_file_name(node)
        local_folders.append(latus_folder)
        file_names.append(file_name)
        write_to_file(latus_folder, file_name, node, '')

    # wait for files to sync
    b_to_a = os.path.join(local_folders[0], file_names[1])
    wait_for_file(b_to_a)
    a_to_b = os.path.join(local_folders[1], file_names[0])
    wait_for_file(a_to_b)

    # stop the syncs
    [sync.request_exit() for sync in syncs]

    # check the results
    assert(os.path.exists(b_to_a))
    assert(os.path.exists(a_to_b))

    latus.logger.log.info('test_start_first exiting')

    return