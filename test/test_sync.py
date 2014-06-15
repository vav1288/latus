
import core.sync
import core.metadatapath
import test.create_files
from test.conftest import setup

def test_sync(setup):
    (node_a_path, node_a_id), (node_b_path, node_b_id) = test.create_files.get_sync_node_info()
    sync = core.sync.Sync(test.create_files.get_metadata_root(), node_a_path, node_a_id)
    sync.scan()
    sync.sync()
    sync.close()
