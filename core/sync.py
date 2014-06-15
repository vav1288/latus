
import os

import core.db

class Sync():
    """
    Determines what needs to be done to sync local to cloud.
    Assumes local already scanned (see db.scan() ).
    """
    def __init__(self, local_db, sync_db, cloud_db):
        self.local_db = local_db
        self.sync_db = sync_db
        self.cloud_db = cloud_db

    def sync(self):
        for f in self.local_db:
            print('f', f.abspath)
        # todo: the actual sync!

