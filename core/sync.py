
import os

import core.db

class Sync():
    """
    Determines what needs to be done to sync local to cloud.
    Assumes local already scanned (see db.scan() ).
    """
    def __init__(self, metadata_folder, local_folder, node_id):
        self.local_folder = local_folder
        self.ldb = core.db.DB(core.metadatapath.MetadataPath(metadata_folder), node_id, force_drop=True) # local
        self.cdb = core.db.DB(core.metadatapath.MetadataPath(metadata_folder), 'c', force_drop=True) # cloud
        self.sdb = core.db.DB(core.metadatapath.MetadataPath(metadata_folder), 's', force_drop=True) # sync

    def scan(self):
        self.ldb.scan(self.local_folder) # scan the local folder

    def sync(self):
        for f in self.ldb:
            print('f', f.abspath)
        # todo: the actual sync!

    def close(self):
        self.ldb.close()

