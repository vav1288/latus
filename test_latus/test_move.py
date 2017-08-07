
import os
import logging
import shutil
import time

import latus.const
import latus.util
import latus.logger
import latus.crypto
import latus.preferences
from test_latus.tstutil import logger_init, get_latus_folder, wait_for_file, write_to_file, get_data_root, write_preferences, get_file_name, SyncProc


def get_move_root():
    return os.path.join(get_data_root(), "test_move")


def test_move(session_setup, module_setup):
    """
    test a move across 2 nodes
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

    time.sleep(latus.const.FILTER_TIME_OUT * 2)

    # start the sync
    syncs = [SyncProc(app_data_folder, log_folder=log_folder) for app_data_folder in app_data_folders]
    [sync.start() for sync in syncs]

    time.sleep(latus.const.FILTER_TIME_OUT * 2)

    # wait for the file to get sync'd
    wait_for_file(path_node_1, message_prefix='stage 1')
    wait_for_file(path_node_0, message_prefix='stage 2')

    time.sleep(latus.const.FILTER_TIME_OUT * 2)  # wait for filters to timeout

    # move to a new file name
    new_file_name = 'dest.txt'
    new_path_node_0 = os.path.join(get_latus_folder(get_move_root(), nodes[0]), new_file_name)
    new_path_node_1 = os.path.join(get_latus_folder(get_move_root(), nodes[1]), new_file_name)

    latus.logger.log.info('moving %s to %s' % (path_node_0, new_path_node_0))
    os.makedirs(os.path.dirname(new_path_node_0), exist_ok=True)
    time.sleep(1)  # sometimes the makedirs doesn't actually get done!
    shutil.move(path_node_0, new_path_node_0)

    time.sleep(latus.const.FILTER_TIME_OUT * 2)

    # wait for the file to be moved on both notes
    wait_for_file(path_node_0, False, message_prefix='stage 3')
    wait_for_file(path_node_1, False, message_prefix='stage 4')
    wait_for_file(new_path_node_0, message_prefix='stage 5')
    wait_for_file(new_path_node_1, message_prefix='stage 6')

    # ok .. should be done ... exit
    [sync.request_exit() for sync in syncs]

    time.sleep(latus.const.FILTER_TIME_OUT * 2)

    # make sure it worked OK
    assert(not os.path.exists(path_node_0))
    assert(not os.path.exists(path_node_1))
    assert(os.path.exists(new_path_node_0))
    assert(os.path.exists(new_path_node_1))

    latus.logger.log.info('test_move exiting')

    return

