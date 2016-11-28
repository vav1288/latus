
import os

import latus.nodedb
import latus.util

import test_latus.tstutil

def get_node_db_general_root():
    return os.path.join(test_latus.tstutil.get_data_root(), "get_node_db_general")


def test_node_db_general():
    log_folder = os.path.join(get_node_db_general_root(), 'log')
    test_latus.tstutil.logger_init(log_folder)

    node_id = 'a'
    general_root = get_node_db_general_root()
    os.makedirs(general_root, exist_ok=True)
    node_db = latus.nodedb.NodeDB(general_root, node_id, True)
    assert(node_db.get_node_id() == node_id)