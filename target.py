
import hash
import metadata_location
import walker

# target is a folder (windows) or directory (unix), typically a source or dest
class target:
    def __init__(self, root, metadata_root = None):
        self.root = root
        if metadata_root is None:
            self.metadata_root = metadata_location.get_metadata_root(root)
        else:
            self.metadata_root = metadata_root
        self.target_hash = hash.hash(metadata_root)
        self.walker = walker.walker(root)

    # get metadata database file path
    def get_metadata_db_path(self):
        metadata_location.get_metadata_db_path(self.metadata_root)

    def get_paths_from_hash(self, in_hash):
        return self.target_hash.get_paths_from_hash(in_hash, self.root)

    def get_hash(self, path):
        result_hash, self.cache_flag = self.target_hash.get_hash(path)
        return result_hash