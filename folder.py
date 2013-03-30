
import hash
import win32con
import win32api
import util
import pywintypes
import logger
import metadata_location
import walker

# target is a folder (windows) or directory (unix), typically a source or dest
class folder:
    def __init__(self, root, metadata_root, verbose = False):
        self.root = root
        self.verbose = verbose
        if metadata_root is None:
            self.metadata_root = metadata_location.get_metadata_root(root, metadata_root)
        else:
            self.metadata_root = metadata_root
        self.target_hash = hash.hash(metadata_root)
        self.walker = walker.walker(self.root)

    # get metadata database file path
    def get_metadata_db_path(self):
        metadata_location.get_metadata_db_path(None, self.metadata_root)

    def get_paths_from_hash(self, in_hash):
        return self.target_hash.get_paths_from_hash(in_hash, self.root)

    def get_hash(self, path):
        result_hash, self.cache_flag = self.target_hash.get_hash(path)
        return result_hash

    def get_walker(self):
        return self.walker

    def scan(self):
        for partial_path in self.walker:
            full_path = self.walker.get_path(partial_path)
            hidden_flag, system_flag = util.get_file_attributes(full_path)
            if not (hidden_flag or system_flag):
                self.get_hash(full_path)



