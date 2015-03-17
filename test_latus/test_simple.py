
import os
import time
from cryptography.fernet import Fernet

import latus.const
import latus.sync
import latus.util
import latus.logger
import latus.folders
import latus.preferences
import test_latus.create_files
import test_latus.util

def get_simple_root():
    return os.path.join(test_latus.create_files.get_data_root(), "simple")

def test_simple(setup):
    """
    test a simple sync of 2 files across 2 nodes
    """

    nodes = ['a', 'b']

    create_folders = test_latus.create_files.Folders(get_simple_root())
    test_latus.util.logger_init(create_folders.get_log_folder())

    key = Fernet.generate_key()

    sync = {}

    for node in nodes:
        test_latus.create_files.write_to_file(os.path.join(create_folders.get_local_folder(node), node + '.txt'), node)

    for node in nodes:
        pref = latus.preferences.Preferences(create_folders.get_appdata_roaming_folder(node))
        pref.set_crypto_key_string(key)
        pref.set_latus_folder(create_folders.get_local_folder(node))
        pref.set_node_id(node)
        pref.set_verbose(True)
        # point both nodes to the same cloud folder to emulate cloud sync
        pref.set_cloud_root(os.path.join(get_simple_root(), 'cloud'))

        sync[node] = latus.sync.Sync(create_folders.get_appdata_roaming_folder(node))

    for node in nodes:
        sync[node].start()

    test_latus.util.wait_for_node(create_folders.get_log_folder())

    for node in nodes:
        sync[node].request_exit()

    local_folders = []
    file_names = []
    for node in nodes:
        local_folders.append(create_folders.get_local_folder(node))
        file_names.append(create_folders.get_file_name(node))
    b_to_a = os.path.join(local_folders[0], file_names[1])
    print('b_to_a', b_to_a)
    assert(os.path.exists(b_to_a))
    a_to_b = os.path.join(local_folders[1], file_names[0])
    print('a_to_b', a_to_b)
    assert(os.path.exists(a_to_b))

    latus.logger.log.info('test_simple exiting')

    return

