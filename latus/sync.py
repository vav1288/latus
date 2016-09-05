
import os
import shutil
import time
import datetime
import sys
import collections

import watchdog.observers
import watchdog.events
import send2trash

import latus.logger
import latus.util
from latus.const import FileSystemEvent, DetectionSource, ChangeAttributes, TIME_OUT, FILTER_TIME_OUT, ENCRYPTION_EXTENSION, \
    UNENCRYPTED_EXTENSION
import latus.preferences
import latus.walker
import latus.hash
import latus.crypto
import latus.nodedb
import latus.miv
import latus.folders
import latus.key_management


FilterEvent = collections.namedtuple('FilterEvent', ['path', 'event', 'timestamp'])

# todo: would it be better to use watchdog.events.LoggingEventHandler instead of FileSystemEventHandler?


class SyncBase(watchdog.events.FileSystemEventHandler):
    def __init__(self, app_data_folder, filter_events):
        self.app_data_folder = app_data_folder
        self.filter_events = filter_events
        self.observer = watchdog.observers.Observer()
        pref = latus.preferences.Preferences(self.app_data_folder)
        latus.logger.log.info('log_folder : %s , %s' % (pref.get_node_id(), latus.logger.get_log_folder()))
        super().__init__()

    def get_type(self):
        # type of folder - children provide this - e.g. local, cloud
        assert False

    def request_exit(self):
        pref = latus.preferences.Preferences(self.app_data_folder)
        latus.logger.log.info('%s - %s - request_exit begin' % (pref.get_node_id(), self.get_type()))
        try:
            self.observer.stop()
        except SystemError as e:
            # todo: put this in util.py
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback_details = {
                'filename': exc_traceback.tb_frame.f_code.co_filename,
                'lineno': exc_traceback.tb_lineno,
                'name': exc_traceback.tb_frame.f_code.co_name,
                'type': exc_type.__name__,
            }
            latus.logger.log.error(str(traceback_details) + ':' + str(e))
        self.observer.join(TIME_OUT)

        if len(self.filter_events) > 0:
            for filter_event in self.filter_events:
                latus.logger.log.warn('%s : remaining filter event : %s' % (pref.get_node_id(), str(filter_event)))

        latus.logger.log.info('%s - %s - request_exit end' % (pref.get_node_id(), self.get_type()))
        if self.observer.is_alive():
            latus.logger.log.error('%s - %s - request_exit failed to stop observer' % (pref.get_node_id(), self.get_type()))
        return self.observer.is_alive()

    def start_observer(self):
        self.observer.start()

    def add_filter_event(self, path, event):
        self.filter_events.append(FilterEvent(path, event, time.time()))

    # Returns True if path is found in the filter list.  Also removes that path entry from the filter list.
    def filtered(self, event):
        now = time.time()
        pref = latus.preferences.Preferences(self.app_data_folder)

        # remove any old events that somehow timed out
        removes = []
        for filter_event in self.filter_events:
            if now > filter_event.timestamp + FILTER_TIME_OUT:
                removes.append(filter_event)
        for remove in removes:
            latus.logger.log.warn('%s : filter event timed out %s' % (pref.get_node_id(), str(remove)))
            self.filter_events.remove(remove)

        # Look for this path in events.  If found, remove it and return True.
        remove = None
        for filter_event in self.filter_events:
            if filter_event.path == event.src_path:
                remove = filter_event
                break
        if remove is not None:
            latus.logger.sync_filtered_log(pref.get_node_id(), str(remove))
            self.filter_events.remove(remove)
            return True

        return False

    def get_node_id(self):
        pref = latus.preferences.Preferences(self.app_data_folder)
        return pref.get_node_id()


