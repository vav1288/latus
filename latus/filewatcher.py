
import threading
import win32file, win32con, win32event


class FileWatcher(threading.Thread):

    def __init__(self, folder, do_sync):
        threading.Thread.__init__(self)
        self.exit_flag = False
        self.folder = folder
        self.do_sync = do_sync  # call this upon detecting a file change
        self.file_change_event = threading.Event()  # this is set to inform the user of this class of a file change
        self.exit_request_event_handle = win32event.CreateEvent(None, 0, 0, None)

    def get_event(self):
        return self.file_change_event

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
        change_handle = win32file.FindFirstChangeNotification(self.folder, 0,
                                                              win32con.FILE_NOTIFY_CHANGE_FILE_NAME)

        # This order is important.  If multiple events are triggered, only the lowest index is
        # indicated.  So, the exit event must be the lowest index or else we could miss
        # the exit event if it happens as the same time as a file system change.
        wait_objects = [self.exit_request_event_handle, change_handle]

        while not self.exit_flag:
            result = win32event.WaitForMultipleObjects(wait_objects, 0, 60 * 1000)
            if result == win32con.WAIT_OBJECT_0:
                self.exit_flag = True
            elif result == win32con.WAIT_OBJECT_0 + 1:
                self.sync()
                win32file.FindNextChangeNotification(change_handle)
                # todo: use win32file.ReadDirectoryChangesW() to provide the particular files/folders that changed
        win32file.FindCloseChangeNotification(change_handle)

