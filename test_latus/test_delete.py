
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
from test_latus.tstutil import logger_init, get_latus_folder, wait_for_file, write_to_file, get_data_root, write_preferences, get_file_name, SyncThread


def get_delete_root():
    return os.path.join(get_data_root(), "delete")


def test_delete(setup):
    """
    test a simple delete across 2 nodes
    """

    nodes = ['a', 'b']

    log_folder = os.path.join(get_delete_root(), 'log')
    logger_init(log_folder)
    latus.logger.set_console_log_level(logging.INFO)

    key = latus.crypto.new_key()
    app_data_folders = [write_preferences(node, get_delete_root(), key) for node in nodes]

    local_folders = []
    file_names = []
    for node in nodes:
        latus_folder = get_latus_folder(get_delete_root(), node)
        file_name = get_file_name(node)
        local_folders.append(latus_folder)
        file_names.append(file_name)

    file_name = nodes[0] + '.txt'
    path_node_0 = write_to_file(get_latus_folder(get_delete_root(), nodes[0]), file_name, nodes[0])
    path_node_1 = os.path.join(get_latus_folder(get_delete_root(), nodes[1]), file_name)

    # start the sync
    syncs = [SyncThread(app_data_folder) for app_data_folder in app_data_folders]
    [sync.start() for sync in syncs]

    # wait for the file to get sync'd
    wait_for_file(path_node_1)
    wait_for_file(path_node_0)

    # now remove the file on the node that it was sync'd to
    os.remove(path_node_1)

    # wait for the file to be removed from both notes
    wait_for_file(path_node_0, False)
    wait_for_file(path_node_1, False)

    # ok .. should be done ... exit
    [sync.request_exit() for sync in syncs]

    # the above might have timed out, so make sure it worked OK
    assert(not os.path.exists(path_node_0))
    assert(not os.path.exists(path_node_1))

    latus.logger.log.info('test_delete exiting')

    return

