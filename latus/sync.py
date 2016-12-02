
import os
import shutil
import time
import datetime
import collections
from functools import wraps

import watchdog.observers
import watchdog.events
import send2trash

import latus.logger
import latus.util
import latus.const
from latus.const import LatusFileSystemEvent, DetectionSource, ChangeAttributes, TIME_OUT, FILTER_TIME_OUT, ENCRYPTION_EXTENSION, UNENCRYPTED_EXTENSION
import latus.preferences
import latus.walker
import latus.hash
import latus.crypto
import latus.nodedb
import latus.miv
import latus.folders
import latus.key_management
import latus.gui
import latus.activity_timer
import latus.usage


FilterEvent = collections.namedtuple('FilterEvent', ['path', 'event', 'timestamp'])

# todo: would it be better to use watchdog.events.LoggingEventHandler instead of FileSystemEventHandler?


def activity_trigger(func):
    """
    decorator that adds activity triggers
    """
    @wraps(func)
    def do_triggers(self, *args, **kwargs):
        self.active_timer.enter_trigger(func.__name__)
        r = func(self, *args, **kwargs)
        self.active_timer.exit_trigger(func.__name__)
        return r
    return do_triggers


class SyncBase(watchdog.events.FileSystemEventHandler):
    def __init__(self, app_data_folder, filter_events):
        self.app_data_folder = app_data_folder
        self.filter_events = filter_events

        self.observer = watchdog.observers.Observer()
        # used to determine of this sync node is currently considered active
        pref = latus.preferences.Preferences(self.app_data_folder)

        self.active_timer = latus.activity_timer.ActivityTimer(3, pref.get_node_id() + '_' + self.get_type())

        super().__init__()

    def get_type(self):
        # type of folder - children provide this - e.g. local, cloud
        assert False

    @activity_trigger
    def request_exit(self):
        pref = latus.preferences.Preferences(self.app_data_folder)
        latus.logger.log.info('%s - %s - request_exit begin' % (pref.get_node_id(), self.get_type()))
        try:
            self.observer.stop()
        except SystemError as e:
            latus.logger.log.exception('error stopping observer : %s' % str(self.get_type()))
        self.observer.join(TIME_OUT)

        if len(self.filter_events) > 0:
            for filter_event in self.filter_events:
                latus.logger.log.warn('%s : remaining filter event : %s' % (pref.get_node_id(), str(filter_event)))

        latus.logger.log.info('%s - %s - request_exit end' % (pref.get_node_id(), self.get_type()))
        if self.observer.is_alive():
            latus.logger.log.error('%s - %s - request_exit failed to stop observer' % (pref.get_node_id(), self.get_type()))

        self.active_timer.reset()
        return self.observer.is_alive()

    @activity_trigger
    def start_observer(self):

        # clear any pending filter events
        for event in self.filter_events:
            try:
                self.filter_events.remove(event)
            except ValueError:
                latus.logger.log.info('error in clearing events : %s' % str(event))

        self.observer.start()

    def add_filter_event(self, path, latus_file_system_event):
        pref = latus.preferences.Preferences(self.app_data_folder)
        latus.logger.log.info('%s : add_filter_event : %s : %s' % (pref.get_node_id(), path, str(latus_file_system_event)))
        self.filter_events.append(FilterEvent(path, latus_file_system_event, time.time()))

    # Returns True if path is found in the filter list.  Also removes that path entry from the filter list.
    def filtered(self, watchdog_event):
        now = time.time()
        pref = latus.preferences.Preferences(self.app_data_folder)

        # remove any old events that somehow timed out
        events_to_remove = []
        for filter_event in self.filter_events:
            if now > filter_event.timestamp + FILTER_TIME_OUT:
                events_to_remove.append(filter_event)
        for event_to_remove in events_to_remove:
            latus.logger.log.warn('%s : filter event timed out %s' % (pref.get_node_id(), str(event_to_remove)))
            try:
                self.filter_events.remove(event_to_remove)
            except ValueError:
                # it's possible another thread had removed this
                latus.logger.log.info('%s already removed' % str(event_to_remove))

        # Look for this path in events.  If found, remove it and return True.
        event_to_remove = None
        for filter_event in self.filter_events:
            if os.path.normpath(filter_event.path) == os.path.normpath(watchdog_event.src_path):
                event_to_remove = filter_event
                break
        if event_to_remove is not None:
            latus.logger.log.info('filtered : %s : %s' % (pref.get_node_id(), str(event_to_remove)))
            self.filter_events.remove(event_to_remove)
            return True

        return False

    def get_node_id(self):
        pref = latus.preferences.Preferences(self.app_data_folder)
        return pref.get_node_id()

    def is_active(self):
        return self.active_timer.is_active()


