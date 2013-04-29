
import os

from . import const, logger

def is_metadata_root(file_path, metadata_override):
    return file_path == get_metadata_root(file_path, metadata_override)

# from a target file, determine the metadata sqlite file path
def get_metadata_db_path(file_path, metadata_override):
    metadata_dir = get_metadata_root(file_path, metadata_override)
    metadata_filename = const.LFS_DB_NAME + const.DB_EXT
    if metadata_override is not None:
        if metadata_override.name is not None:
            metadata_filename = metadata_override.name + const.DB_EXT
    db_path = os.path.join(metadata_dir, const.METADATA_DIR_NAME, metadata_filename)
    return db_path

def get_metadata_root(file_path, metadata_root_override):
    if metadata_root_override is None:
        # get to <drive>:\ or \
        if file_path is None:
            file_path = "." # hack
        metadata_dir = os.path.abspath(file_path)
        while os.path.split(metadata_dir)[1]:
            metadata_dir = os.path.split(metadata_dir)[0]
    else:
        metadata_dir = metadata_root_override.root
    return metadata_dir


