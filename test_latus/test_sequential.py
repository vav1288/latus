
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
from test_latus.tstutil import get_latus_folder, get_file_name, wait_for_file, logger_init, get_data_root, write_preferences, write_to_file, SyncProc, clean


def get_sequential_root():
    return os.path.join(get_data_root(), "test_sequential")


def test_sequential_start_first(setup):
    do_sequential(True)


def test_sequential_do_not_start_first(setup):
    do_sequential(False)


def do_sequential(start_first):
    """
    test that we can bring up nodes sequentially and they do the right thing (e.g. when a 2nd node comes up
    it doesn't signal a file delete just because it doesn't have the file to start with).
    """

    nodes = ['a', 'b']

    # so we can run this multiple times
    clean(get_sequential_root())

    log_folder = os.path.join(get_sequential_root(), 'log')
    logger_init(log_folder)
    latus.logger.set_console_log_level(logging.INFO)

    # write preferences
    key = latus.crypto.new_key()
    app_data_folders = [write_preferences(node, get_sequential_root(), key) for node in nodes]

    latus_folders = []
    latus_file = get_file_name(nodes[0])  # only one file for this test
    latus_paths = []
    for node in nodes:
        folder = get_latus_folder(get_sequential_root(), node)
        latus_folders.append(folder)
        path = os.path.join(folder, latus_file)
        latus_paths.append(path)

    if start_first:
        syncs = [SyncProc(app_data_folder) for app_data_folder in app_data_folders]
        [sync.start() for sync in syncs]
        time.sleep(3)
        [sync.request_exit() for sync in syncs]
        time.sleep(3)

    write_to_file(latus_folders[0], latus_file, nodes[0], '')

    syncs = [SyncProc(app_data_folder) for app_data_folder in app_data_folders]
    syncs[0].start()  # just start 'a'

    # check we have the proper files
    assert(os.path.exists(latus_paths[0]))
    assert(not os.path.exists(latus_paths[1]))

    syncs[1].start()  # start 'b'

    wait_for_file(latus_paths[1])

    # stop the syncs
    [sync.request_exit() for sync in syncs]

    # check the results
    assert(os.path.exists(latus_paths[0]))
    assert(os.path.exists(latus_paths[1]))

    latus.logger.log.info('test_simple exiting')

    return

