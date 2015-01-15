
import os
import glob
import shutil

import watchdog.observers
import watchdog.events
import send2trash

import latus.logger
import latus.util
import latus.const
import latus.walker
import latus.hash
import latus.crypto
import latus.fsdb
import latus.miv


class Sync(watchdog.events.FileSystemEventHandler):
    """
    Determines what needs to be done to sync local to cloud.
    """

    def __init__(self, crypto_key, latus_folder, cloud_root, node_id, verbose):
        self.timeout = 60  # seconds
        self.crypto_key = crypto_key
        self.latus_folder = latus_folder
        self.cloud_folder = os.path.join(cloud_root, '.' + latus.const.NAME)
        self.cloud_cache_folder = os.path.join(self.cloud_folder, 'cache')
        self.cloud_fs_db_folder = os.path.join(self.cloud_folder, 'fsdb')
        self.cloud_miv_folder = os.path.join(self.cloud_folder, 'miv')
        self.node_id = node_id
        self.verbose = verbose
        self.fernet_extension = '.fer'

        latus.logger.log.info('local_folder : %s' % self.latus_folder)
        latus.logger.log.info('cloud_fs_db : %s' % self.cloud_fs_db_folder)
        latus.logger.log.info('cloud_cache : %s' % self.cloud_cache_folder)
        latus.logger.log.info('cloud_miv : %s' % self.cloud_miv_folder)
        latus.logger.log.info('crypto_key : %s' % self.crypto_key)
        latus.logger.log.info('node_id : %s' % self.node_id)

        latus.util.make_dirs(self.latus_folder)
        latus.util.make_dirs(self.cloud_cache_folder)
        latus.util.make_dirs(self.cloud_fs_db_folder)
        latus.util.make_dirs(self.cloud_miv_folder)

    def start(self):
        self.sync_local()
        self.sync_other()

        self.latus_observer = watchdog.observers.Observer()
        self.latus_observer.schedule(self, self.latus_folder, recursive=True)
        self.latus_observer.start()
        self.cloud_observer = watchdog.observers.Observer()
        self.cloud_observer.schedule(self, self.cloud_folder, recursive=True)
        self.cloud_observer.start()

    def request_exit(self):
        latus.logger.log.info('request_exit begin')

        self.latus_observer.stop()
        self.cloud_observer.stop()
        self.latus_observer.join()
        self.cloud_observer.join()

        latus.logger.log.info('request_exit end')

    def dispatch(self, event):
        self.sync_local()
        self.sync_other()

    def sync_local(self):
        latus.logger.log.info('%s : scanning local %s' % (self.node_id, self.latus_folder))

        crypto = latus.crypto.Crypto(self.crypto_key, self.verbose)

        # new or updated local files
        local_walker = latus.walker.Walker(self.latus_folder)
        for partial_path in local_walker:
            # this is where we use the local _file_ name to create the cloud _folder_ where the fernet and metadata reside
            local_full_path = local_walker.full_path(partial_path)
            hash, _ = latus.hash.calc_sha512(local_full_path)
            if hash:
                # todo: encrypt the hash?
                cloud_fernet_file = os.path.join(self.cloud_cache_folder, hash + self.fernet_extension)
                fs_db = latus.fsdb.FileSystemDB(self.cloud_fs_db_folder, self.node_id, True)
                most_recent_hash = fs_db.get_most_recent_hash(partial_path)
                if hash != most_recent_hash:
                    mtime = os.path.getmtime(local_full_path)
                    size = os.path.getsize(local_full_path)
                    latus.logger.log.info('%s : updated %s' % (self.node_id, local_full_path))
                    fs_db.update(latus.miv.next_miv(self.cloud_miv_folder), partial_path, size, hash, mtime)
                fs_db.close()
                if not os.path.exists(cloud_fernet_file):
                    latus.logger.log.info('%s : writing %s (%s)' % (self.node_id, partial_path, cloud_fernet_file))
                    crypto.compress(self.latus_folder, partial_path, os.path.abspath(cloud_fernet_file))
            else:
                latus.logger.log.warn('no hash for %s' % local_full_path)

        # deleted local files
        fs_db = latus.fsdb.FileSystemDB(self.cloud_fs_db_folder, self.node_id, True)
        for partial_path in fs_db.get_paths():
            db_info = fs_db.get_file_info(partial_path)
            cloud_most_recent_hash = db_info[-1]['hash']
            latus_path = os.path.join(self.latus_folder, partial_path)
            if cloud_most_recent_hash and not os.path.exists(latus_path):
                latus.logger.log.info('%s : found as deleted %s' % (self.node_id, latus_path))
                # mark in DB as deleted
                fs_db.update(latus.miv.next_miv(self.cloud_miv_folder), partial_path, None, None, None)
        fs_db.close()

    def sync_other(self):
        latus.logger.log.info('%s : scanning other nodes' % self.node_id)

        crypto = latus.crypto.Crypto(self.crypto_key, self.verbose)

        # new or updated cloud files
        this_fs_db = latus.fsdb.FileSystemDB(self.cloud_fs_db_folder, self.node_id)
        for db_file in glob.glob(os.path.join(self.cloud_fs_db_folder, '*.db')):
            file_name = os.path.basename(db_file)
            db_node_id = file_name.split('.')[0]
            if db_node_id != self.node_id:
                latus.logger.log.info('%s : checking node %s' % (self.node_id, db_node_id))
                other_fs_db = latus.fsdb.FileSystemDB(self.cloud_fs_db_folder, db_node_id)
                for partial_path in other_fs_db.get_paths():
                    local_path = os.path.join(self.latus_folder, partial_path)

                    local_hash = None
                    if os.path.exists(local_path):
                        local_hash, _ = latus.hash.calc_sha512(local_path)

                    most_recent = None
                    db_info = other_fs_db.get_file_info(partial_path)
                    if db_info:
                        most_recent = db_info[-1]

                    if most_recent and most_recent['size'] and most_recent['size'] > 0:
                        local_sequence = None
                        local_file_info = this_fs_db.get_file_info(partial_path)
                        if local_file_info:
                            local_sequence = local_file_info[-1]['seq']

                        if not os.path.exists(local_path) or \
                                (local_hash != most_recent['hash'] and most_recent['seq'] > local_sequence):
                            cloud_fernet_file = os.path.abspath(os.path.join(self.cloud_cache_folder, most_recent['hash'] + self.fernet_extension))
                            file_abs_path = os.path.abspath(os.path.join(self.latus_folder, partial_path))
                            latus.logger.log.info('%s : %s has changed %s , so propagating to %s' % (self.node_id, db_node_id, partial_path, file_abs_path))
                            expand_ok = crypto.expand(cloud_fernet_file, file_abs_path)
                    if most_recent and most_recent['hash'] is None:
                        latus.logger.log.info('%s : %s has deleted %s , so deleting %s' % (self.node_id, db_node_id, partial_path, local_path))
                        try:
                            if os.path.exists(local_path):
                                send2trash.send2trash(local_path)
                        except OSError:
                            # fallback
                            latus.logger.log.warn('%s : send2trash failed on %s' % (self.node_id, local_path))
