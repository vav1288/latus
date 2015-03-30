from builtins import property
import os
import glob
import json
import time
import datetime

import watchdog.observers
import watchdog.events
import send2trash
import random

import latus.logger
import latus.util
import latus.const
import latus.preferences
import latus.walker
import latus.hash
import latus.crypto
import latus.nodedb
import latus.miv
import latus.folders

TIME_OUT = 60  # seconds


class SyncBase(watchdog.events.FileSystemEventHandler):

    def __init__(self, app_data_folder):
        self.call_count = 0
        self.fernet_extension = '.fer'
        self.app_data_folder = app_data_folder
        self.observer = watchdog.observers.Observer()
        latus.logger.log.info('log_folder : %s' % latus.logger.get_log_folder())
        self.write_log_status()

    def get_type(self):
        # type of folder - children provide this - e.g. local, cloud
        return None

    def request_exit(self):
        pref = latus.preferences.Preferences(self.app_data_folder)
        latus.logger.log.info('%s - %s - request_exit begin' % (pref.get_node_id(), self.get_type()))
        self.observer.stop()
        self.observer.join(TIME_OUT)
        latus.logger.log.info('%s - %s - request_exit end' % (pref.get_node_id(), self.get_type()))
        return self.observer.is_alive()

    def start(self):
        self.dispatch(None)  # rescan entire folder before we 'start' the observer
        self.observer.start()

    def write_log_status(self):
        # write a out the status of this sync - e.g. local is running, etc.
        if latus.logger.get_log_folder() and self.get_type():
            log_folder = latus.logger.get_log_folder()
            latus.util.make_dirs(log_folder)
            file_path = os.path.join(log_folder, self.get_type() + '.log')
            if os.path.exists(file_path):
                with open(file_path) as f:
                    try:
                        json_data = json.load(f)
                    except ValueError:
                        json_data = {'count': 0}
                    if json_data:
                        json_data['count'] += 1
            else:
                json_data = {'count': 0}
            json_data['timestamp'] = time.time()
            with open(file_path, 'w') as f:
                json.dump(json_data, f)
        else:
            latus.logger.log.warn('log_status can not write file')


class LocalSync(SyncBase):
    """
    Local sync folder
    """
    def __init__(self, app_data_folder):
        super().__init__(app_data_folder)
        pref = latus.preferences.Preferences(app_data_folder)
        latus.util.make_dirs(pref.get_latus_folder())
        self.observer.schedule(self, pref.get_latus_folder(), recursive=True)

    def get_type(self):
        return 'local'

    def dispatch(self, event):
        self.write_log_status()
        self.call_count += 1
        pref = latus.preferences.Preferences(self.app_data_folder)
        latus.logger.log.info('%s : local dispatch : event : %s : %s' % (pref.get_node_id(), self.call_count, event))

        crypto = latus.crypto.Crypto(pref.get_crypto_key(), pref.get_verbose())
        cloud_folders = latus.folders.CloudFolders(pref.get_cloud_root())

        # created or updated local files
        local_walker = latus.walker.Walker(pref.get_latus_folder())
        for partial_path in local_walker:
            # use the local _file_ name to create the cloud _folder_ where the fernet and metadata reside
            local_full_path = local_walker.full_path(partial_path)
            local_hash, _ = latus.hash.calc_sha512(local_full_path)
            if local_hash:
                # todo: encrypt the hash?
                cloud_fernet_file = os.path.join(cloud_folders.cache, local_hash + self.fernet_extension)
                fs_db = latus.nodedb.NodeDB(cloud_folders.nodedb, pref.get_node_id(), pref.get_public_key(), True)
                fs_updated = False
                while not fs_updated:
                    if fs_db.acquire_lock():
                        most_recent_hash = fs_db.get_most_recent_hash(partial_path)
                        if os.path.exists(local_full_path):
                            if local_hash != most_recent_hash:
                                mtime = datetime.datetime.utcfromtimestamp(os.path.getmtime(local_full_path))
                                size = os.path.getsize(local_full_path)
                                latus.logger.log.info('%s : %s updated %s' % (pref.get_node_id(), local_full_path, local_hash))
                                fs_db.update(latus.miv.next_miv(cloud_folders.miv), pref.get_node_id(), partial_path,
                                             size, local_hash, mtime)
                        if not os.path.exists(cloud_fernet_file):
                            latus.logger.log.info('%s : writing %s (%s)' % (pref.get_node_id(), partial_path, cloud_fernet_file))
                            crypto.compress(pref.get_latus_folder(), partial_path, os.path.abspath(cloud_fernet_file))
                        fs_updated = True
                        fs_db.release_lock()
                    else:
                        time.sleep(random.random(1.0))
            else:
                latus.logger.log.warn('could not calculate hash for %s' % local_full_path)

        # check for local deletions
        fs_db = latus.nodedb.NodeDB(cloud_folders.nodedb, pref.get_node_id(), pref.get_public_key(), True)
        fs_updated = False
        while not fs_updated:
            if fs_db.acquire_lock():
                for partial_path in fs_db.get_paths():
                    local_full_path = os.path.abspath(os.path.join(pref.get_latus_folder(), partial_path))
                    db_fs_info = fs_db.get_latest_file_info(partial_path)
                    if not os.path.exists(local_full_path) and db_fs_info['hash']:
                        latus.logger.log.info('%s : %s deleted' % (pref.get_node_id(), local_full_path))
                        fs_db.update(latus.miv.next_miv(cloud_folders.miv), pref.get_node_id(), partial_path, None, None, None)
                fs_updated = True
                fs_db.release_lock()
            else:
                time.sleep(random.random(1.0))


