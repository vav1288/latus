from builtins import property
import os
import shutil
import json
import time
import datetime

import watchdog.observers
import watchdog.events
import send2trash

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
import latus.key_management


class SyncBase(watchdog.events.FileSystemEventHandler):

    def __init__(self, app_data_folder):
        self.sync_count = 0  # for logging and design for testability
        self.app_data_folder = app_data_folder
        self.observer = watchdog.observers.Observer()
        latus.logger.log.info('log_folder : %s' % latus.logger.get_log_folder())
        self.write_log_status()
        super().__init__()

    def get_type(self):
        # type of folder - children provide this - e.g. local, cloud
        assert False

    def do_sync(self):
        self.sync_count += 1

    def request_exit(self):
        pref = latus.preferences.Preferences(self.app_data_folder)
        latus.logger.log.info('%s - %s - request_exit begin' % (pref.get_node_id(), self.get_type()))
        self.observer.stop()
        self.observer.join(latus.const.TIME_OUT)
        latus.logger.log.info('%s - %s - request_exit end' % (pref.get_node_id(), self.get_type()))
        return self.observer.is_alive()

    def start(self):
        self.do_sync()  # rescan entire folder before we 'start' the observer
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
        latus_folder = pref.get_latus_folder()
        latus.util.make_dir(latus_folder)
        self.observer.schedule(self, latus_folder, recursive=True)

    def get_type(self):
        return 'local'

    def dispatch(self, event):
        pref = latus.preferences.Preferences(self.app_data_folder)
        latus.logger.log.info('%s : local dispatch : event : %s : %s' % (pref.get_node_id(), self.sync_count, event))
        self.do_sync()

    def do_sync(self):
        super().do_sync()
        self.write_log_status()
        pref = latus.preferences.Preferences(self.app_data_folder)

        crypto_key = pref.get_crypto_key()
        if crypto_key is None:
            latus.logger.log.info('no crypto_key yet')
            return
        crypto = latus.crypto.Crypto(crypto_key, pref.get_verbose())
        cloud_folders = latus.folders.CloudFolders(pref.get_cloud_root())
        node_id = pref.get_node_id()

        # created or updated local files
        local_walker = latus.walker.Walker(pref.get_latus_folder())
        for partial_path in local_walker:
            local_full_path = local_walker.full_path(partial_path)
            node_db = latus.nodedb.NodeDB(cloud_folders.nodes, node_id, True)
            encrypt, shared, cloud = node_db.get_folder_preferences_from_path(local_full_path)
            local_hash, _ = latus.hash.calc_sha512(local_full_path)
            if local_hash:
                # todo: encrypt the hash?
                cloud_fernet_file = os.path.join(cloud_folders.cache, local_hash + latus.const.ENCRYPTION_EXTENSION)
                most_recent_hash = node_db.get_most_recent_hash(partial_path)
                if os.path.exists(local_full_path):
                    if local_hash != most_recent_hash:
                        mtime = datetime.datetime.utcfromtimestamp(os.path.getmtime(local_full_path))
                        size = os.path.getsize(local_full_path)
                        latus.logger.log.info('%s : %s updated, size=%s, hash=%s' %
                                              (node_id, local_full_path, size, local_hash))
                        node_db.update(latus.miv.get_miv(), node_id, partial_path, size, local_hash, mtime)
                        latus.logger.log.info('%s : %s preferences : encrypt=%s, shared=%s, cloud=%s' %
                                              (node_id, local_full_path, encrypt, shared, cloud))
                if encrypt:
                    if not os.path.exists(cloud_fernet_file):
                        latus.logger.log.info('%s : writing %s' % (node_id, cloud_fernet_file))
                        crypto.encrypt(local_full_path, os.path.abspath(cloud_fernet_file))
                else:
                    destination = os.path.join(cloud_folders.cache, local_hash + latus.const.UNENCRYPTED_EXTENSION)
                    if not os.path.exists(destination):
                        shutil.copy2(local_full_path, destination)
            else:
                latus.logger.log.warn('could not calculate hash for %s' % local_full_path)

        # check for local deletions
        node_db = latus.nodedb.NodeDB(cloud_folders.nodes, pref.get_node_id(), True)
        for partial_path in node_db.get_paths():
            local_full_path = os.path.abspath(os.path.join(pref.get_latus_folder(), partial_path))
            db_fs_info = node_db.get_latest_file_info(partial_path)
            if not os.path.exists(local_full_path) and db_fs_info['hash']:
                latus.logger.log.info('%s : %s deleted' % (pref.get_node_id(), local_full_path))
                node_db.update(latus.miv.get_miv(), pref.get_node_id(), partial_path, None, None, None)


