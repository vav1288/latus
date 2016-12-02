
import os
import logging
import shutil

import latus.const
import latus.sync
import latus.util
import latus.logger
import latus.folders
import latus.crypto
import latus.preferences
from test_latus.tstutil import logger_init, get_latus_folder, wait_for_file, write_to_file, get_data_root, write_preferences, get_file_name, SyncProc


def get_move_root():
    return os.path.join(get_data_root(), "test_move")


def test_move(setup):
    """
    test a simple delete across 2 nodes
    """

    nodes = ['a', 'b']

    log_folder = os.path.join(get_move_root(), 'log')
    logger_init(log_folder)
    latus.logger.set_console_log_level(logging.INFO)

    key = latus.crypto.new_key()
    app_data_folders = [write_preferences(node, get_move_root(), key) for node in nodes]

    local_folders = []
    file_names = []
    for node in nodes:
        latus_folder = get_latus_folder(get_move_root(), node)
        file_name = get_file_name(node)
        local_folders.append(latus_folder)
        file_names.append(file_name)

    file_name = 'src.txt'
    path_node_0 = write_to_file(get_latus_folder(get_move_root(), nodes[0]), file_name, nodes[0])
    path_node_1 = os.path.join(get_latus_folder(get_move_root(), nodes[1]), file_name)

    # start the sync
    syncs = [SyncProc(app_data_folder) for app_data_folder in app_data_folders]
    [sync.start() for sync in syncs]

    # wait for the file to get sync'd
    wait_for_file(path_node_1)
    wait_for_file(path_node_0)

    # move to a new file name
    new_file_name = 'dest.txt'
    new_path_node_0 = os.path.join(get_latus_folder(get_move_root(), nodes[0]), new_file_name)
    new_path_node_1 = os.path.join(get_latus_folder(get_move_root(), nodes[1]), new_file_name)

    latus.logger.log.info('moving %s to %s' % (path_node_0, new_path_node_0))
    shutil.move(path_node_0, new_path_node_0)

    # wait for the file to be moved on both notes
    wait_for_file(path_node_0, False)
    wait_for_file(path_node_1, False)
    wait_for_file(new_path_node_0)
    wait_for_file(new_path_node_1)

    # ok .. should be done ... exit
    [sync.request_exit() for sync in syncs]

    # make sure it worked OK
    assert(not os.path.exists(path_node_0))
    assert(not os.path.exists(path_node_1))
    assert(os.path.exists(new_path_node_0))
    assert(os.path.exists(new_path_node_1))

    latus.logger.log.info('test_move exiting')

    return

