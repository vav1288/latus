
import os
import const


# use this to avoid the metadata
def is_metadata_root(path, metadata_root_override):
    return path == get_metadata_dir_path(path, metadata_root_override)

# from a target file, determine the metadata sqlite file path
def get_metadata_db_path(path, metadata_root_override):
    return os.path.join(get_metadata_dir_path(path, metadata_root_override), const.DB_NAME + ".db")

def get_metadata_dir_path(path, metadata_root_override):
    return os.path.join(get_metadata_root(path, metadata_root_override), const.METADATA_DIR_NAME)

def get_metadata_root(path, metadata_root_override):
    if metadata_root_override is None:
        # get to <drive>:\ or \
        if path is None:
            path = "." # hack
        metadata_root = os.path.abspath(path)
        while os.path.split(metadata_root)[1]:
            metadata_root = os.path.split(metadata_root)[0]
    else:
        metadata_root = metadata_root_override
    return metadata_root