class LocalSync(SyncBase):
    """
    Local sync folder
    """
    def __init__(self, app_data_folder, filter_events):
        super().__init__(app_data_folder, filter_events)
        pref = latus.preferences.Preferences(app_data_folder)
        latus_folder = pref.get_latus_folder()
        latus.util.make_dir(latus_folder)
        self.observer.schedule(self, latus_folder, recursive=True)

    def get_type(self):
        return 'local'

    def on_created(self, watchdog_event):
        if not watchdog_event.is_directory:
            if not self.filtered(watchdog_event):
                src_path = watchdog_event.src_path
                file_hash = self.fill_cache(src_path)
                self.write_db(src_path, FileSystemEvent.created, DetectionSource.watchdog, file_hash)

    def on_deleted(self, event):
        if not event.is_directory:
            latus.logger.log.info('%s : local on_deleted event : %s' % (self.get_node_id(), event))
            if not self.filtered(event):
                # todo: remove from cache
                self.write_db(event.src_path, FileSystemEvent.deleted, DetectionSource.watchdog, None)

    def on_modified(self, event):
        if not event.is_directory:
            latus.logger.log.info('%s : local on_modified event : %s' % (self.get_node_id(), event))
            if not self.filtered(event):
                file_hash = self.fill_cache(event.src_path)
                self.write_db(event.src_path, FileSystemEvent.modified, DetectionSource.watchdog, file_hash)

    def on_moved(self, event):
        latus.logger.log.warn('on_moved not yet implemented')

    def fill_cache(self, full_path):
        pref = latus.preferences.Preferences(self.app_data_folder)
        node_id = pref.get_node_id()
        cloud_folders = latus.folders.CloudFolders(pref.get_cloud_root())
        node_db = latus.nodedb.NodeDB(cloud_folders.nodes, node_id)
        encrypt, shared, cloud = node_db.get_folder_preferences_from_path(full_path)
        hash, _ = latus.hash.calc_sha512(full_path)
        if encrypt:
            crypto_key = pref.get_crypto_key()
            if crypto_key is None:
                latus.logger.log.error('no crypto_key yet')
                return
            cloud_fernet_file = os.path.join(cloud_folders.cache, hash + ENCRYPTION_EXTENSION)
            crypto = latus.crypto.Crypto(crypto_key, pref.get_verbose())
            if not os.path.exists(cloud_fernet_file):
                latus.logger.log.info('%s : file_write , %s' % (node_id, cloud_fernet_file))
                crypto.encrypt(full_path, os.path.abspath(cloud_fernet_file))
        else:
            destination = os.path.join(cloud_folders.cache, hash + UNENCRYPTED_EXTENSION)
            if not os.path.exists(destination):
                shutil.copy2(full_path, destination)
        return hash

    # todo: encrypt the hash?
    def write_db(self, full_path, filesystem_event_type, detection_source, file_hash):
        pref = latus.preferences.Preferences(self.app_data_folder)
        cloud_folders = latus.folders.CloudFolders(pref.get_cloud_root())
        latus_path = full_path.replace(pref.get_latus_folder() + os.sep, '')
        node_id = pref.get_node_id()
        if os.path.exists(full_path):
            mtime = datetime.datetime.utcfromtimestamp(os.path.getmtime(full_path))
            size = os.path.getsize(full_path)
        else:
            mtime = None
            size = None
        miv = latus.miv.get_miv(node_id)
        latus.logger.sync_log(node_id, miv, filesystem_event_type, full_path, detection_source, size, file_hash, mtime)
        node_db = latus.nodedb.NodeDB(cloud_folders.nodes, node_id)
        most_recent_hash = node_db.get_most_recent_hash(latus_path)
        if most_recent_hash != file_hash:
            node_db.update(miv, node_id, int(filesystem_event_type), int(detection_source),
                           latus_path, size, file_hash, mtime)

    def fs_scan(self, detection_source):
        pref = latus.preferences.Preferences(self.app_data_folder)
        cloud_folders = latus.folders.CloudFolders(pref.get_cloud_root())
        node_id = pref.get_node_id()
        node_db = latus.nodedb.NodeDB(cloud_folders.nodes, node_id)
        local_walker = latus.walker.Walker(pref.get_latus_folder())
        for partial_path in local_walker:
            local_full_path = local_walker.full_path(partial_path)
            if os.path.exists(local_full_path):
                local_hash, _ = latus.hash.calc_sha512(local_full_path)
                if local_hash:
                    most_recent_hash = node_db.get_most_recent_hash(partial_path)
                    if most_recent_hash is None:
                        file_system_event = FileSystemEvent.created
                    else:
                        file_system_event = FileSystemEvent.modified
                    if local_hash != most_recent_hash:
                        mtime = datetime.datetime.utcfromtimestamp(os.path.getmtime(local_full_path))
                        size = os.path.getsize(local_full_path)
                        miv = latus.miv.get_miv(node_id)
                        latus.logger.sync_log(node_id, file_system_event, miv, partial_path,
                                              detection_source, size, local_hash, mtime)
                        self.fill_cache(local_full_path)
                        self.add_filter_event(node_db.get_database_file_name(), FileSystemEvent.modified)
                        node_db.update(miv, node_id, int(file_system_event),
                                       int(detection_source), partial_path, size, local_hash, mtime)
                else:
                    latus.logger.log.warn('could not calculate hash for %s' % local_full_path)

        node_db = latus.nodedb.NodeDB(cloud_folders.nodes, pref.get_node_id())
        for partial_path in node_db.get_paths():
            full_path = os.path.join(pref.get_latus_folder(), partial_path)
            if not os.path.exists(full_path):
                latus.logger.log.info('%s : %s deleted' % (pref.get_node_id(), partial_path))
                node_id = pref.get_node_id()
                self.add_filter_event(node_db.get_database_file_name(), FileSystemEvent.modified)
                most_recent_hash = node_db.get_most_recent_hash(partial_path)
                if most_recent_hash is not None:
                    miv = latus.miv.get_miv(node_id)
                    latus.logger.sync_log(node_id, FileSystemEvent.deleted, miv, partial_path,
                                          detection_source, None, None, None)
                    node_db.update(miv, node_id, int(FileSystemEvent.deleted),
                                   int(DetectionSource.initial_scan), partial_path, None, None, None)


