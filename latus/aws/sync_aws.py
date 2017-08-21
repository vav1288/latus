
import os
import datetime
from functools import wraps
import threading
import shutil
import time

import send2trash
import watchdog.observers
import watchdog.events

import maya
from maya import MayaDT

from boto3.dynamodb import conditions

import latus.aws.aws_access
import latus.const
import latus.aws
from latus.aws.table_events import TableEvents
from latus.aws.table_node import TableNodes
import latus.walker
import latus.hash
import latus.miv
from latus import nodedb
import latus.usage
import latus.crypto
from latus import logger
from latus import preferences
from latus import util
from latus import activity_timer
from latus.const import TIME_OUT, LatusFileSystemEvent, DetectionSource, ENCRYPTION_EXTENSION, UNENCRYPTED_EXTENSION, FILTER_TIME_OUT


latus_to_watchdog_events = {latus.const.LatusFileSystemEvent.moved: watchdog.events.EVENT_TYPE_MOVED,
                            latus.const.LatusFileSystemEvent.deleted: watchdog.events.EVENT_TYPE_DELETED,
                            latus.const.LatusFileSystemEvent.created: watchdog.events.EVENT_TYPE_CREATED,
                            latus.const.LatusFileSystemEvent.modified: watchdog.events.EVENT_TYPE_MODIFIED}


# todo: should I periodically check this to make sure it's not held indefinitely?
latus_lock = threading.Lock()  # since the file system is globally shared, lock it during access


def activity_and_lock(func):
    """
    decorator that adds activity triggers
    """
    @wraps(func)
    def do_activity_and_lock(self, *args, **kwargs):
        self.active_timer.enter_trigger(func.__name__)
        time_before_acquire = time.time()
        acquired = latus_lock.acquire(timeout=latus.const.LONG_TIME_OUT)
        time_to_acquire_lock = time.time() - time_before_acquire
        if time_to_acquire_lock < latus.const.LONG_TIME_OUT:
            logger.log.info('time to acquire lock : %f' % time_to_acquire_lock)
        else:
            logger.log.warn('time to acquire lock : %f' % time_to_acquire_lock)
        if not acquired:
            logger.log.warn('could not acquire lock to run %s - proceeding anyway' % func.__name__)
        r = func(self, *args, **kwargs)
        if acquired:
            try:
                latus_lock.release()
                logger.log.info('lock released : %f' % (time.time() - time_before_acquire))
            except RuntimeError:
                logger.log.warn('tried to release an unlocked lock for %s' % func.__name__)
        self.active_timer.exit_trigger(func.__name__)
        return r
    return do_activity_and_lock


class EventFilter(threading.Thread):
    def __init__(self):
        super().__init__()
        self.filter_list = []
        self.exit_event = threading.Event()
        self.filter_sample_period = 0.25
        self.filter_timeout_count = int(round(float(FILTER_TIME_OUT)/self.filter_sample_period))

    def run(self):
        while not self.exit_event.is_set():
            events_to_remove = []
            for filter_event in self.filter_list:
                if filter_event['countdown'] > 0:
                    logger.log.debug('counting down filter event %s' % str(filter_event))
                    filter_event['countdown'] -= 1
                else:
                    events_to_remove.append(filter_event)
            for event_to_remove in events_to_remove:
                if event_to_remove['seen_count'] != 1:
                    logger.log.warn('seen_count is not 1 : %s' % (event_to_remove))
                self.filter_list.remove(event_to_remove)
                logger.log.info('removing filter event %s' % str(event_to_remove))
            self.exit_event.wait(self.filter_sample_period)
        logger.log.info('exiting EventFilter')

    # todo: need src and dest for moves - right now we just use the dest
    def add_event(self, path, event_type):
        event = {'path': path, 'countdown': self.filter_timeout_count, 'seen_count': 0, 'event_type': event_type}
        logger.log.info('filter add_event : %s (timeout_count=%d, sample_period=%.2f)' % (str(event), self.filter_timeout_count, self.filter_sample_period))
        self.filter_list.append(event)

    def test_event(self, watchdog_event):
        # test if this path should be filtered out
        if watchdog_event.is_directory:
            # always filter out directory events
            logger.log.info('filtering out watchdog directory event : %s' % str(watchdog_event))
            return True
        found_one = False
        for filter_event in self.filter_list:
            if watchdog_event.src_path == filter_event['path']:
                filter_event['seen_count'] += 1  # assume it's the most senior entry
                found_one = True
                if latus_to_watchdog_events[filter_event['event_type']] != watchdog_event.event_type:
                    logger.log.warn('event type mismatch : expected %s, got %s' % (filter_event, watchdog_event))
                break
        if found_one:
            logger.log.info('event filtered : %s' % watchdog_event)
        return found_one

    def request_exit(self):
        self.exit_event.set()
        if len(self.filter_list) > 0:
            for filter_event in self.filter_list:
                logger.log.info('leftover filter event : %s' % str(filter_event))