class LocalSync(SyncBase):
    """
    Local sync folder
    """
    def __init__(self, app_data_folder, filter_events):
        super().__init__(app_data_folder, filter_events)
        pref = latus.preferences.Preferences(app_data_folder)
        self.latus_folder = pref.get_latus_folder()
        latus.util.make_dir(self.latus_folder)
        self.observer.schedule(self, self.latus_folder, recursive=True)

    def get_type(self):
        return 'local'

    # todo: make these logs DRY

    @activity_trigger
    def on_created(self, watchdog_event):
        if watchdog_event.is_directory:
            latus.logger.log.debug(watchdog_event)
        else:
            if self.filtered(watchdog_event):
                latus.logger.log.info('%s : filtered local on_created event : %s' % (self.get_node_id(), str(watchdog_event)))
            else:
                latus.logger.log.info('%s : local on_created event : %s' % (self.get_node_id(), str(watchdog_event)))
                src_path = watchdog_event.src_path
                file_hash = self.__fill_cache(src_path)
                self.__write_db(src_path, None, LatusFileSystemEvent.created, DetectionSource.watchdog, file_hash)

    @activity_trigger
    def on_deleted(self, watchdog_event):
        if watchdog_event.is_directory:
            latus.logger.log.debug(watchdog_event)
        else:
            if self.filtered(watchdog_event):
                latus.logger.log.info('%s : filtered local on_deleted event : %s' % (self.get_node_id(), str(watchdog_event)))
            else:
                latus.logger.log.info('%s : local on_deleted event : %s' % (self.get_node_id(), str(watchdog_event)))
                # todo: remove from cache
                self.__write_db(watchdog_event.src_path, None, LatusFileSystemEvent.deleted, DetectionSource.watchdog, None)

    @activity_trigger
    def on_modified(self, watchdog_event):
        if watchdog_event.is_directory:
            latus.logger.log.debug(watchdog_event)
        else:
            if self.filtered(watchdog_event):
                latus.logger.log.info('%s : filtered local on_modified event : %s' % (self.get_node_id(), str(watchdog_event)))
            else:
                latus.logger.log.info('%s : local on_modified event : %s' % (self.get_node_id(), str(watchdog_event)))
                file_hash = self.__fill_cache(watchdog_event.src_path)
                self.__write_db(watchdog_event.src_path, None, LatusFileSystemEvent.modified, DetectionSource.watchdog, file_hash)

    @activity_trigger
    def on_moved(self, watchdog_event):
        if watchdog_event.is_directory:
            latus.logger.log.debug(watchdog_event)
        else:
            if self.filtered(watchdog_event):
                latus.logger.log.info('%s : filtered local on_moved event : %s' % (self.get_node_id(), str(watchdog_event)))
            else:
                latus.logger.log.info('%s : local on_moved event : %s' % (self.get_node_id(), str(watchdog_event)))

                # for move events the dest is an absolute path - we need just the partial path
                src_path = watchdog_event.src_path.replace(self.latus_folder, '')
                if src_path[0] == os.sep:
                    # remove leading /
                    src_path = src_path[1:]

                file_hash, _ = latus.hash.calc_sha512(watchdog_event.dest_path)
                self.__write_db(watchdog_event.dest_path, src_path, LatusFileSystemEvent.moved, DetectionSource.watchdog, file_hash)

    def __fill_cache(self, full_path):
        pref = latus.preferences.Preferences(self.app_data_folder)
        node_id = pref.get_node_id()
        cloud_folders = latus.folders.CloudFolders(pref.get_cloud_root())
        node_db = latus.nodedb.NodeDB(cloud_folders.nodes, node_id)
        partial_path = os.path.relpath(full_path, pref.get_latus_folder())
        encrypt, shared, cloud = node_db.get_folder_preferences_from_path(partial_path)
        hash, _ = latus.hash.calc_sha512(full_path)
        if encrypt:
            crypto_key = pref.get_crypto_key()
            if crypto_key is None:
                latus.logger.log.fatal('No Latus Key - please reinitialize the preferences - exiting')
                return None
            if hash is None:
                latus.logger.log.warning('could not get hash for %s' % full_path)
            else:
                cloud_fernet_file = os.path.join(cloud_folders.cache, hash + ENCRYPTION_EXTENSION)
                crypto = latus.crypto.Crypto(crypto_key, pref.get_node_id())
                if not os.path.exists(cloud_fernet_file):
                    latus.logger.log.info('%s : file_write , %s' % (node_id, cloud_fernet_file))
                    crypto.encrypt(full_path, os.path.abspath(cloud_fernet_file))
        else:
            destination = os.path.join(cloud_folders.cache, hash + UNENCRYPTED_EXTENSION)
            if not os.path.exists(destination):
                shutil.copy2(full_path, destination)
        return hash

    # todo: encrypt the hash?
    def __write_db(self, full_path, src_path, filesystem_event_type, detection_source, file_hash):
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
        self.sync_log(node_id, miv, filesystem_event_type, full_path, detection_source, size, file_hash, mtime)
        node_db = latus.nodedb.NodeDB(cloud_folders.nodes, node_id)
        most_recent_hash = node_db.get_most_recent_hash(latus_path)
        if most_recent_hash != file_hash:
            node_db.update(miv, node_id, int(filesystem_event_type), int(detection_source),
                           latus_path, src_path, size, file_hash, mtime, False)

    @activity_trigger
    def fs_scan(self, detection_source):
        latus.logger.log.info('starting fs_scan')
        pref = latus.preferences.Preferences(self.app_data_folder)
        cloud_folders = latus.folders.CloudFolders(pref.get_cloud_root())
        this_node_id = pref.get_node_id()
        node_db = latus.nodedb.NodeDB(cloud_folders.nodes, this_node_id)
        local_walker = latus.walker.Walker(pref.get_latus_folder())
        src_path = None  # no moves in file system scan
        for partial_path in local_walker:
            local_full_path = local_walker.full_path(partial_path)
            if os.path.exists(local_full_path):
                local_hash, _ = latus.hash.calc_sha512(local_full_path)
                if local_hash:
                    most_recent_hash = node_db.get_most_recent_hash(partial_path)
                    if most_recent_hash is None:
                        file_system_event = LatusFileSystemEvent.created
                    else:
                        file_system_event = LatusFileSystemEvent.modified
                    if local_hash != most_recent_hash:
                        mtime = datetime.datetime.utcfromtimestamp(os.path.getmtime(local_full_path))
                        size = os.path.getsize(local_full_path)
                        miv = latus.miv.get_miv(this_node_id)
                        self.sync_log(this_node_id, file_system_event, miv, partial_path, detection_source, size, local_hash, mtime)
                        self.__fill_cache(local_full_path)
                        self.add_filter_event(node_db.get_database_file_abs_path(), LatusFileSystemEvent.modified)
                        node_db.update(miv, this_node_id, int(file_system_event),
                                       int(detection_source), partial_path, src_path, size, local_hash, mtime, False)
                else:
                    latus.logger.log.warn('%s : could not calculate hash for %s' % (this_node_id, local_full_path))

        if False:
            for partial_path in node_db.get_paths():
                full_path = os.path.join(pref.get_latus_folder(), partial_path)
                if not os.path.exists(full_path):
                    most_recent_hash = node_db.get_most_recent_hash(partial_path)
                    if most_recent_hash is not None:
                        if node_db.any_pendings(partial_path):
                            latus.logger.log.warning('%s : there are still pendings for %s' % (this_node_id, partial_path))
                        else:
                            latus.logger.log.info('%s : %s deleted' % (this_node_id, partial_path))
                            miv = latus.miv.get_miv(this_node_id)
                            self.sync_log(this_node_id, LatusFileSystemEvent.deleted, miv, partial_path, detection_source, None, None, None)
                            self.add_filter_event(node_db.get_database_file_abs_path(), LatusFileSystemEvent.modified)
                            node_db.update(miv, this_node_id, int(LatusFileSystemEvent.deleted),
                                           int(detection_source), partial_path, src_path, None, None, None, True)

    # todo: get rid of this - it makes the line number irrelevant
    def sync_log(self, node_id, file_system_event, miv, file_path, detection_source, size, local_hash, mtime):
        latus.logger.log.info('sync : %s , %s , %s , "%s" , %s , %s , %s , %s' %
                              (node_id, str(file_system_event), str(miv), file_path, detection_source, size, local_hash, mtime))


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

    @activity_trigger
    def on_any_event(self, event):
        pref = latus.preferences.Preferences(self.app_data_folder)
        if self.filtered(event):
            latus.logger.log.info('%s : filtered cloud on_any_event : %s' % (pref.get_node_id(), str(event)))
        else:
            latus.logger.log.info('%s : cloud on_any_event : %s' % (pref.get_node_id(), str(event)))
            cloud_folders = latus.folders.CloudFolders(pref.get_cloud_root())
            this_node_db = latus.nodedb.NodeDB(cloud_folders.nodes, pref.get_node_id())
            event_node_id = latus.nodedb.get_node_id_from_db_file_path(event.src_path)
            # if this dispatch was caused by an event on our own DB, ignore it
            if not event.is_directory and event_node_id != this_node_db.get_node_id() and 'db-journal' not in event.src_path:
                latus.logger.log.info('%s : cloud dispatch : event : %s' % (pref.get_node_id(), event))
                self.cloud_sync(DetectionSource.watchdog)

    @activity_trigger
    def cloud_sync(self, detection_source):
        pref = latus.preferences.Preferences(self.app_data_folder)
        cloud_folders = latus.folders.CloudFolders(pref.get_cloud_root())
        this_node_db = latus.nodedb.NodeDB(cloud_folders.nodes, pref.get_node_id())

        # ensure this node's DB has all the entries that other node's DBs have
        for db_node_id in latus.nodedb.get_existing_nodes(cloud_folders.nodes):
            if db_node_id != this_node_db.get_node_id():
                latus.nodedb.sync_dbs(cloud_folders.nodes, db_node_id, this_node_db.get_node_id())

        for info in this_node_db.get_last_seqs_info():
            local_file_path = os.path.join(pref.get_latus_folder(), info['path'])
            if os.path.exists(local_file_path):
                local_file_hash, _ = latus.hash.calc_sha512(local_file_path)  # todo: get this pre-computed from the db
            else:
                local_file_hash = None

            if info['event'] == LatusFileSystemEvent.created or info['event'] == LatusFileSystemEvent.modified:
                if info['hash'] != local_file_hash:

                    crypto_key = pref.get_crypto_key()
                    if crypto_key is None:
                        latus.logger.log.warning('no crypto_key yet')
                        return
                    crypto = latus.crypto.Crypto(crypto_key, pref.get_node_id())

                    if info['hash']:
                        cloud_fernet_file = os.path.join(cloud_folders.cache,
                                                         info['hash'] + ENCRYPTION_EXTENSION)
                        latus.logger.log.info('%s : %s : %s %s %s - propagating to %s %s' %
                                              (pref.get_node_id(), info['detection'], info['originator'], info['event'], info['path'],
                                               local_file_path, info['hash']))
                        encrypt, shared, cloud = this_node_db.get_folder_preferences_from_path(info['path'])
                        self.add_filter_event(local_file_path, LatusFileSystemEvent.any)  # is actually create or modify ... will be correct when we have this class use the proper watchdog events
                        if encrypt:
                            expand_ok = crypto.decrypt(cloud_fernet_file, local_file_path)
                            # todo: set mtime
                            if not expand_ok:
                                latus.logger.log.fatal('Latus Key Error - please reinitialize the Latus Key : %s : %s' % (cloud_fernet_file, local_file_path))
                        else:
                            cloud_file = os.path.join(cloud_folders.cache, info['hash'] + UNENCRYPTED_EXTENSION)
                            shutil.copy2(cloud_file, local_file_path)
                        this_node_db.clear_pending(info)
                    else:
                        latus.logger.log.warning('%s : hash is None for %s' % (pref.get_node_id(), local_file_path))
            elif info['event'] == LatusFileSystemEvent.deleted:
                self.add_filter_event(local_file_path, LatusFileSystemEvent.deleted)
                latus.logger.log.info('%s : %s : %s deleted %s' % (pref.get_node_id(), detection_source, info['originator'], info['path']))
                try:
                    if os.path.exists(local_file_path):
                        send2trash.send2trash(local_file_path)
                except OSError:
                    # fallback
                    latus.logger.log.warn('%s : send2trash failed on %s' % (pref.get_node_id(), local_file_path))
                this_node_db.clear_pending(info)
            elif info['event'] == LatusFileSystemEvent.moved:
                # todo: make a specific 'moved' filter event - this one just uses the dest
                latus_path = pref.get_latus_folder()
                latus.logger.log.info('%s : %s : %s moved %s to %s' % (pref.get_node_id(), detection_source, info['originator'], info['path'], info['srcpath']))
                dest_abs_path = os.path.join(latus_path, info['path'])
                src_abs_path = os.path.join(latus_path, info['srcpath'])
                self.add_filter_event(src_abs_path, LatusFileSystemEvent.moved)  # on moves, we only get a watchdog on the source
                try:
                    shutil.move(src_abs_path, dest_abs_path)
                except IOError as e:
                    latus.logger.log.error('%s : %s' % (pref.get_node_id(), str(e)))
                    if os.path.exists(dest_abs_path):
                        latus.logger.log.error('%s : attempting move but %s already exists' % (pref.get_node_id(), dest_abs_path))
                    if not os.path.exists(src_abs_path):
                        latus.logger.log.error('%s : attempting move but %s not found' % (pref.get_node_id(), src_abs_path))
                this_node_db.clear_pending(info)
            else:
                latus.logger.log.error('not yet implemented : %s' % str(info['event']))

    def fs_scan(self, detection_source):
        pass


