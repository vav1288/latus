
import os

import core.db
import core.const
import core.metadatapath

class Sync():
    """
    Determines what needs to be done to sync local to cloud.
    """
    def __init__(self, cloud_metadata_folder, local_folder, node_id, local_and_sync_metadata_folder = None):
        self.local_folder = local_folder
        if local_and_sync_metadata_folder is None:
            # I'd like to use winpaths.get_local_appdata() but it doesn't seem to work with Python 3, so I'll
            # rely on the environment variable.
            appdata = os.environ['APPDATA']
            local_and_sync_metadata_folder = os.path.join(appdata, core.const.NAME)
        print("local_and_sync_metadata_folder", local_and_sync_metadata_folder)
        # cloud
        self.cdb = core.db.DB(core.metadatapath.MetadataPath(cloud_metadata_folder), 'c', force_drop=True)
        # local
        self.ldb = core.db.DB(core.metadatapath.MetadataPath(local_and_sync_metadata_folder), node_id, force_drop=True)
        # sync
        self.sdb = core.db.DB(core.metadatapath.MetadataPath(local_and_sync_metadata_folder), 's', force_drop=True)

    def scan(self):
        self.ldb.scan(self.local_folder) # scan the local folder

    def sync(self):
        for f in self.ldb:
            print('f', f.abspath)
        # todo: the actual sync!

    def close(self):
        self.ldb.close()