class AWSSync(watchdog.events.FileSystemEventHandler):
    """
    Sync using AWS
    """
    def __init__(self, app_data_folder, use_aws_local):

        # there is no "super().__init__()"

        self.app_data_folder = app_data_folder
        self.use_aws_local = use_aws_local
        pref = preferences.Preferences(app_data_folder)

        self.active_timer = activity_timer.ActivityTimer(pref.get_node_id() + '_' + self.get_type())

        self.event_filter = EventFilter()
        self.event_filter.start()

        if pref.get_upload_logs():
            self.usage_uploader = latus.usage.LatusUsageUploader(60*60)  # todo: make usage upload period a preference variable
            latus.logger.add_http_handler()
        else:
            self.usage_uploader = None

        self.s3 = latus.aws.aws_access.LatusS3(pref, use_aws_local)

        self.table_node = TableNodes(use_aws_local)
        self.table_node.register(pref.get_node_id())

        self.latus_folder = pref.get_latus_folder()
        util.make_dir(self.latus_folder)

        self.observer = watchdog.observers.Observer()
        self.observer.schedule(self, self.latus_folder, recursive=True)

        latus.nodedb.NodeDB(self.app_data_folder, pref.get_node_id(), True)  # make DB if doesn't already exist

        self.fs_scan(DetectionSource.initial_scan)

        # todo: this needs to be in a separate class so that we can have a test value and a value from advanced preferences
        if use_aws_local:
            poll_period = latus.const.POLL_PERIOD
        else:
            poll_period = 10*60  # should be from advanced preferences
        self.aws_db_sync = AWSDBSync(self.app_data_folder, poll_period, use_aws_local, self.event_filter)

    def get_type(self):
        return 'aws_sync'

    def get_node_id(self):
        pref = latus.preferences.Preferences(self.app_data_folder)
        return pref.get_node_id()

    @activity_and_lock
    def start(self):
        if self.usage_uploader:
            self.usage_uploader.start()
        self.observer.start()
        self.aws_db_sync.start()

    def request_exit(self, time_out=TIME_OUT):
        pref = latus.preferences.Preferences(self.app_data_folder)
        logger.log.info('%s - %s - request_exit begin' % (pref.get_node_id(), self.get_type()))
        self.observer.stop()
        self.observer.join(time_out)
        if self.observer.is_alive():
            logger.log.warn('%s - %s - request_exit failed to stop observer' % (pref.get_node_id(), self.get_type()))
        self.active_timer.reset()
        self.aws_db_sync.request_exit()
        self.aws_db_sync.join(time_out)
        if self.aws_db_sync.isAlive():
            logger.log.warn('%s - %s - request_exit failed to stop aws_db_sync' % (pref.get_node_id(), self.get_type()))
        logger.log.info('%s - %s - request_exit end' % (pref.get_node_id(), self.get_type()))
        return self.observer.is_alive() or self.aws_db_sync.is_alive()

    @activity_and_lock
    def start_observer(self):
        pref = latus.preferences.Preferences(self.app_data_folder)
        logger.log.info('%s : starting observer : %s' % (pref.get_node_id(), self.latus_folder))
        self.observer.start()

    @activity_and_lock
    def on_created(self, watchdog_event):
        logger.log.info('%s : local on_created event : %s' % (self.get_node_id(), str(watchdog_event)))
        if not self.event_filter.test_event(watchdog_event):
            src_path = watchdog_event.src_path
            file_hash = self._fill_file_cache(src_path)
            self._write_db(src_path, None, LatusFileSystemEvent.created, DetectionSource.watchdog, file_hash, watchdog_event.is_directory)

    @activity_and_lock
    def on_deleted(self, watchdog_event):
        latus.logger.log.info('%s : local on_deleted event : %s' % (self.get_node_id(), str(watchdog_event)))
        if not self.event_filter.test_event(watchdog_event):
            # todo: remove from cache
            self._write_db(watchdog_event.src_path, None, LatusFileSystemEvent.deleted, DetectionSource.watchdog, None, watchdog_event.is_directory)

    @activity_and_lock
    def on_modified(self, watchdog_event):
        latus.logger.log.info('%s : local on_modified event : %s' % (self.get_node_id(), str(watchdog_event)))
        if not self.event_filter.test_event(watchdog_event):
            if os.path.isdir(watchdog_event.src_path):
                # todo: perhaps handle directories and not just files?
                logger.log.info('%s : %s is dir - doing nothing' % (self.get_node_id(), watchdog_event.src_path))
            else:
                file_hash = self._fill_file_cache(watchdog_event.src_path)
                self._write_db(watchdog_event.src_path, None, LatusFileSystemEvent.modified, DetectionSource.watchdog, file_hash, watchdog_event.is_directory)

    @activity_and_lock
    def on_moved(self, watchdog_event):
        latus.logger.log.info('%s : local on_moved event : %s' % (self.get_node_id(), str(watchdog_event)))
        if not self.event_filter.test_event(watchdog_event):
            # for move events the dest is an absolute path - we need just the partial path
            src_path = watchdog_event.src_path.replace(self.latus_folder, '')
            if src_path[0] == os.sep:
                # remove leading /
                src_path = src_path[1:]

            pref = latus.preferences.Preferences(self.app_data_folder)
            file_hash, _ = latus.hash.calc_sha512(watchdog_event.dest_path, pref.get_crypto_key())
            self._write_db(watchdog_event.dest_path, src_path, LatusFileSystemEvent.moved, DetectionSource.watchdog, file_hash, watchdog_event.is_directory)

    # todo: encrypt the hash?
    def _write_db(self, full_path, src_path, filesystem_event_type, detection_source, file_hash, is_dir):
        pref = latus.preferences.Preferences(self.app_data_folder)
        latus_path = full_path.replace(pref.get_latus_folder() + os.sep, '')
        this_node_id = pref.get_node_id()
        node_db = nodedb.NodeDB(self.app_data_folder, this_node_id)
        if os.path.exists(full_path):
            mtime = datetime.datetime.utcfromtimestamp(os.path.getmtime(full_path))
            size = os.path.getsize(full_path)
        else:
            mtime = None
            size = None
        mivui = latus.miv.get_mivui(this_node_id)

        logger.log.info("_write_db : %s" % str([this_node_id, mivui, filesystem_event_type, full_path, detection_source, size, file_hash, mtime]))

        # write this entry if there is no entry for this path or if the file has changed
        partial_path = os.path.relpath(full_path, pref.get_latus_folder())
        event_table = TableEvents(self.use_aws_local)
        # update locally first (pending True)
        node_db.insert(mivui, this_node_id, int(filesystem_event_type), int(detection_source), partial_path, src_path, size, file_hash, mtime, True)
        # then AWS
        aws_success = event_table.add(mivui, this_node_id, int(filesystem_event_type), int(detection_source), latus_path, src_path, size, file_hash, mtime)
        # now set the pending flag based on aws_success
        if aws_success:
            node_db.update_pending({'miviu': mivui, 'file_path': partial_path})
        else:
            latus.logger.log.warn('event_table.add() failed for %s' % latus_path)

        latus.logger.log.info('exiting _write_db')

    def _fill_file_cache(self, full_path):
        pref = latus.preferences.Preferences(self.app_data_folder)
        node_id = pref.get_node_id()
        cache_folder = pref.get_cache_folder()

        # Currently for AWS we encrypt everything - eventually we'll want to make this a per-folder option
        # that is in a new AWS preferences table.  The csp way stored the folder preferences in the node_db,
        # and we don't have node_db for the AWS version so we need a new table.
        # todo: move per folder preferences to a new AWS table (not node_db)
        encrypt = True

        hash, _ = latus.hash.calc_sha512(full_path, pref.get_crypto_key())
        if encrypt:

            crypto_key = pref.get_crypto_key()
            if crypto_key is None:
                latus.logger.log.fatal('No Latus Key - please reinitialize the preferences - exiting')
                return None
            if hash is None:
                latus.logger.log.warning('could not get hash for %s' % full_path)
            else:

                # write to local cache
                os.makedirs(cache_folder, exist_ok=True)
                cloud_fernet_file = os.path.join(cache_folder, hash + ENCRYPTION_EXTENSION)
                crypto = latus.crypto.Crypto(crypto_key, node_id)
                if not os.path.exists(cloud_fernet_file):
                    latus.logger.log.info('%s : file_write , %s' % (node_id, cloud_fernet_file))
                    crypto.encrypt_file(full_path, os.path.abspath(cloud_fernet_file))

                # upload to S3 (if it's not there already)
                self.s3.upload_file(cloud_fernet_file, hash)

        else:
            raise NotImplemented  # need the new AWS folder preferences table mentioned above
        return hash

    @activity_and_lock
    def fs_scan(self, detection_source):
        latus.logger.log.info('fs_scan start')
        pref = latus.preferences.Preferences(self.app_data_folder)
        this_node_id = pref.get_node_id()
        node_db = latus.nodedb.NodeDB(self.app_data_folder, this_node_id)
        local_walker = latus.walker.Walker(pref.get_latus_folder())
        for partial_path in local_walker:
            logger.log.info('partial_path : %s' % partial_path)
            local_full_path = local_walker.full_path(partial_path)
            logger.log.info('local_full_path : %s' % local_full_path)
            if os.path.exists(local_full_path):
                local_hash, _ = latus.hash.calc_sha512(local_full_path, pref.get_crypto_key())
                if local_hash:
                    logger.log.info('local_hash : %s' % local_hash)
                    most_recent_hash = node_db.get_most_recent_hash(partial_path)
                    if most_recent_hash is None:
                        file_system_event = LatusFileSystemEvent.created
                    else:
                        file_system_event = LatusFileSystemEvent.modified
                    logger.log.info('file_system_event : %s' % file_system_event)
                    if local_hash != most_recent_hash:
                        mtime = datetime.datetime.utcfromtimestamp(os.path.getmtime(local_full_path))
                        size = os.path.getsize(local_full_path)
                        logger.log.info('getting mivui')
                        mivui = latus.miv.get_mivui(this_node_id)
                        logger.log.info('sync : %s' % [this_node_id, file_system_event, mivui, partial_path, detection_source, size, local_hash, mtime])
                        self._fill_file_cache(local_full_path)
                        self._write_db(local_full_path, None, file_system_event, detection_source, local_hash, os.path.isdir(local_full_path))
                    else:
                        logger.log.warn('hashes : %s, %s' % (local_hash, most_recent_hash))
                else:
                    latus.logger.log.warn('%s : could not calculate hash for %s' % (this_node_id, local_full_path))
            else:
                logger.log.info('not found : %s' % local_full_path)
        latus.logger.log.info('fs_scan end')


