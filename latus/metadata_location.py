
import os

from . import const, logger, util

def is_metadata_root(p, metadata_root):
    if os.path.isfile(p):
        p = os.path.split(p)[0] # get folder this file is in
    return p == get_metadata_root(metadata_root, p)

# from a target file, determine the metadata sqlite file path
def get_metadata_db_path(metadata, file_path = None):
    metadata_dir = get_metadata_root(metadata, file_path)
    metadata_filename = const.LFS_DB_NAME + const.DB_EXT
    if metadata is not None:
        if metadata.name is not None:
            metadata_filename = metadata.name + const.DB_EXT
    metadata_dir = os.path.join(metadata_dir, const.METADATA_DIR_NAME)
    # todo: make a separate function that does this make dir in case we are only intending to read an existing set of files
    if not os.path.exists(metadata_dir):
        os.makedirs(metadata_dir)
        util.make_hidden(metadata_dir)
    db_path = os.path.join(metadata_dir, metadata_filename)
    return db_path

def get_metadata_root(metadata_root, file_path):
    if metadata_root is None:
        # get to <drive>:\ or \
        if file_path is None:
            file_path = "." # hack
        metadata_dir = os.path.abspath(file_path)
        while os.path.split(metadata_dir)[1]:
            metadata_dir = os.path.split(metadata_dir)[0]
    else:
        metadata_dir = metadata_root.root
    return metadata_dir


