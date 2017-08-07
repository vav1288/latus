
import os
import logging
import time

import latus.const
import latus.util
import latus.logger
import latus.crypto
import latus.preferences
from test_latus.tstutil import get_latus_folder, get_file_name, wait_for_file, logger_init, get_data_root, write_preferences, write_to_file, SyncProc


def get_simple_root():
    return os.path.join(get_data_root(), "test_simple")


def test_simple(session_setup, module_setup):
    """
    test a simple sync of 2 files across 2 nodes
    """

    nodes = ['a', 'b']
    sleep_time = 2

    log_folder = os.path.join(get_simple_root(), 'log')
    logger_init(log_folder)
    latus.logger.set_console_log_level(logging.INFO)

    # write preferences
    key = latus.crypto.new_key()
    app_data_folders = [write_preferences(node, get_simple_root(), key) for node in nodes]

    # get list of folders and files, and write to them
    local_folders = []
    file_names = []
    for node in nodes:
        latus_folder = get_latus_folder(get_simple_root(), node)
        file_name = get_file_name(node)
        local_folders.append(latus_folder)
        file_names.append(file_name)
        write_to_file(latus_folder, file_name, node, '')

    time.sleep(sleep_time)

    # start the sync
    syncs = [SyncProc(app_data_folder, log_folder=log_folder) for app_data_folder in app_data_folders]
    [sync.start() for sync in syncs]

    # wait for files to sync
    b_to_a = os.path.join(local_folders[0], file_names[1])
    assert(wait_for_file(b_to_a))
    a_to_b = os.path.join(local_folders[1], file_names[0])
    assert(wait_for_file(a_to_b))

    time.sleep(sleep_time)

    # stop the syncs
    for sync in syncs:
        assert(not sync.request_exit(1))  # make sure we exited cleanly

    time.sleep(sleep_time)

    # final check of the results
    paths = [b_to_a, a_to_b]
    for p in paths:
        assert(os.path.exists(p))

    latus.logger.log.info('test_simple exiting')

    return

