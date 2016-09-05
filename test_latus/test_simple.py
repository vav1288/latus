
import os
import multiprocessing
import time

import latus.const
import latus.sync
import latus.util
import latus.logger
import latus.folders
import latus.crypto
import latus.preferences
from test_latus.util import logger_init, get_latus_folder, wait_for_file, get_file_name, sync_node, \
    get_data_root


def get_simple_root():
    return os.path.join(get_data_root(), "simple")


def test_simple(setup):
    """
    test a simple sync of 2 files across 2 nodes
    """

    nodes = ['a', 'b']

    log_folder = os.path.join(get_simple_root(), 'log')
    logger_init(log_folder)

    key = latus.crypto.new_key()

    syncs = {}
    exit_event = multiprocessing.Event()

    cloud = os.path.join(get_simple_root(), 'cloud')

    local_folders = []
    file_names = []
    for node in nodes:
        local_folders.append(get_latus_folder(get_simple_root(), node))
        file_names.append(get_file_name(node))

    for node in nodes:
        syncs[node] = multiprocessing.Process(target=sync_node,
                                              args=(node, key, get_simple_root(), cloud, None, exit_event))
    for sync in syncs:
        syncs[sync].start()  # start the thread

    b_to_a = os.path.join(local_folders[0], file_names[1])
    wait_for_file(b_to_a)

    a_to_b = os.path.join(local_folders[1], file_names[0])
    wait_for_file(a_to_b)

    exit_event.set()

    for node in nodes:
        syncs[node].join()

    assert(os.path.exists(b_to_a))
    assert(os.path.exists(a_to_b))

    latus.logger.log.info('test_simple exiting')

    return