class CloudSync(SyncBase):
    """
    Cloud Sync folder
    """
    def __init__(self, app_data_folder, filter_events):
        super().__init__(app_data_folder, filter_events)

        pref = latus.preferences.Preferences(self.app_data_folder)
        cloud_folders = latus.folders.CloudFolders(pref.get_cloud_root())

        latus.logger.log.info('cloud_nodedb : %s' % cloud_folders.nodes)
        latus.logger.log.info('cloud_cache : %s' % cloud_folders.cache)

        latus.util.make_dir(pref.get_cloud_root())
        # make_dir make the folder hidden, even if it already exists
        latus.util.make_dir(cloud_folders.latus, True)
        latus.util.make_dir(cloud_folders.nodes, True)
        latus.util.make_dir(cloud_folders.cache, True)

        # make the node DB if it isn't already there
        pref = latus.preferences.Preferences(self.app_data_folder)
        node_id = pref.get_node_id()
        cloud_folders = latus.folders.CloudFolders(pref.get_cloud_root())
        latus.nodedb.NodeDB(cloud_folders.nodes, node_id, True)

        self.observer.schedule(self, cloud_folders.nodes, recursive=True)

    def get_type(self):
        return 'cloud'

    def on_any_event(self, event):
        pref = latus.preferences.Preferences(self.app_data_folder)
        cloud_folders = latus.folders.CloudFolders(pref.get_cloud_root())
        this_node_db = latus.nodedb.NodeDB(cloud_folders.nodes, pref.get_node_id())
        event_node_id = latus.nodedb.get_node_id_from_db_file_path(event.src_path)
        # if this dispatch was caused by an event on our own DB, ignore it
        if not event.is_directory and event_node_id != this_node_db.get_node_id() and 'db-journal' not in event.src_path:
            latus.logger.log.info('%s : cloud dispatch : event : %s' % (pref.get_node_id(), event))
            self.cloud_sync(DetectionSource.watchdog)

    def cloud_sync(self, detection_source):
        # todo: it would be nice to have the detection_source be in the node DB when we copy it over, but
        # currently we copy over the original detection source, which is also valuable.  We do log
        # the detection_source though.  Maybe that's enough.
        pref = latus.preferences.Preferences(self.app_data_folder)
        cloud_folders = latus.folders.CloudFolders(pref.get_cloud_root())
        this_node_db = latus.nodedb.NodeDB(cloud_folders.nodes, pref.get_node_id())

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

        latus.logger.log.info('%s : len(winners) = %d' % (pref.get_node_id(), len(winners)))
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
                                                     winning_file_info['hash'] + ENCRYPTION_EXTENSION)
                    latus.logger.log.info('%s : %s : %s changed %s - propagating to %s %s' %
                                          (pref.get_node_id(), detection_source, db_node_id, partial_path,
                                           local_file_path, winning_file_info['hash']))
                    encrypt, shared, cloud = this_node_db.get_folder_preferences_from_path(local_file_path)

                    latus.logger.log.info('%s : muting %s' % (pref.get_node_id(), local_file_path))
                    self.add_filter_event(local_file_path, FileSystemEvent.any)  # is actually create or modify ... will be correct when we have this class use the proper watchdog events
                    if encrypt:
                        expand_ok = crypto.decrypt(cloud_fernet_file, local_file_path)
                        # todo: set mtime
                    else:
                        cloud_file = os.path.join(cloud_folders.cache,
                                                  winning_file_info['hash'] + UNENCRYPTED_EXTENSION)
                        shutil.copy2(cloud_file, local_file_path)
                    last_seq = this_node_db.get_last_seq(partial_path)
                    if winning_file_info['seq'] != last_seq:
                        this_node_db.update(winning_file_info['seq'], winning_file_info['originator'],
                                            winning_file_info['event'], winning_file_info['detection'],
                                            winning_file_info['path'], winning_file_info['size'],
                                            winning_file_info['hash'], winning_file_info['mtime'])
            elif local_file_hash:
                self.add_filter_event(local_file_path, FileSystemEvent.deleted)
                latus.logger.log.info('%s : %s : %s deleted %s' % (pref.get_node_id(), detection_source, db_node_id, partial_path))
                try:
                    if os.path.exists(local_file_path):
                        send2trash.send2trash(local_file_path)
                except OSError:
                    # fallback
                    latus.logger.log.warn('%s : send2trash failed on %s' % (pref.get_node_id(), local_file_path))
                this_node_db.update(winning_file_info['seq'], winning_file_info['originator'],
                                    winning_file_info['event'], winning_file_info['detection'],
                                    winning_file_info['path'], None, None, None)

    def fs_scan(self, detection_source):
        pass


