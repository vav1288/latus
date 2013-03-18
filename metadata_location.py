
import os
import const


# use this to avoid the metadata
def is_metadata_root(path):
    return path == get_metadata_dir_path(path)

# from a target file, determine the metadata sqlite file path
def get_metadata_db_path(path = None):
    return os.path.join(get_metadata_dir_path(path), const.DB_NAME + ".db")

def get_metadata_dir_path(path):
    return os.path.join(get_metadata_root(path), const.METADATA_DIR_NAME)

def get_metadata_root(path, metadata_root_override = None):
    if metadata_root_override is not None:
        metadata_root = metadata_root_override
    else:
        # get to <drive>:\ or \
        metadata_root = os.path.abspath(path)
        while os.path.split(metadata_root)[1]:
            metadata_root = os.path.split(metadata_root)[0]
    return metadata_root

