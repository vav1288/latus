
import os
import logging
import time

import latus.logger
import latus.crypto
import latus.preferences
from test_latus.tstutil import get_latus_folder, get_file_name, wait_for_file, logger_init, get_data_root, write_preferences, write_to_file, SyncProc


def get_subdir_root():
    return os.path.join(get_data_root(), "subdir")


def test_subdir(session_setup, module_setup):
    """
    test a subdir sync of 2 files across 2 nodes
    """

    nodes = ['a', 'b']
    subdir_name = 'mysubdir'

    log_folder = os.path.join(get_subdir_root(), 'log')
    logger_init(log_folder)
    latus.logger.set_console_log_level(logging.INFO)

    key = latus.crypto.new_key()
    app_data_folders = [write_preferences(node, get_subdir_root(), key) for node in nodes]

    local_folders = []
    file_names = []
    for node in nodes:
        latus_folder = get_latus_folder(get_subdir_root(), node)
        file_name = get_file_name(node)
        local_folders.append(latus_folder)
        file_names.append(file_name)
        write_to_file(latus_folder, file_name, node, subdir_name)

    time.sleep(2)

    # start the sync
    syncs = [SyncProc(app_data_folder, log_folder=log_folder) for app_data_folder in app_data_folders]
    [sync.start() for sync in syncs]

    b_to_a = os.path.join(local_folders[0], subdir_name, file_names[1])
    wait_for_file(b_to_a)

    time.sleep(2)

    a_to_b = os.path.join(local_folders[1], subdir_name, file_names[0])
    wait_for_file(a_to_b)

    time.sleep(2)

    [sync.request_exit() for sync in syncs]

    assert(os.path.exists(b_to_a))
    assert(os.path.exists(a_to_b))

    latus.logger.log.info('test_subdir exiting')

    return

