
import os
import shutil
import core.const
import core.sync
import core.metadatapath
import test.create_files
from test.conftest import setup

cloud_folder_name = 'cloud'  # folder name for cloud storage provider

# todo: return a list of the paths with their relative path from root_path, not just merely the file names
def get_file_names(root_path):
    """
    Get a sorted list of all file names (but NOT their path) in path.
    :param root_path: folder/directory to look in
    :return: sorted list of files
    """
    files = []
    for r, _, fns in os.walk(root_path):
        for fn in fns:
            files.append(fn)
    files.sort()
    return files

def copy_metadata(src, dest):
    # fake out cloud sync of the db file
    metadata_src = core.metadatapath.MetadataPath(os.path.join(src, cloud_folder_name),
                                                  folder_type=core.metadatapath.CLOUD)
    metadata_dest = core.metadatapath.MetadataPath(os.path.join(dest, cloud_folder_name),
                                                  folder_type=core.metadatapath.CLOUD)
    print("copying", metadata_src.metadata_dir_path, ' to ', metadata_dest.metadata_dir_path)
    # todo: I'd really like a copy that copies each file but where I don't have to wipe out the dest tree first
    shutil.rmtree(metadata_dest.metadata_dir_path)
    shutil.copytree(metadata_src.metadata_dir_path, metadata_dest.metadata_dir_path)

def test_sync(setup):
    (node_a_root, node_a_id), (node_b_root, node_b_id) = test.create_files.get_sync_node_info()

    def do_sync(node_root, node_id):
        sync = core.sync.Sync(os.path.join(node_root, cloud_folder_name), os.path.join(node_root, core.const.NAME),
                              node_id, appdata_folder=os.path.join(node_root, 'appdata'))
        sync.scan()
        sync.sync()
        sync.close()

    do_sync(node_a_root, node_a_id)
    copy_metadata(node_a_root, node_b_root)  # emulate cloud sync of the db file
    do_sync(node_b_root, node_b_id)
    copy_metadata(node_b_root, node_a_root)  # emulate cloud sync of the db file
    do_sync(node_a_root, node_a_id)

    # Test that we've sync'd the files across the two nodes
    assert get_file_names(os.path.join(node_a_root, core.const.NAME)) == get_file_names(os.path.join(node_b_root, core.const.NAME))