class CloudSync(SyncBase):
    """
    Cloud Sync folder
    """
    def __init__(self, app_data_folder):
        super().__init__(app_data_folder)

        pref = latus.preferences.Preferences(self.app_data_folder)
        cloud_folders = latus.folders.CloudFolders(pref.get_cloud_root())

        latus.logger.log.info('cloud_nodedb : %s' % cloud_folders.nodes)
        latus.logger.log.info('cloud_cache : %s' % cloud_folders.cache)

        latus.util.make_dir(pref.get_cloud_root())
        # make_dir make the folder hidden, even if it already exists
        latus.util.make_dir(cloud_folders.latus, True)
        latus.util.make_dir(cloud_folders.nodes, True)
        latus.util.make_dir(cloud_folders.cache, True)

        self.observer.schedule(self, cloud_folders.nodes, recursive=True)

    def get_type(self):
        return 'cloud'

    def dispatch(self, event):
        pref = latus.preferences.Preferences(self.app_data_folder)
        cloud_folders = latus.folders.CloudFolders(pref.get_cloud_root())
        this_node_db = latus.nodedb.NodeDB(cloud_folders.nodes, pref.get_node_id())
        event_node_id = latus.nodedb.get_node_id_from_db_file_path(event.src_path)
        # if this dispatch was caused by an even on our own DB, ignore it
        if event_node_id != this_node_db.get_node_id() and 'db-journal' not in event.src_path:
            latus.logger.log.info('%s : cloud dispatch : event : %s : %s' % (pref.get_node_id(), self.sync_count, event))
            self.do_sync()

    def do_sync(self):
        super().do_sync()
        pref = latus.preferences.Preferences(self.app_data_folder)
        cloud_folders = latus.folders.CloudFolders(pref.get_cloud_root())
        this_node_db = latus.nodedb.NodeDB(cloud_folders.nodes, pref.get_node_id())
        self.write_log_status()

        crypto_key = pref.get_crypto_key()
        if crypto_key is None:
            latus.logger.log.info('no crypto_key yet')
            return
        crypto = latus.crypto.Crypto(crypto_key, pref.get_verbose())
        # for each file path, determine the 'winning' node (which could be this node)
        winners = {}
        for db_file in latus.nodedb.get_existing_nodes(cloud_folders.nodes):
            file_name = os.path.basename(db_file)
            db_node_id = file_name.split('.')[0]
            fs_db = latus.nodedb.NodeDB(cloud_folders.nodes, db_node_id)
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

        for partial_path in winners:
            winning_file_info = winners[partial_path]
            local_file_path = os.path.join(pref.get_latus_folder(), partial_path)
            if os.path.exists(local_file_path):
                local_file_hash, _ = latus.hash.calc_sha512(local_file_path)  # todo: get this pre-computed from the db
            else:
                local_file_hash = None
            if winning_file_info['hash']:
                if winning_file_info['hash'] != local_file_hash:
                    cloud_fernet_file = os.path.join(cloud_folders.cache,
                                                     winning_file_info['hash'] + latus.const.ENCRYPTION_EXTENSION)
                    latus.logger.log.info('%s : %s changed %s - propagating to %s %s' %
                                          (pref.get_node_id(), db_node_id, partial_path, local_file_path,
                                           winning_file_info['hash']))
                    encrypt, shared, cloud = this_node_db.get_folder_preferences_from_path(local_file_path)
                    if encrypt:
                        expand_ok = crypto.decrypt(cloud_fernet_file, local_file_path)
                    else:
                        cloud_file = os.path.join(cloud_folders.cache,
                                                  winning_file_info['hash'] + latus.const.UNENCRYPTED_EXTENSION)
                        shutil.copy2(cloud_file, local_file_path)
                    last_seq = this_node_db.get_last_seq(partial_path)
                    if winning_file_info['seq'] != last_seq:
                        this_node_db.update(winning_file_info['seq'], winning_file_info['originator'],
                                            winning_file_info['path'], winning_file_info['size'],
                                            winning_file_info['hash'], winning_file_info['mtime'])
            elif local_file_hash:
                latus.logger.log.info('%s : %s deleted %s' % (pref.get_node_id(), db_node_id, partial_path))
                try:
                    if os.path.exists(local_file_path):
                        send2trash.send2trash(local_file_path)
                except OSError:
                    # fallback
                    latus.logger.log.warn('%s : send2trash failed on %s' % (pref.get_node_id(), local_file_path))
                this_node_db.update(winning_file_info['seq'], winning_file_info['originator'],
                                    winning_file_info['path'], None, None, None)


class Sync:
    def __init__(self, app_data_folder):
        self.app_data_folder = app_data_folder
        pref = latus.preferences.Preferences(self.app_data_folder)
        latus.logger.log.info('node_id : %s' % pref.get_node_id())
        latus.logger.log.info('local_folder : %s' % pref.get_latus_folder())
        latus.logger.log.info('crypto_key : %s' % pref.get_crypto_key())
        latus.logger.log.info('cloud_root : %s' % pref.get_cloud_root())

        self.local_sync = LocalSync(self.app_data_folder)
        self.cloud_sync = CloudSync(self.app_data_folder)

    def start(self):
        self.local_sync.start()
        self.cloud_sync.start()

    def request_exit(self):
        pref = latus.preferences.Preferences(self.app_data_folder)
        cloud_folder = latus.folders.CloudFolders(pref.get_cloud_root())
        node_id = pref.get_node_id()
        node = latus.nodedb.NodeDB(cloud_folder.nodes, node_id)
        latus.logger.log.info('%s - sync - request_exit begin' % node_id)
        timed_out = self.local_sync.request_exit()
        timed_out |= self.cloud_sync.request_exit()
        node.set_login(False)
        node.set_heartbeat()
        latus.logger.log.info('%s - sync - request_exit end' % node_id)
        return timed_out

