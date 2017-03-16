
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


def get_create_modify_delete_root():
    return os.path.join(get_data_root(), "test_create_modify_delete")


def test_create_modify_delete(setup):
    """
    test that we can bring up nodes sequentially and they do the right thing (e.g. when a 2nd node comes up
    it doesn't signal a file delete just because it doesn't have the file to start with).
    """

    nodes = ['a', 'b']

    log_folder = os.path.join(get_create_modify_delete_root(), 'log')
    logger_init(log_folder)
    latus.logger.set_console_log_level(logging.INFO)

    # write preferences
    key = latus.crypto.new_key()
    app_data_folders = [write_preferences(node, get_create_modify_delete_root(), key) for node in nodes]

    latus_folders = []
    latus_file = get_file_name(nodes[0])  # only one file for this test
    latus_paths = []
    for node in nodes:
        folder = get_latus_folder(get_create_modify_delete_root(), node)
        latus_folders.append(folder)
        latus_paths.append(os.path.join(folder, latus_file))

    syncs = [SyncProc(app_data_folder) for app_data_folder in app_data_folders]
    [sync.start() for sync in syncs]

    time.sleep(1)

    write_to_file(latus_folders[0], latus_file, 'abc')

    [wait_for_file(p) for p in latus_paths]

    # check we have the proper files
    time.sleep(1)
    assert(os.path.exists(latus_paths[0]))
    assert(os.path.exists(latus_paths[1]))

    # append so it's a modify
    write_to_file(latus_folders[0], latus_file, 'def', mode='a')

    # wait for append to propagate
    while os.path.getsize(os.path.join(latus_folders[1], latus_file)) != 6:
        time.sleep(1)

    assert(os.path.getsize(os.path.join(latus_folders[1], latus_file)) == 6)

    os.remove(latus_paths[0])

    # wait for delete to propagate
    [wait_for_file(p, False) for p in latus_paths]

    # stop the syncs
    [sync.request_exit() for sync in syncs]

    # check the results
    assert(not os.path.exists(latus_paths[0]))
    assert(not os.path.exists(latus_paths[1]))

    latus.logger.log.info('test_create_modify_delete exiting')

    return

