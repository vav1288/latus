
import threading
import win32file, win32con, win32event
import latus.logger

class FileWatcher(threading.Thread):

    def __init__(self, folder, sync_method):
        threading.Thread.__init__(self)
        self.exit_flag = False
        self.folder = folder
        self.sync_method = sync_method  # call this upon detecting a file change
        self.file_change_event = threading.Event()  # this is set to inform the user of this class of a file change
        self.exit_request_event_handle = win32event.CreateEvent(None, 0, 0, None)

    def request_exit(self):
        """
        Call this to cause this thread to exit.
        """
        self.exit_flag = True
        win32event.PulseEvent(self.exit_request_event_handle)

    def run(self):
        #
        # FindFirstChangeNotification sets up a handle for watching
        #  file changes. The first parameter is the path to be
        #  watched; the second is a boolean indicating whether the
        #  directories underneath the one specified are to be watched;
        #  the third is a list of flags as to what kind of changes to
        #  watch for. We're just looking at file additions / deletions.
        #
        latus.logger.log.info('watching : %s' % self.folder)

        filter = win32con.FILE_NOTIFY_CHANGE_FILE_NAME
        filter |= win32con.FILE_NOTIFY_CHANGE_DIR_NAME
        filter |= win32con.FILE_NOTIFY_CHANGE_DIR_NAME
        filter |= win32con.FILE_NOTIFY_CHANGE_ATTRIBUTES
        filter |= win32con.FILE_NOTIFY_CHANGE_SIZE
        filter |= win32con.FILE_NOTIFY_CHANGE_LAST_WRITE
        filter |= win32con.FILE_NOTIFY_CHANGE_SECURITY

        change_handle = win32file.FindFirstChangeNotification(self.folder, 0, filter)

        # This order is important.  If multiple events are triggered, only the lowest index is
        # indicated.  So, the exit event must be the lowest index or else we could miss
        # the exit event if it happens as the same time as a file system change.
        wait_objects = [self.exit_request_event_handle, change_handle]

        while not self.exit_flag:
            latus.logger.log.info('WaitForMultipleObjects - %s - calling' % self.folder)
            result = win32event.WaitForMultipleObjects(wait_objects, 0, 600 * 1000)
            latus.logger.log.info('WaitForMultipleObjects - %s - returned' % self.folder)
            if result == win32con.WAIT_OBJECT_0:
                self.exit_flag = True
            elif result == win32con.WAIT_OBJECT_0 + 1:
                latus.logger.log.info('calling sync')
                self.sync_method()
                win32file.FindNextChangeNotification(change_handle)
                # todo: use win32file.ReadDirectoryChangesW() to provide the particular files/folders that changed
        win32file.FindCloseChangeNotification(change_handle)

