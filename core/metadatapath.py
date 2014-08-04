
import os
import core.logger
import core.const
import core.util
import win32api, win32con
import functools

CLOUD = 1  # cloud storage side- dropbox, etc.
LOCAL = 2  # local - e.g. appdata in Windows

DB_DIR_NAME = 'db'
CACHE_DIR_NAME = 'cache'

class MetadataPath():
    """
    Helper for creating and managing the metadata folder/dir
    """

    def __init__(self, metadata_base, folder_type = LOCAL, make_hidden = False):
        if folder_type == CLOUD:
            self.metadata_dir_name = "." + core.const.NAME  # put a dot in front for cloud folder
        elif folder_type == LOCAL:
            self.metadata_dir_name = core.const.NAME  # no dot for local folder
        self.metadata_base = metadata_base
        if not os.path.exists(self.db_folder):
            os.makedirs(self.db_folder)
        if make_hidden:
            core.util.make_hidden(self.metadata_dir_path)

    @property
    def metadata_dir_path(self):
        return os.path.join(self.metadata_base, self.metadata_dir_name)

    @property
    def db_folder(self):
        return functools.reduce(os.path.join, self.db_folder_as_list)

    @property
    def db_folder_as_list(self):
        return [self.metadata_base, self.metadata_dir_name, DB_DIR_NAME]


    @property
    def cache_folder(self):
        return functools.reduce(os.path.join, self.cache_folder_as_list)

    @property
    def cache_folder_as_list(self):
        return [self.metadata_base, self.metadata_dir_name, CACHE_DIR_NAME]