class Sync:
    def __init__(self, app_data_folder, status_folder_path=None):
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

        if pref.get_upload_logs():
            self.usage_uploader = latus.usage.LatusUsageUploader(60*60)  # todo: make usage upload period a preference variable
            latus.logger.add_http_handler()
        else:
            self.usage_uploader = None

    def start(self):
        if self.usage_uploader:
            self.usage_uploader.start()
        self.local_sync.fs_scan(DetectionSource.initial_scan)
        self.cloud_sync.cloud_sync(DetectionSource.initial_scan)
        self.local_sync.start_observer()
        self.cloud_sync.start_observer()

    def poll(self):
        self.local_sync.fs_scan(DetectionSource.periodic_poll)
        self.cloud_sync.cloud_sync(DetectionSource.periodic_poll)

    def request_exit(self):
        if self.usage_uploader:
            self.usage_uploader.request_exit()
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

    def is_active(self):
        return self.local_sync.is_active() and self.cloud_sync.is_active()

if __name__ == '__main__':
    # Run latus from the command line with existing preferences.
    # This is particularly useful for testing.
    args = latus.util.arg_parse()
    latus.logger.init_from_args(args)
    sync = Sync(args.appdatafolder)
    sync.start()
    input('hit enter to exit')
    if sync.request_exit():
        print('note: exit timed out')
