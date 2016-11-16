
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


# todo: make this a much better test!
def test_folder_preferences(setup):
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
        test_latus.util.write_to_file(sync[node].get_file_dir(), sync[node].get_file_name(), node)
    for node in nodes:
        sync[node].get_sync().start()

    for node in nodes:
        sync[node].get_sync().request_exit()

    return

