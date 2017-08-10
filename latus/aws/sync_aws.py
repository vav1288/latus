
import os
import datetime
from functools import wraps
import threading
import time
import shutil

import send2trash
import watchdog.observers
import watchdog.events

import maya

import boto3
from boto3.dynamodb import conditions

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

g_event_filter = EventFilter()
g_event_filter.start()


class Sync(watchdog.events.FileSystemEventHandler):
    """
    Local sync folder
    """
    def __init__(self, app_data_folder):

        # there is no "super().__init__()"

        self.app_data_folder = app_data_folder
        pref = preferences.Preferences(app_data_folder)

        self.active_timer = activity_timer.ActivityTimer(3, pref.get_node_id() + '_' + self.get_type())

        if pref.get_upload_logs():
            self.usage_uploader = latus.usage.LatusUsageUploader(60*60)  # todo: make usage upload period a preference variable
            latus.logger.add_http_handler()
        else:
            self.usage_uploader = None

        if pref.get_aws_local():
            latus.aws.local_testing()
        latus.aws.init()
        self.s3 = latus.aws.LatusS3()

        self.table_node = TableNodes()
        self.table_node.register(pref.get_node_id())

        self.latus_folder = pref.get_latus_folder()
        util.make_dir(self.latus_folder)

        self.observer = watchdog.observers.Observer()
        self.observer.schedule(self, self.latus_folder, recursive=True)

        latus.nodedb.NodeDB(self.app_data_folder, pref.get_node_id(), True)  # make DB if doesn't already exist

        self.fs_scan(DetectionSource.initial_scan)

        if pref.get_aws_local():
            poll_period = latus.const.FILTER_TIME_OUT * 2
        else:
            poll_period = 10*60
        self.aws_db_sync = AWSDBSync(self.app_data_folder, poll_period)

    def get_type(self):
        return 'local_aws_sync'

    def get_node_id(self):
        pref = latus.preferences.Preferences(self.app_data_folder)
        return pref.get_node_id()

    @activity_trigger
    def start(self):
        if self.usage_uploader:
            self.usage_uploader.start()
        self.observer.start()
        self.aws_db_sync.start()

    @activity_trigger
    def request_exit(self, time_out=TIME_OUT):
        pref = latus.preferences.Preferences(self.app_data_folder)
        logger.log.info('%s - %s - request_exit begin' % (pref.get_node_id(), self.get_type()))
        self.observer.stop()
        self.observer.join(time_out)
        if self.observer.is_alive():
            logger.log.warn('%s - %s - request_exit failed to stop observer' % (pref.get_node_id(), self.get_type()))
        self.active_timer.reset()
        self.aws_db_sync.request_exit()
        logger.log.info('%s - %s - request_exit end' % (pref.get_node_id(), self.get_type()))
        return self.observer.is_alive() or self.aws_db_sync.is_alive()

    @activity_trigger
    def start_observer(self):
        pref = latus.preferences.Preferences(self.app_data_folder)
        logger.log.info('%s : starting observer : %s' % (pref.get_node_id(), self.latus_folder))
        self.observer.start()

    @activity_trigger
    def on_created(self, watchdog_event):
        logger.log.info('%s : local on_created event : %s' % (self.get_node_id(), str(watchdog_event)))
        if not g_event_filter.test_event(watchdog_event):
            src_path = watchdog_event.src_path
            file_hash = self._fill_cache(src_path)
            self._write_db(src_path, None, LatusFileSystemEvent.created, DetectionSource.watchdog, file_hash, watchdog_event.is_directory)

    @activity_trigger
    def on_deleted(self, watchdog_event):
        latus.logger.log.info('%s : local on_deleted event : %s' % (self.get_node_id(), str(watchdog_event)))
        if not g_event_filter.test_event(watchdog_event):
            # todo: remove from cache
            self._write_db(watchdog_event.src_path, None, LatusFileSystemEvent.deleted, DetectionSource.watchdog, None, watchdog_event.is_directory)

    @activity_trigger
    def on_modified(self, watchdog_event):
        latus.logger.log.info('%s : local on_modified event : %s' % (self.get_node_id(), str(watchdog_event)))
        if not g_event_filter.test_event(watchdog_event):
            if os.path.isdir(watchdog_event.src_path):
                # todo: perhaps handle directories and not just files?
                logger.log.info('%s : %s is dir - doing nothing' % (self.get_node_id(), watchdog_event.src_path))
            else:
                file_hash = self._fill_cache(watchdog_event.src_path)
                self._write_db(watchdog_event.src_path, None, LatusFileSystemEvent.modified, DetectionSource.watchdog, file_hash, watchdog_event.is_directory)

    @activity_trigger
    def on_moved(self, watchdog_event):
        latus.logger.log.info('%s : local on_moved event : %s' % (self.get_node_id(), str(watchdog_event)))
        if not g_event_filter.test_event(watchdog_event):
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

        # check that file actually changed
        logger.log.info("_write_db : %s" % str([this_node_id, mivui, filesystem_event_type, full_path, detection_source, size, file_hash, mtime]))
        most_recent_hash = node_db.get_most_recent_hash(latus_path)
        if most_recent_hash != file_hash:
            partial_path = os.path.relpath(full_path, pref.get_latus_folder())
            event_table = TableEvents()
            # update locally first (pending True)
            node_db.update(mivui, this_node_id, int(filesystem_event_type), int(detection_source), partial_path, src_path, size, file_hash, mtime, True)
            # then AWS
            aws_success = event_table.add(mivui, this_node_id, int(filesystem_event_type), int(detection_source), latus_path, src_path, size, file_hash, mtime)
            # now set the pending flag based on aws_success
            if aws_success:
                node_db.update_pending({'miviu': mivui, 'file_path': partial_path})

    def _fill_cache(self, full_path):
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

    @activity_trigger
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
                        self._fill_cache(local_full_path)
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
    Fill in any local event DB entries from AWS that we don't have in our local DB.  This can happen either by polling
    or as the result of an AWS SQS message that another node has published.
    """
    def __init__(self, app_data_folder, poll_period_sec):
        super().__init__()
        self.app_data_folder = app_data_folder
        self.exit_event = threading.Event()
        self.event_table = TableEvents()
        self.node_table = TableNodes()
        self.poll_period_sec = poll_period_sec
        self.s3 = latus.aws.LatusS3()

        latus.logger.log.info('poll period : %f sec' % float(self.poll_period_sec))

    def run(self):
        pref = preferences.Preferences(self.app_data_folder)
        while not self.exit_event.is_set():
            self._pull_down_new_db_entries(pref)
            self._sync(pref)
            self.exit_event.wait(timeout=self.poll_period_sec)

    def _pull_down_new_db_entries(self, pref):

        logger.log.info('pulling down new entries')
        this_node_id = pref.get_node_id()
        node_db = nodedb.NodeDB(self.app_data_folder, this_node_id)
        event_table_resource = self.event_table.get_table_resource()

        for node_id in self.node_table.get_all_nodes():
            if node_id != this_node_id:
                most_recent_local = node_db.get_most_recent_entry(node_id)
                if most_recent_local:
                    most_recent_local_mivui = most_recent_local['mivui']
                else:
                    most_recent_local_mivui = 0
                logger.log.info('most_recent_local_mivui for : %s : %d' % (node_id, most_recent_local_mivui))

                query_response = event_table_resource.query(
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
                    node_db.update(int(q['mivui']), q['originator'], int(q['event_type']), int(q['detection']), q['file_path'],
                                   q['src_path'], size, q['file_hash'], mtime, False)

    def _sync(self, pref):
        this_node_id = pref.get_node_id()
        node_db = nodedb.NodeDB(self.app_data_folder, this_node_id)
        for path in node_db.get_paths():
            self._one_sync(path, pref)

    def _one_sync(self, path, pref):
        logger.log.info('start _one_sync')
        this_node_id = pref.get_node_id()
        node_db = nodedb.NodeDB(self.app_data_folder, this_node_id)
        most_recent = node_db.get_most_recent_entry_for_path(path)
        if most_recent['originator'] == this_node_id:
            # this node created the most recent state, so nothing to do
            return
        logger.log.info('most_recent : %s' % str(most_recent))
        event = most_recent['event_type']
        hash_value = most_recent['file_hash']
        local_file_path = os.path.join(pref.get_latus_folder(), most_recent['file_path'])
        if os.path.exists(local_file_path):
            local_file_hash, _ = latus.hash.calc_sha512(local_file_path, pref.get_crypto_key())
        else:
            local_file_hash = None
        if event == LatusFileSystemEvent.created or event == LatusFileSystemEvent.modified:
            if hash_value != local_file_hash:
                g_event_filter.add_event(local_file_path, event)
                crypto_key = pref.get_crypto_key()
                if crypto_key is None:
                    latus.logger.log.warning('no crypto_key yet')
                    return
                crypto = latus.crypto.Crypto(crypto_key, pref.get_node_id())

                if hash_value:
                    cache_fernet_file = os.path.join(pref.get_cache_folder(), hash_value + ENCRYPTION_EXTENSION)
                    self.s3.download_file(cache_fernet_file, hash_value)
                    latus.logger.log.info('originator=%s, event_type=%s, detection=%s, file_path="%s" - propagating to "%s" (file_hash=%s)' %
                                          (most_recent['originator'], most_recent['event_type'], most_recent['detection'],
                                           most_recent['file_path'], local_file_path, most_recent['file_hash']))
                    encrypt, shared, cloud = True, False, True  # todo: get this from pref
                    if encrypt:
                        expand_ok = crypto.decrypt_file(cache_fernet_file, local_file_path)
                        if expand_ok:
                            mtime = (most_recent['mtime'] - datetime.datetime.utcfromtimestamp(0)).total_seconds()
                            os.utime(local_file_path, (mtime, mtime))
                        else:
                            # todo: something more elegant than just calling fatal here
                            latus.logger.log.fatal('Unable to decrypt (possible latus key error) : %s : %s' % (cache_fernet_file, local_file_path))
                    else:
                        cloud_file = os.path.join(pref.get_cache_folder(), most_recent['file_hash'] + UNENCRYPTED_EXTENSION)
                        shutil.copy2(cloud_file, local_file_path)
                else:
                    latus.logger.log.warning('%s : hash is None for %s' % (pref.get_node_id(), local_file_path))
        elif event == LatusFileSystemEvent.deleted:
            latus.logger.log.info('%s : %s : %s deleted %s' % (pref.get_node_id(), most_recent['detection'], most_recent['originator'], most_recent['file_path']))
            try:
                if os.path.exists(local_file_path):
                    g_event_filter.add_event(local_file_path, event)
                    send2trash.send2trash(local_file_path)
            except OSError:
                # fallback
                latus.logger.log.warn('%s : send2trash failed on %s' % (pref.get_node_id(), local_file_path))
        elif event == LatusFileSystemEvent.moved:
            # todo: make a specific 'moved' filter event - this one just uses the dest
            latus_path = pref.get_latus_folder()
            latus.logger.log.info('%s : %s : %s moved %s to %s' % (pref.get_node_id(), most_recent['detection'], most_recent['originator'], most_recent['src_path'], most_recent['file_path']))
            dest_abs_path = os.path.join(latus_path, most_recent['file_path'])
            src_abs_path = os.path.join(latus_path, most_recent['src_path'])
            if not os.path.exists(src_abs_path):
                logger.log.info('%s : most recent is move of %s to %s but source does not exist - nothing to do' % (pref.get_node_id(), src_abs_path, dest_abs_path))
                return
            os.makedirs(os.path.dirname(dest_abs_path), exist_ok=True)
            # we'll get events for both src and dest
            g_event_filter.add_event(src_abs_path, event)
            g_event_filter.add_event(dest_abs_path, event)
            try:
                shutil.move(src_abs_path, dest_abs_path)
            except IOError as e:
                latus.logger.log.error('%s : %s' % (pref.get_node_id(), str(e)))
                if os.path.exists(dest_abs_path):
                    latus.logger.log.error('%s : attempting move but %s already exists' % (pref.get_node_id(), dest_abs_path))
                if not os.path.exists(src_abs_path):
                    latus.logger.log.error('%s : attempting move but %s not found' % (pref.get_node_id(), src_abs_path))
        else:
            latus.logger.log.error('not yet implemented : %s' % str(event))

    def request_exit(self):
        g_event_filter.request_exit()
        self.exit_event.set()
        g_event_filter.join(TIME_OUT)
        return self.exit_event.wait(TIME_OUT) and not g_event_filter.is_alive()

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