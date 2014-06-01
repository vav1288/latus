
import os
import core.logger
import core.const
import core.util
import win32api, win32con
import functools

class MetadataPath():
    """
    Helper for creating and managing the metadata folder/dir
    """
    METADATA_DIR_NAME = "." + core.const.NAME
    DB_DIR_NAME = 'db'

    def __init__(self, metadata_base):
        self.metadata_base = metadata_base
        if not os.path.exists(self.db_folder):
            os.makedirs(self.db_folder)
        core.util.make_hidden(os.path.join(self.metadata_base, self.METADATA_DIR_NAME))

    @property
    def db_folder(self):
        return functools.reduce(os.path.join, self.db_folder_as_list)

    @property
    def db_folder_as_list(self):
        return [self.metadata_base, self.METADATA_DIR_NAME, self.DB_DIR_NAME]

