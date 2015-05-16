
import os
import time

import latus.logger
import latus.preferences
import latus.nodedb
import latus.util
import latus.folders
import latus.key_management
import latus.crypto
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
        if node == nodes[0]:
            pref[node].set_crypto_key(latus.crypto.new_key())
        node_dbs[node] = latus.nodedb.NodeDB(cloud_folders.nodes, node, pref[node].get_public_key(), True)
        node_dbs[node].set_user(user_prefix + node)  # essentially override defaults
        node_dbs[node].set_computer(computer_prefix + node)  # essentially override defaults
        kms[node] = latus.key_management.KeyManagement(app_data_folder, False, True)
        kms[node].start()

    time_out = 20.0  # seconds
    timer_sec_per_iteration = 0.01  # seconds
    timer_count = 0.0  # seconds
    key_0 = pref[nodes[0]].get_crypto_key()
    key_1 = None
    while key_1 is None and timer_count <= time_out:
        key_1 = pref[nodes[1]].get_crypto_key()
        if not key_1:
            time.sleep(timer_sec_per_iteration)
            timer_count += timer_sec_per_iteration
    latus.logger.log.info('key wait time : %f (sec)' % float(timer_count))

    latus.logger.log.info('key_0 : %s' % key_0)
    latus.logger.log.info('key_1 : %s' % key_1)
    assert(key_0 is not None)
    assert(key_0 == key_1)

    for node in nodes:
        kms[node].request_exit()
    for node in nodes:
        kms[node].join()

