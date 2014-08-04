
import os
import shutil
import core.logger
import core.util
import core.db
import core.const
import core.metadatapath

class Sync():
    """
    Determines what needs to be done to sync local to cloud.
    """
    def __init__(self, cloud_folder, latus_folder, node_id, appdata_folder = None):
        self.latus_folder = latus_folder
        self.node_id = node_id

        self.cloud_metadata = core.metadatapath.MetadataPath(cloud_folder, core.metadatapath.CLOUD)
        self.appdata_metadata = core.metadatapath.MetadataPath(appdata_folder)

        core.util.make_dirs(self.latus_folder)
        core.util.make_dirs(self.cloud_metadata.cache_folder)

        if appdata_folder is None:
            # I'd like to use winpaths.get_local_appdata() but it doesn't seem to work with Python 3, so I'll
            # rely on the environment variable.
            appdata_folder = os.environ['APPDATA']
        # cloud
        self.cdb = core.db.DB(self.cloud_metadata, 'c')
        # local
        self.ldb = core.db.DB(self.appdata_metadata, 'l')
        # sync
        self.sdb = core.db.DB(self.appdata_metadata, 's')

        core.logger.log.info("%s:%s", "cloud", self.cdb.sqlite_db_path)
        core.logger.log.info("%s:%s", "local", self.ldb.sqlite_db_path)
        core.logger.log.info("%s:%s", "sync", self.sdb.sqlite_db_path)

    def scan(self):
        self.ldb.scan(self.latus_folder) # scan the local latus folder

    def sync(self):
        local_files = set(f.path for f in self.ldb)
        sync_files = set(f.path for f in self.sdb)
        cloud_files = set(f.path for f in self.cdb)
        print('l', local_files)
        print('s', sync_files)
        print('c', cloud_files)

        # the main sync algo
        # todo: add hash into this - right now this doesn't take revisions into account
        download = cloud_files - sync_files
        upload = local_files - sync_files
        conflict = download & upload # intersection
        # this ensures these 3 lists are mutually exclusive
        download = download - conflict
        upload = upload - conflict

        # todo: delete

        print('download', download)
        print('upload', upload)
        print('conflict', conflict)
        for rel_path in upload:
            # copy into the cache proactively
            cache_file_path = os.path.join(self.cloud_metadata.cache_folder, rel_path)
            if not os.path.exists(cache_file_path):
                shutil.copy2(os.path.join(self.latus_folder, rel_path), cache_file_path)
            # tell the cloud db we're sync'd, and mark the sync db as well
            self.add_to_db(self.sdb, rel_path)
            self.add_to_db(self.cdb, rel_path)
        for rel_path in download:
            cache_file_path = os.path.join(self.cloud_metadata.cache_folder, rel_path)
            if os.path.exists(cache_file_path):
                # it's in the cache - so go get it
                shutil.copy2(cache_file_path, os.path.join(self.latus_folder, rel_path))
                # todo: this scan does too much ... figure out how to just do a db copy ... probably have to modify "add_to_db()"
                self.scan()
                self.add_to_db(self.sdb, rel_path)
            else:
                # request it
                self.cdb.session.add(core.db.Request(path=rel_path, nodeid = self.node_id))
        for rel_path in conflict:
            print("todo: resolve conflict:", rel_path)

    def add_to_db(self, dest_db, rel_path):
            file_info = self.ldb.get_file_info(rel_path)
            dest_db.session.add(core.db.Files(absroot=None, path=rel_path, sha512=file_info.sha512,size=file_info.size,
                                              mtime=file_info.mtime, hidden=file_info.hidden,system=file_info.system))
            dest_db.commit()

    def close(self):
        self.ldb.close()