class Sync:
    def __init__(self, app_data_folder):
        self.app_data_folder = app_data_folder
        pref = latus.preferences.Preferences(self.app_data_folder)
        node_id = pref.get_node_id()
        latus.logger.log.info('node_id : %s' % node_id)
        latus.logger.log.info('local_folder : %s , %s' % (node_id, pref.get_latus_folder()))
        latus.logger.log.info('crypto_key : %s , %s' % (node_id, pref.get_crypto_key()))
        latus.logger.log.info('cloud_root : %s , %s' % (node_id, pref.get_cloud_root()))

        self.filter_events = []

        self.local_sync = LocalSync(self.app_data_folder, self.filter_events)
        self.cloud_sync = CloudSync(self.app_data_folder, self.filter_events)

    def start(self):
        self.local_sync.fs_scan(DetectionSource.initial_scan)
        self.cloud_sync.cloud_sync(DetectionSource.initial_scan)
        self.local_sync.start_observer()
        self.cloud_sync.start_observer()

    def poll(self):
        self.local_sync.fs_scan(DetectionSource.periodic_poll)
        self.cloud_sync.cloud_sync(DetectionSource.periodic_poll)

    def request_exit(self):
        pref = latus.preferences.Preferences(self.app_data_folder)
        cloud_folder = latus.folders.CloudFolders(pref.get_cloud_root())
        node_id = pref.get_node_id()
        node = latus.nodedb.NodeDB(cloud_folder.nodes, node_id)
        latus.logger.log.info('%s - sync - request_exit begin' % node_id)
        timed_out = self.local_sync.request_exit()
        timed_out |= self.cloud_sync.request_exit()
        node.set_login(False)
        latus.logger.log.info('%s - sync - request_exit end' % node_id)
        return timed_out

