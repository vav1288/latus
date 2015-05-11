
import os
import datetime
import time

import latus.logger
import latus.preferences
import latus.nodedb
import latus.util
import latus.folders
import latus.key_management
import test_latus.create_files


def get_key_management_root():
    return os.path.join(test_latus.create_files.get_data_root(), "key_management")


def test_key_management():
    import shutil

    if os.path.exists(get_key_management_root()):
        shutil.rmtree(get_key_management_root())

    log_folder = os.path.join(get_key_management_root(), 'log')
    latus.util.make_dirs(log_folder)
    latus.logger.init(log_folder)
    cloud_folder = os.path.join(get_key_management_root(), 'cloud')
    cloud_folders = latus.folders.CloudFolders(cloud_folder)

    nodes = ['a', 'b']
    user_prefix = 'user_'
    computer_prefix = 'computer_'
    pref = {}
    node_dbs = {}
    kms = {}
    for node in nodes:
        app_data_folder = os.path.join(get_key_management_root(), node, 'appdata')
        pref[node] = latus.preferences.Preferences(app_data_folder, True)
        pref[node].set_node_id(node)
        pref[node].set_new_private_key()
        pref[node].set_cloud_root(cloud_folder)
        node_dbs[node] = latus.nodedb.NodeDB(cloud_folders.nodedb, node, pref[node].get_public_key(), True)
        node_dbs[node].set_user(user_prefix + node)  # essentially override defaults
        node_dbs[node].set_computer(computer_prefix + node)  # essentially override defaults
        kms[node] = latus.key_management.KeyManagement(app_data_folder, False, True)
        kms[node].start()
        time.sleep(1)

    key_0 = pref[nodes[0]].get_crypto_key()
    key_1 = pref[nodes[1]].get_crypto_key()
    latus.logger.log.info('key : %s' % key_0)
    assert(key_0 is not None)
    assert(key_0 == key_1)

    for node in nodes:
        kms[node].request_exit()
    for node in nodes:
        kms[node].join()