class AWSDBSync(threading.Thread):
    """
    Synchronize to AWS and act on any new events.
    Fill in any local event DB entries from AWS that we don't have in our local DB.  This can happen either by polling
    or as the result of an AWS SQS message that another node has published.
    """
    def __init__(self, app_data_folder, poll_period_sec, use_aws_local, event_filter):
        super().__init__()
        self.app_data_folder = app_data_folder
        self.event_filter = event_filter

        self.exit_event = threading.Event()
        pref = preferences.Preferences(self.app_data_folder)
        self.active_timer = activity_timer.ActivityTimer(pref.get_node_id() + '_' + self.get_type())
        self.aws_event_table = TableEvents(use_aws_local)
        self.node_table = TableNodes(use_aws_local)
        self.poll_period_sec = poll_period_sec
        self.s3 = latus.aws.aws_access.LatusS3(pref, use_aws_local)

        latus.logger.log.info('poll period : %f sec' % float(self.poll_period_sec))

    def run(self):
        pref = preferences.Preferences(self.app_data_folder)
        while not self.exit_event.is_set():
            latus.logger.log.info('starting poll')
            self._sync_with_aws(pref)
            latus.logger.log.info('poll complete')
            self.exit_event.wait(timeout=self.poll_period_sec)
        self.event_filter.request_exit()
        self.event_filter.join(latus.const.LONG_TIME_OUT)
        if self.event_filter.isAlive():
            logger.log.warn('g_event_filter is still alive')
        logger.log.info('exiting node "%s"' % pref.get_node_id())

    def _pull_down_new_db_entries(self, pref):
        """
        Get new file system event DB entries from AWS.  Keep a list of events that we got new entries for,
        so that we can perform these events locally.  In a sense this is a 'command' to perform this action,
        and we will only do it once since it is only inserted into the local DB once.
        :return: a list of events to take action on
        """
        logger.log.debug('pulling down new entries')
        this_node_id = pref.get_node_id()
        node_db = nodedb.NodeDB(self.app_data_folder, this_node_id)
        aws_event_table_resource = self.aws_event_table.get_table_resource()

        updated_events = []
        for node_id in self.node_table.get_all_nodes():
            if node_id != this_node_id:
                most_recent_local = node_db.get_most_recent_entry(node_id)
                if most_recent_local:
                    most_recent_local_mivui = most_recent_local['mivui']
                else:
                    most_recent_local_mivui = 0
                logger.log.debug('most_recent_local_mivui for : %s : %d' % (node_id, most_recent_local_mivui))

                query_response = aws_event_table_resource.query(
                    KeyConditionExpression=conditions.Key('originator').eq(node_id) & conditions.Key('mivui').gt(most_recent_local_mivui)
                )
                for q in query_response['Items']:
                    logger.log.info('query_response : %s' % str(q))
                    mtime = q['mtime']
                    if mtime:
                        mtime = maya.parse(mtime).datetime()
                    size = q['size']
                    if size:
                        size = int(size)
                    logger.log.info('new_db_entry : %s' % str(q))
                    node_db.insert(int(q['mivui']), q['originator'], int(q['event_type']), int(q['detection']), q['file_path'],
                                   q['src_path'], size, q['file_hash'], mtime, False)
                    updated_events.append(q)
        if len(updated_events) > 0:
            latus.logger.log.info('updated events : %s' % str(updated_events))
        return updated_events

    @activity_and_lock
    def _sync_with_aws(self, pref):
        latus.logger.log.info('entering _sync')
        updated_events = self._pull_down_new_db_entries(pref)
        for fs_event in updated_events:
            event_type = fs_event['event_type']
            hash_value = fs_event['file_hash']
            local_file_path = os.path.join(pref.get_latus_folder(), fs_event['file_path'])
            if os.path.exists(local_file_path):
                local_file_hash, _ = latus.hash.calc_sha512(local_file_path, pref.get_crypto_key())
            else:
                local_file_hash = None
            if event_type == LatusFileSystemEvent.created or event_type == LatusFileSystemEvent.modified:
                if hash_value != local_file_hash:
                    self.event_filter.add_event(local_file_path, event_type)
                    crypto_key = pref.get_crypto_key()
                    if crypto_key is None:
                        latus.logger.log.warning('no crypto_key yet')
                        return
                    crypto = latus.crypto.Crypto(crypto_key, pref.get_node_id())

                    if hash_value:
                        cache_fernet_file = os.path.join(pref.get_cache_folder(), hash_value + ENCRYPTION_EXTENSION)
                        self.s3.download_file(cache_fernet_file, hash_value)
                        latus.logger.log.info(
                            'originator=%s, event_type=%s, detection=%s, file_path="%s" - propagating to "%s" (file_hash=%s)' %
                            (fs_event['originator'], fs_event['event_type'], fs_event['detection'],
                             fs_event['file_path'], local_file_path, fs_event['file_hash']))
                        encrypt, shared, cloud = True, False, True  # todo: get this from pref
                        if encrypt:
                            expand_ok = crypto.decrypt_file(cache_fernet_file, local_file_path)
                            if expand_ok:
                                mtime = MayaDT.from_iso8601(fs_event['mtime']).epoch
                                os.utime(local_file_path, (mtime, mtime))
                            else:
                                # todo: something more elegant than just calling fatal here
                                latus.logger.log.fatal('Unable to decrypt (possible latus key error) : %s : %s' % (
                                cache_fernet_file, local_file_path))
                        else:
                            cloud_file = os.path.join(pref.get_cache_folder(),
                                                      fs_event['file_hash'] + UNENCRYPTED_EXTENSION)
                            shutil.copy2(cloud_file, local_file_path)
                    else:
                        latus.logger.log.warning('%s : hash is None for %s' % (pref.get_node_id(), local_file_path))
            elif event_type == LatusFileSystemEvent.deleted:
                try:
                    if os.path.exists(local_file_path):
                        latus.logger.log.info('%s : %s : %s deleted %s' % (
                        pref.get_node_id(), fs_event['detection'], fs_event['originator'], fs_event['file_path']))
                        self.event_filter.add_event(local_file_path, event_type)
                        send2trash.send2trash(local_file_path)
                except OSError:
                    # fallback
                    latus.logger.log.warn('%s : send2trash failed on %s' % (pref.get_node_id(), local_file_path))
            elif event_type == LatusFileSystemEvent.moved:
                # todo: make a specific 'moved' filter event - this one just uses the dest
                latus_path = pref.get_latus_folder()
                latus.logger.log.info('%s : %s : %s moved %s to %s' % (
                pref.get_node_id(), fs_event['detection'], fs_event['originator'], fs_event['src_path'],
                fs_event['file_path']))
                dest_abs_path = os.path.join(latus_path, fs_event['file_path'])
                src_abs_path = os.path.join(latus_path, fs_event['src_path'])
                if not os.path.exists(src_abs_path):
                    logger.log.info('%s : most recent is move of %s to %s but source does not exist - nothing to do' % (
                    pref.get_node_id(), src_abs_path, dest_abs_path))
                    return
                os.makedirs(os.path.dirname(dest_abs_path), exist_ok=True)
                # we'll get events for both src and dest
                self.event_filter.add_event(src_abs_path, event_type)
                self.event_filter.add_event(dest_abs_path, event_type)
                try:
                    shutil.move(src_abs_path, dest_abs_path)
                except IOError as e:
                    latus.logger.log.error('%s : %s' % (pref.get_node_id(), str(e)))
                    if os.path.exists(dest_abs_path):
                        latus.logger.log.error(
                            '%s : attempting move but %s already exists' % (pref.get_node_id(), dest_abs_path))
                    if not os.path.exists(src_abs_path):
                        latus.logger.log.error(
                            '%s : attempting move but %s not found' % (pref.get_node_id(), src_abs_path))
            else:
                latus.logger.log.error('not yet implemented : %s' % str(event_type))

        latus.logger.log.info('exiting _sync')

    def get_type(self):
        return 'aws_db_sync'

    def request_exit(self):
        latus.logger.log.info('request_exit')
        self.active_timer.reset()
        self.exit_event.set()
