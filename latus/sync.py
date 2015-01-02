
import os
import json
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

    def __init__(self, crypto_key, latus_folder, cloud_root, verbose=False):
        self.crypto_key = crypto_key
        self.latus_folder = latus_folder
        self.cloud_root = cloud_root
        self.verbose = verbose
        self.fernet_extension = 'fer'

        latus.logger.log.info('local_folder : %s' % self.latus_folder)
        latus.logger.log.info('cloud_root : %s' % self.cloud_root)
        latus.logger.log.info('cloud_folder : %s' % self.get_cloud_folder())
        latus.logger.log.info('crypto_key : %s' % self.crypto_key)

        latus.util.make_dirs(self.latus_folder)
        latus.util.make_dirs(self.get_cloud_folder())

    def get_cloud_folder(self):
        return os.path.join(self.cloud_root, '.' + latus.const.NAME)

    def start(self):
        self.sync()
        self.latus_file_watcher = latus.filewatcher.FileWatcher(self.latus_folder, self.sync)
        self.latus_file_watcher.start()
        self.cloud_file_watcher = latus.filewatcher.FileWatcher(self.get_cloud_folder(), self.sync)
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
            latus.logger.log.info('new : %s' % full_path)
            file_as_cloud_folder = os.path.join(self.get_cloud_folder(), partial_path)
            if not os.path.exists(file_as_cloud_folder):
                os.makedirs(file_as_cloud_folder)
                if self.verbose:
                    print('new local', partial_path)
            hash, _ = latus.hash.calc_sha512(full_path)
            if hash is not None:
                cloud_fernet_file = os.path.join(file_as_cloud_folder, hash + self.fernet_extension)
                if not os.path.exists(cloud_fernet_file):
                    if self.verbose:
                        print('writing', partial_path, '(', cloud_fernet_file, ')')
                    # Input to archive program (7z) is relative to the latus folder.  Note that we have to explicitly
                    # give the full abs path of the archive itself since it's in a different folder.
                    crypto.compress(self.latus_folder, partial_path, os.path.abspath(cloud_fernet_file))
                    mtime = os.path.getmtime(full_path)
                    size = os.path.getsize(full_path)
                    fs_db = latus.fsdb.FileSystemDB(file_as_cloud_folder, partial_path)
                    fs_db.update(size, hash, mtime)
                    fs_db.close()

        # new or updated cloud files
        # todo: we're actually only interested in dirs here ... make Walker have a dirs only mode
        cloud_walker = latus.walker.Walker(self.get_cloud_folder(), do_dirs=True)
        for partial_path in cloud_walker:
            full_path = cloud_walker.full_path(partial_path)
            if os.path.isdir(full_path):
                file_as_cloud_folder = os.path.join(self.get_cloud_folder(), partial_path)
                fs_db = latus.fsdb.FileSystemDB(file_as_cloud_folder)
                changes = fs_db.read()
                file_path = fs_db.get_path()
                fs_db.close()
                if changes:
                    hash = changes[-1]['hash'] # last entry in the list is most recent
                    # todo: compare hashes
                    dest_path = os.path.join(self.latus_folder, file_path)
                    if not os.path.exists(dest_path):
                        cloud_fernet_file = os.path.join(file_as_cloud_folder, hash + self.fernet_extension)
                        abs_cloud_fernet_file = os.path.abspath(cloud_fernet_file)
                        expand_ok = crypto.expand(self.latus_folder, abs_cloud_fernet_file, dest_path)
                        if not expand_ok:
                            latus.logger.log.error('could not expand : %s , %s , %s' %
                                                   (self.latus_folder, abs_cloud_fernet_file, dest_path))
                else:
                    latus.logger.log.warn('no DB : %s' % file_as_cloud_folder)

