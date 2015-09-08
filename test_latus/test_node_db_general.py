
import os

import latus.nodedb

import test_latus.paths
import test_latus.util

def get_node_db_general_root():
    return os.path.join(test_latus.paths.get_data_root(), "get_node_db_general")


def test_node_db_general():
    log_folder = os.path.join(get_node_db_general_root(), 'log')
    test_latus.util.logger_init(log_folder)

    node_id = 'a'
    node_db = latus.nodedb.NodeDB(get_node_db_general_root(), node_id, True)
    assert(node_db.get_node_id() == node_id)