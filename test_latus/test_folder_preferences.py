
import os

import latus.const
import latus.sync
import latus.util
import latus.logger
import latus.folders
import latus.crypto
import latus.preferences
import test_latus.util


def get_simple_root():
    return os.path.join(test_latus.util.get_data_root(), "folder_preferences")


def test_simple(setup):
    """
    test folder preferences
    """

    nodes = ['a', 'b']

    log_folder = os.path.join(get_simple_root(), 'log')
    test_latus.util.logger_init(log_folder)

    key = latus.crypto.new_key()

    sync = {}

    sub_folder = 's'

    cloud = os.path.join(get_simple_root(), 'cloud')
    for node in nodes:
        sync[node] = test_latus.util.SetupSyncNode(node, key, get_simple_root(), cloud, sub_folder)
        sync[node].set_folder_preferences(False, True, False)
    for node in nodes:
        test_latus.util.write_to_file(sync[node].get_file_path(), node)
    for node in nodes:
        sync[node].get_sync().start()

    test_latus.util.wait_for_node(log_folder)

    for node in nodes:
        sync[node].get_sync().request_exit()

    local_folders = []
    file_names = []
    for node in nodes:
        local_folders.append(sync[node].get_latus_folder())
        file_names.append(sync[node].get_file_name())
    b_to_a = os.path.join(local_folders[0], sub_folder, file_names[1])
    print('b_to_a', b_to_a)
    assert(os.path.exists(b_to_a))
    a_to_b = os.path.join(local_folders[1], sub_folder, file_names[0])
    print('a_to_b', a_to_b)
    assert(os.path.exists(a_to_b))

    latus.logger.log.info('test_simple exiting')

    return

