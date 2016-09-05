
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
from test_latus.util import logger_init, get_latus_folder, wait_for_file, sync_node, write_to_file, get_data_root


def get_delete_root():
    return os.path.join(get_data_root(), "delete")


def test_delete(setup):
    """
    test a simple delete across 2 nodes
    """

    nodes = ['a', 'b']
    file_a = 'a.txt'
    local_folders = []
    for node in nodes:
        local_folders.append(get_latus_folder(get_delete_root(), node))
    file_path_a = os.path.join(local_folders[0], file_a)
    file_path_b = os.path.join(local_folders[1], file_a)

    log_folder = os.path.join(get_delete_root(), 'log')
    logger_init(log_folder)

    key = latus.crypto.new_key()

    syncs = {}
    exit_event = multiprocessing.Event()

    cloud = os.path.join(get_delete_root(), 'cloud')
    for node in nodes:
        syncs[node] = multiprocessing.Process(target=sync_node,
                                              args=(node, key, get_delete_root(), cloud, None, exit_event, False))

    for sync in syncs:
        syncs[sync].start()

    time.sleep(1)
    latus.logger.log.info('starting write to %s' % file_path_a)
    write_to_file(file_path_a, 'a')
    latus.logger.log.info('finished write to %s' % file_path_a)

    time.sleep(1)

    wait_for_file(file_path_a)
    wait_for_file(file_path_b)

    assert(os.path.exists(file_path_a))
    assert(os.path.exists(file_path_b))

    latus.logger.log.info('starting delete of %s' % file_path_a)
    os.remove(file_path_a)  # remove it on a
    latus.logger.log.info('finished delete of %s' % file_path_a)

    time.sleep(1)

    wait_for_file(file_path_a, False)
    wait_for_file(file_path_b, False)

    assert(not os.path.exists(file_path_a))
    assert(not os.path.exists(file_path_b))

    time.sleep(1)

    exit_event.set()

    for node in nodes:
        syncs[node].join()

    latus.logger.log.info('test_delete exiting')

    return

