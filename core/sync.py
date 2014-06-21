
import os

import core.logger
import core.db
import core.const
import core.metadatapath

class Sync():
    """
    Determines what needs to be done to sync local to cloud.
    """
    def __init__(self, cloud_metadata_folder, local_folder, node_id, appdata_folder = None):
        self.local_folder = local_folder
        if appdata_folder is None:
            # I'd like to use winpaths.get_local_appdata() but it doesn't seem to work with Python 3, so I'll
            # rely on the environment variable.
            appdata_folder = os.environ['APPDATA']
        # cloud
        self.cdb = core.db.DB(core.metadatapath.MetadataPath(cloud_metadata_folder, core.metadatapath.CLOUD), 'c')
        # local
        self.ldb = core.db.DB(core.metadatapath.MetadataPath(appdata_folder), 'l')
        # sync
        self.sdb = core.db.DB(core.metadatapath.MetadataPath(appdata_folder), 's')

        core.logger.log.info("%s:%s", "cloud", self.cdb.sqlite_db_path)
        core.logger.log.info("%s:%s", "local", self.ldb.sqlite_db_path)
        core.logger.log.info("%s:%s", "sync", self.sdb.sqlite_db_path)

    def scan(self):
        self.ldb.scan(self.local_folder) # scan the local folder

    def sync(self):
        for f in self.ldb:
            print('f', f.abspath)
        # todo: the actual sync!

    def close(self):
        self.ldb.close()

