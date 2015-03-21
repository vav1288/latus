

import os
import time

import latus.const
import latus.sync
import latus.util
import latus.logger
import latus.folders
import latus.preferences
import latus.crypto
import latus.local_comm
import test_latus.create_files
import test_latus.util

def get_lan_key_root():
    return os.path.join(test_latus.create_files.get_data_root(), "lan_key")

def test_lan_key(setup):
    """
    test getting the key over the LAN (just this computer for this test case)
    """

    node_a_string = 'a'
    node_b_string = 'b'

    log_folder = os.path.join(get_lan_key_root(), 'log')
    test_latus.util.logger_init(log_folder)

    key = latus.crypto.new_key()

    cloud = os.path.join(get_lan_key_root(), 'cloud')
    node_a = test_latus.util.SetupSyncNode(node_a_string, key, get_lan_key_root(), cloud)
    node_a.get_sync().start()
    time.sleep(1)

    node_b_app_data_folder = test_latus.util.get_app_data_folder(os.path.join(get_lan_key_root(), node_b_string))
    pref = latus.preferences.Preferences(node_b_app_data_folder, True)
    pref.set_node_id(node_b_string)
    pref.set_cloud_root(cloud)
    pref.set_trusted_network(True)

    test_latus.util.wait_for_node(log_folder)

    time.sleep(2)

    key = latus.local_comm.get_key(node_b_app_data_folder)
    latus.logger.log.info('key %s' % key)
    assert(key is not None)  # todo: test for the real value

    is_still_alive = node_a.get_sync().request_exit()
    assert(is_still_alive is False)  # make sure we didn't time out

    latus.logger.log.info('test_lan_key exiting')

    return

