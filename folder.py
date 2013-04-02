
import hash
import os
import hashlib
import util
import metadata_location
import walker

# target is a folder (windows) or directory (unix), typically a source or dest
class folder:
    def __init__(self, root, metadata_root, verbose = False):
        self.root = root
        self.verbose = verbose
        self.metadata_root = metadata_root
        self.target_hash = hash.hash(metadata_root)
        self.walker = walker.walker(self.root)

    # get metadata database file path
    def get_metadata_db_path(self):
        metadata_location.get_metadata_db_path(None, self.metadata_root)

    def get_paths_from_hash(self, in_hash):
        return self.target_hash.get_paths_from_hash(in_hash, self.root)

    # get the hash of a file or a directory/folder
    # todo: get rid of this??? it simple calls the hash module...
    def get_hash(self, in_path):
        result_hash, self.cache_flag = self.target_hash.get_hash(in_path)
        return result_hash

    def get_walker(self):
        return self.walker

    def scan(self):
        for partial_path in self.walker:
            full_path = self.walker.get_path(partial_path)
            attributes = util.get_file_attributes(full_path)
            # should an attribute filter flag be added here?
            if not attributes:
                self.get_hash(full_path)



