
import os
import glob
import latus.logger
import latus.util
import latus.const
import latus.walker
import latus.hash
import latus.crypto
import latus.filewatcher
import latus.fsdb


class Sync():
    """
    Determines what needs to be done to sync local to cloud.
    """

    def __init__(self, crypto_key, latus_folder, cloud_root, node_id, verbose):
        self.crypto_key = crypto_key
        self.latus_folder = latus_folder
        cloud_folder = os.path.join(cloud_root, '.' + latus.const.NAME)
        self.cloud_cache_folder = os.path.join(cloud_folder, 'cache')
        self.cloud_fs_db_folder = os.path.join(cloud_folder, 'fsdb')
        self.node_id = node_id
        self.verbose = verbose
        self.fernet_extension = '.fer'

        latus.logger.log.info('local_folder : %s' % self.latus_folder)
        latus.logger.log.info('cloud_fs_db : %s' % self.cloud_fs_db_folder)
        latus.logger.log.info('cloud_cache : %s' % self.cloud_cache_folder)
        latus.logger.log.info('crypto_key : %s' % self.crypto_key)
        latus.logger.log.info('node_id : %s' % self.node_id)

        latus.util.make_dirs(self.latus_folder)
        latus.util.make_dirs(self.cloud_cache_folder)
        latus.util.make_dirs(self.cloud_fs_db_folder)

    def start(self):
        self.sync()
        self.latus_file_watcher = latus.filewatcher.FileWatcher(self.latus_folder, self.sync)
        self.latus_file_watcher.start()
        self.cloud_file_watcher = latus.filewatcher.FileWatcher(self.cloud_cache_folder, self.sync)
        self.cloud_file_watcher.start()

    def request_exit(self):
        self.latus_file_watcher.request_exit()
        self.cloud_file_watcher.request_exit()

    def sync(self):
        """
        Sync new or updated files (both local and cloud).
        """

        latus.logger.log.info('scanning : %s' % self.latus_folder)

        crypto = latus.crypto.Crypto(self.crypto_key, self.verbose)

        # new or updated local files
        local_walker = latus.walker.Walker(self.latus_folder)
        for partial_path in local_walker:
            # this is where we use the local _file_ name to create the cloud _folder_ where the fernet and metadata reside
            full_path = local_walker.full_path(partial_path)
            hash, _ = latus.hash.calc_sha512(full_path)
            if hash:
                # todo: encrypt the hash?
                cloud_fernet_file = os.path.join(self.cloud_cache_folder, hash + self.fernet_extension)
                fs_db = latus.fsdb.FileSystemDB(self.cloud_fs_db_folder, self.node_id)
                most_recent_hash = fs_db.get_most_recent_hash(partial_path)
                if hash != most_recent_hash:
                    mtime = os.path.getmtime(full_path)
                    size = os.path.getsize(full_path)
                    fs_db.update(self.get_highest_sequence_value() + 1, partial_path, size, hash, mtime)
                fs_db.close()
                if not os.path.exists(cloud_fernet_file):
                    latus.logger.log.info('writing %s (%s)' % (partial_path, cloud_fernet_file))
                    crypto.compress(self.latus_folder, partial_path, os.path.abspath(cloud_fernet_file))
            else:
                latus.logger.log.warn('no hash for %s' % full_path)

        # deleted local files
        fs_db = latus.fsdb.FileSystemDB(self.cloud_fs_db_folder, self.node_id)
        for partial_path in fs_db.get_paths():
            db_info = fs_db.get_file_info(partial_path)
            cloud_most_recent_hash = db_info[-1]['hash']
            if not cloud_most_recent_hash and os.path.exists(os.path.join(self.latus_folder, partial_path)):
                # mark in DB as deleted
                fs_db.update(self.get_highest_sequence_value() + 1, partial_path, None, None, None)
        fs_db.close()

        # new or updated cloud files
        for db_file in glob.glob(os.path.join(self.cloud_fs_db_folder, '*.db')):
            file_name = os.path.basename(db_file)
            node_id = file_name.split('.')[0]
            fs_db = latus.fsdb.FileSystemDB(self.cloud_fs_db_folder, node_id)
            for partial_path in fs_db.get_paths():
                local_path = os.path.join(self.latus_folder, partial_path)
                local_hash = None
                if os.path.exists(local_path):
                    local_hash, _ = latus.hash.calc_sha512(local_path)
                db_info = fs_db.get_file_info(partial_path)
                cloud_most_recent_hash = db_info[-1]['hash']
                if not os.path.exists(local_path) or local_hash != cloud_most_recent_hash:
                    cloud_fernet_file = os.path.abspath(os.path.join(self.cloud_cache_folder, cloud_most_recent_hash + self.fernet_extension))
                    file_abs_path = os.path.abspath(os.path.join(self.latus_folder, partial_path))
                    expand_ok = crypto.expand(cloud_fernet_file, file_abs_path)

    def get_highest_sequence_value(self):
        """
        Get the highest sequence value of all the DBs.  Returns -1 if none found (so 1 can be added to start at 0).
        """
        highest_sequence_value = -1
        for db_file in glob.glob(os.path.join(self.cloud_fs_db_folder, '*.db')):
            file_name = os.path.basename(db_file)
            node_id = file_name.split('.')[0]
            fs_db = latus.fsdb.FileSystemDB(self.cloud_fs_db_folder, node_id)
            highest_sequence_value = max(highest_sequence_value, fs_db.get_highest_sequence_value())
        return highest_sequence_value
