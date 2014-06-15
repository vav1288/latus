
import os

import core.db

class Sync():
    """
    Determines what needs to be done to sync local to cloud.
    Assumes local already scanned (see db.scan() ).
    """
    def __init__(self, metadata_folder, local_folder, node_id):
        self.local_folder = local_folder
        self.db = core.db.DB(core.metadatapath.MetadataPath(metadata_folder), node_id, force_drop=True)

    def scan(self):
        self.db.scan(self.local_folder)

    def sync(self):
        for f in self.db:
            print('f', f.abspath)
        # todo: the actual sync!

    def close(self):
        self.db.close()