class CloudSync(SyncBase):
    """
    Cloud Sync folder
    """
    def __init__(self, app_data_folder):
        super().__init__(app_data_folder)

        pref = latus.preferences.Preferences(self.app_data_folder)
        cloud_folders = latus.folders.CloudFolders(pref.get_cloud_root())

        latus.logger.log.info('cloud_nodedb : %s' % cloud_folders.nodedb)
        latus.logger.log.info('cloud_cache : %s' % cloud_folders.cache)
        latus.logger.log.info('cloud_miv : %s' % cloud_folders.miv)

        latus.util.make_dirs(cloud_folders.nodedb)
        latus.util.make_dirs(cloud_folders.cache)
        latus.util.make_dirs(cloud_folders.miv)

        self.observer.schedule(self, cloud_folders.nodedb, recursive=True)

    def get_type(self):
        return 'cloud'

    def dispatch(self, event):
        pref = latus.preferences.Preferences(self.app_data_folder)
        cloud_folders = latus.folders.CloudFolders(pref.get_cloud_root())
        if event is None or 'db-journal' not in event.src_path:
            self.write_log_status()
            self.call_count += 1
            latus.logger.log.info('%s : cloud dispatch : event : %s : %s' % (pref.get_node_id(), self.call_count, event))

            crypto = latus.crypto.Crypto(pref.get_crypto_key(), pref.get_verbose())
            fs_db_this_node = latus.nodedb.NodeDB(cloud_folders.nodedb, pref.get_node_id())
            # for each file path, determine the 'winning' node (which could be this node)
            db_files = glob.glob(os.path.join(cloud_folders.nodedb, '*' + latus.const.DB_EXTENSION))
            looking = True  # set to False when we have a full set of winners
            while looking:
                winners = {}
                any_locked = False
                for db_file in db_files:
                    if not any_locked:
                        file_name = os.path.basename(db_file)
                        db_node_id = file_name.split('.')[0]
                        fs_db = latus.nodedb.NodeDB(cloud_folders.nodedb, db_node_id)
                        if fs_db.get_lock_state():
                            # one of the DBs is locked - we can't use this
                            winners = {}
                            latus.logger.log.info('%s : DB locked' % fs_db.get_node_id())
                            any_locked = True
                        else:
                            for partial_path in fs_db.get_paths():
                                file_info = fs_db.get_latest_file_info(partial_path)
                                file_info['node'] = db_node_id  # this isn't in the db
                                if partial_path in winners:
                                    # got file info that is later than we've seen so far
                                    if file_info['seq'] > winners[partial_path]['seq']:
                                        winners[partial_path] = file_info
                                else:
                                    # init winner for this file
                                    winners[partial_path] = file_info
                if any_locked:
                    time.sleep(random.random())
                else:
                    looking = False  # got a full set of winners

            for partial_path in winners:
                winning_file_info = winners[partial_path]
                local_file_abs_path = os.path.abspath(os.path.join(pref.get_latus_folder(), partial_path))
                if os.path.exists(local_file_abs_path):
                    local_file_hash, _ = latus.hash.calc_sha512(local_file_abs_path)  # todo: get this pre-computed from the db
                else:
                    local_file_hash = None
                if winning_file_info['hash']:
                    if winning_file_info['hash'] != local_file_hash:
                        fs_db_this_node.acquire_lock()  # make expand of new file and update of this DB atomic
                        cloud_fernet_file = os.path.abspath(os.path.join(cloud_folders.cache, winning_file_info['hash'] + self.fernet_extension))
                        latus.logger.log.info('%s : %s changed %s - propagating to %s %s' % (pref.get_node_id(), db_node_id, partial_path, local_file_abs_path, winning_file_info['hash']))
                        expand_ok = crypto.expand(cloud_fernet_file, local_file_abs_path)
                        last_seq = fs_db_this_node.get_last_seq(partial_path)
                        if winning_file_info['seq'] != last_seq:
                            fs_db_this_node.update(winning_file_info['seq'], winning_file_info['originator'],
                                                   winning_file_info['path'], winning_file_info['size'],
                                                   winning_file_info['hash'], winning_file_info['mtime'])
                        fs_db_this_node.release_lock()
                elif local_file_hash:
                    latus.logger.log.info('%s : %s deleted %s' % (pref.get_node_id(), db_node_id, partial_path))
                    fs_db_this_node.acquire_lock()  # make delete of file and update of this DB atomic
                    try:
                        if os.path.exists(local_file_abs_path):
                            send2trash.send2trash(local_file_abs_path)
                    except OSError:
                        # fallback
                        latus.logger.log.warn('%s : send2trash failed on %s' % (pref.get_node_id(), local_file_abs_path))
                    fs_db_this_node.update(winning_file_info['seq'], winning_file_info['originator'],
                                           winning_file_info['path'], None, None, None)
                    fs_db_this_node.release_lock()


class Sync:
    def __init__(self, app_data_folder):
        self.app_data_folder = app_data_folder
        pref = latus.preferences.Preferences(self.app_data_folder)
        latus.logger.log.info('node_id : %s' % pref.get_node_id())
        latus.logger.log.info('local_folder : %s' % pref.get_latus_folder())
        latus.logger.log.info('crypto_key : %s' % pref.get_crypto_key_string())
        latus.logger.log.info('cloud_root : %s' % pref.get_cloud_root())

        self.local_sync = LocalSync(self.app_data_folder)
        self.cloud_sync = CloudSync(self.app_data_folder)

        if pref.get_crypto_key_string() is None:
            # todo: implement getting the key
            pass

    def start(self):
        self.local_sync.start()
        self.cloud_sync.start()

    def scan(self):
        self.local_sync.dispatch(None)
        self.cloud_sync.dispatch(None)

    def request_exit(self):
        pref = latus.preferences.Preferences(self.app_data_folder)
        latus.logger.log.info('%s - sync - request_exit begin' % pref.get_node_id())
        timed_out = self.local_sync.request_exit()
        timed_out |= self.cloud_sync.request_exit()
        latus.logger.log.info('%s - sync - request_exit end' % pref.get_node_id())
        return timed_out

