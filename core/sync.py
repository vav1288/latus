
import os
import json
import threading
import win32file
import win32event
import win32con
import pprint
import core.logger
import core.util
import core.const
import core.metadatapath
import core.walker
import core.hash
import core.compression
import core.exitcontrol

class KBExit(threading.Thread):
    def __init__(self, event):
        self.event = event
        self.keyboard_event = win32event.CreateEvent(None, 0, 0, None)

    def run(self):
        input('press enter to exit')

class Sync(threading.Thread):
    """
    Determines what needs to be done to sync local to cloud.
    """
    DATABASE_FILE_NAME = '.' + core.const.NAME + '_sync_db' + '.json' # reserved

    def __init__(self, password, latus_folder, cloud_root, exit_event_handle = None, appdata_folder = None, verbose = False):
        threading.Thread.__init__(self)
        self.password = password
        self.cloud_root = cloud_root
        self.exit_event_handle = exit_event_handle
        self.latus_folder = latus_folder
        self.verbose = verbose
        if self.verbose:
            print('local_folder', self.latus_folder)
            print('cloud_root', self.cloud_root)
            print('cloud_folder', self.get_cloud_folder())

        core.util.make_dirs(self.latus_folder)

        if appdata_folder is None:
            # I'd like to use winpaths.get_local_appdata() but it doesn't seem to work with Python 3, so I'll
            # rely on the environment variable.
            self.appdata_folder = os.environ['APPDATA']

    def get_cloud_folder(self):
        return os.path.join(self.cloud_root, '.' + core.const.NAME)

    def local_folder_contents(self):
        return dict([(f, None) for f in os.listdir (self.latus_folder)])

    def run(self):
        #
        # FindFirstChangeNotification sets up a handle for watching
        #  file changes. The first parameter is the path to be
        #  watched; the second is a boolean indicating whether the
        #  directories underneath the one specified are to be watched;
        #  the third is a list of flags as to what kind of changes to
        #  watch for. We're just looking at file additions / deletions.
        #
        change_handle = win32file.FindFirstChangeNotification(self.latus_folder, 0,
                                                              win32con.FILE_NOTIFY_CHANGE_FILE_NAME)

        # This order is important.  If multiple events are triggered, only the lowest index is
        # indicated.  So, the exit event must be the lowest index or else we could miss
        # the exit event if it happens as the same time as a file system change.
        wait_objects = [change_handle]
        if self.exit_event_handle is not None:
            wait_objects.insert(0, self.exit_event_handle) # prepend

        #
        # Loop forever, listing any file changes. The WaitFor... will
        #  time out every half a second allowing for keyboard interrupts
        #  to terminate the loop.
        #
        exit_flag = False
        try:
            old_path_contents = self.local_folder_contents()
            while not exit_flag:
                result = win32event.WaitForMultipleObjects(wait_objects, 0, 10 * 1000)
                print('WaitForMultipleObjects', result)
                #
                # If the WaitFor... returned because of a notification (as
                #  opposed to timing out or some error) then look for the
                #  changes in the directory contents.
                #
                if result == win32con.WAIT_OBJECT_0:
                    exit_flag = True
                elif result == win32con.WAIT_OBJECT_0 + 1:
                    new_path_contents = self.local_folder_contents()
                    added = [f for f in new_path_contents if not f in old_path_contents]
                    deleted = [f for f in old_path_contents if not f in new_path_contents]
                    self.sync(added, deleted)
                    old_path_contents = new_path_contents
                    win32file.FindNextChangeNotification(change_handle)
        finally:
            win32file.FindCloseChangeNotification(change_handle)

    def sync(self, added = None, deleted = None):
        """
        Sync new or updated files (both local and cloud).
        """

        # new or updated local files
        local_walker = core.walker.Walker(self.latus_folder)
        for partial_path in local_walker:
            # this is where we use the local _file_ name to create the cloud _folder_ where the .zips and metadata reside
            full_path = local_walker.full_path(partial_path)
            file_as_cloud_folder = os.path.join(self.get_cloud_folder(), partial_path)
            if not os.path.exists(file_as_cloud_folder):
                os.makedirs(file_as_cloud_folder)
                if self.verbose:
                    print('new local', partial_path)
            hash, _ = core.hash.calc_sha512(full_path)
            if hash is not None:
                cloud_zip_file = os.path.join(file_as_cloud_folder, hash + '.zip')
                if not os.path.exists(cloud_zip_file):
                    if self.verbose:
                        print('writing', partial_path, '(', cloud_zip_file, ')')
                    compressor = core.compression.Compression(self.password, self.verbose)
                    # Input to archive program (7z) is relative to the latus folder.  Note that we have to explicitly
                    # give the full abs path of the archive itself since it's in a different folder.
                    compressor.compress(self.latus_folder, partial_path, os.path.abspath(cloud_zip_file))
                    mtime = os.path.getmtime(full_path)
                    size = os.path.getsize(full_path)
                    self.update_database(partial_path, file_as_cloud_folder, hash, mtime, size)

        # new or updated cloud files
        # todo: we're actually only interested in dirs here ... make Walker have a dirs only mode
        cloud_walker = core.walker.Walker(self.get_cloud_folder(), do_dirs=True)
        for partial_path in cloud_walker:
            full_path = cloud_walker.full_path(partial_path)
            if os.path.isdir(full_path):
                print('checking for new cloud files', 'full_path', full_path)
                file_as_cloud_folder = os.path.join(self.get_cloud_folder(), partial_path)
                db = self.read_database(file_as_cloud_folder)
                file_path = db['path']
                version = db['versions'][-1] # last entry in the list is most recent
                hash = version['hash']
                # todo: compare hashes
                dest_path = os.path.join(self.latus_folder, file_path)
                if not os.path.exists(dest_path):
                    print('extracting', dest_path)
                    extractor = core.compression.Compression(self.password, self.verbose)
                    cloud_zip_file = os.path.join(file_as_cloud_folder, hash + '.zip')
                    extractor.expand(self.latus_folder, os.path.abspath(cloud_zip_file))

    def update_database(self, partial_path, file_as_cloud_folder, hash, mtime, size):
        db_file_path = os.path.join(file_as_cloud_folder, self.DATABASE_FILE_NAME)
        if os.path.exists(db_file_path):
            with open(db_file_path) as f:
                db_info = json.load(f)
        else:
            db_info = {'path' : partial_path, 'versions' : []}
        info = {'size' : size, 'hash' : hash, 'mtime' : mtime}
        db_info['versions'].append(info)
        with open(db_file_path, 'w') as f:
            json.dump(db_info, f, indent = 4)

    def read_database(self, file_as_cloud_folder):
        db_file_path = os.path.join(file_as_cloud_folder, self.DATABASE_FILE_NAME)
        with open(db_file_path) as f:
            db = json.load(f)
        return db