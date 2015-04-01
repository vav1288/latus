
import os
import datetime

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

    latus_key = 'my_secret_latus_key'

    if os.path.exists(get_key_management_root()):
        shutil.rmtree(get_key_management_root())

    log_folder = os.path.join(get_key_management_root(), 'log')
    latus.util.make_dirs(log_folder)
    latus.logger.init(log_folder)
    cloud_folder = os.path.join(get_key_management_root(), 'cloud')
    cloud_folders = latus.folders.CloudFolders(cloud_folder)

    user_prefix = 'user_'
    computer_prefix = 'computer_'
    preferences = {}
    node_dbs = {}
    kms = {}
    for node in ['a', 'b']:
        app_data_folder = os.path.join(get_key_management_root(), node, 'appdata')
        preferences[node] = latus.preferences.Preferences(app_data_folder, True)
        preferences[node].set_node_id(node)
        preferences[node].set_new_private_key()
        preferences[node].set_cloud_root(cloud_folder)
        node_dbs[node] = latus.nodedb.NodeDB(cloud_folders.nodedb, node, preferences[node].get_public_key(), True)
        node_dbs[node].set_user(user_prefix + node)  # essentially override defaults
        node_dbs[node].set_computer(computer_prefix + node)  # essentially override defaults
        kms[node] = latus.key_management.KeyManagement(app_data_folder)
    preferences['b'].set_crypto_key_string(latus_key)  # b has the latus key, a wants it

    # a requests from b
    kms['a'].request_key()
    requesters = kms['b'].get_requesters()
    assert(requesters == ['a'])
    requester_user, requester_computer = kms['b'].get_requester_info(requesters[0])
    assert(requester_user == user_prefix + 'a')
    assert(requester_computer == computer_prefix + 'a')
    kms['b'].respond_to_request('a')
    key_from_b = kms['a'].get_key()
    assert(latus_key == key_from_b)
    preferences['a'].set_crypto_key_string(key_from_b)

    # now b can request from a (just for testing ... b already has it ...)
    kms['b'].request_key()
    kms['a'].respond_to_request('b')

    # test that we can request again without breaking anything
    kms['a'].request_key()  # over write existing one
    kms['a'].request_key(datetime.datetime.utcnow() - datetime.timedelta(days=10))  # an "old" one that will get deleted
    requesters = kms['b'].get_requesters()  # this will delete the "old" one from above
    assert(requesters == ['b'])


