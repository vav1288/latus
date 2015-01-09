
import os
from cryptography.fernet import Fernet
import latus.const
import latus.sync
import test_latus.create_files
from test_latus.conftest import setup

def test_mult(setup):
    """
    test a simple sync of 2 files across 2 nodes
    """

    key = Fernet.generate_key()

    sync_nodes_test_info = test_latus.create_files.SyncNodesTestInfo()
    sync = {}

    for node in sync_nodes_test_info.nodes:
        # point both nodes to the same cloud folder to 'emulate' cloud sync
        sync[node] = latus.sync.Sync(key, sync_nodes_test_info.get_local_folder(node),
                                     sync_nodes_test_info.get_cloud_folder(sync_nodes_test_info.nodes[0]),
                                     node, True)
        sync[node].sync()

    for node in sync_nodes_test_info.nodes:
        sync[node].sync()

    local_folders = []
    file_names = []
    for node in sync_nodes_test_info.nodes:
        local_folders.append(sync_nodes_test_info.get_local_folder(node))
        file_names.append(sync_nodes_test_info.get_file_name(node))
    b_to_a = os.path.join(local_folders[0], file_names[1])
    print('b_to_a', b_to_a)
    assert(os.path.exists(b_to_a))
    a_to_b = os.path.join(local_folders[1], file_names[0])
    print('a_to_b', a_to_b)
    assert(os.path.exists(a_to_b))
    return

