
# from:
# http://timgolden.me.uk/python/win32_how_do_i/watch_directory_for_changes.html
# http://www.themacaque.com/?p=859

import win32con, win32file, win32event, pywintypes

class Watcher():
    def __init__(self, timeout = 60 * 60 * 1000):
        self.timeout = timeout # mS
        # NB Tim Juchcinski reports that he needed to up
        # the buffer size to be sure of picking up all
        # events when a large number of files were
        # deleted at once.
        size = 64 * 1024
        self.buffer = win32file.AllocateReadBuffer( size )

    # either a directory change or an external "pulse" can trigger this event
    def create_change_event(self):
        self.overlapped = pywintypes.OVERLAPPED()
        self.overlapped.hEvent = win32event.CreateEvent(None, 0, 0, None)
        return self.overlapped.hEvent

    def wait(self, path_to_watch):
        change_flag = False

        self.ACTIONS = {
          1 : "Created",
          2 : "Deleted",
          3 : "Updated",
          4 : "Renamed from something",
          5 : "Renamed to something"
        }

        # Thanks to Claudio Grondi for the correct set of numbers
        FILE_LIST_DIRECTORY = 0x0001

        handle = win32file.CreateFile (
            path_to_watch,
            FILE_LIST_DIRECTORY,
            win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE,
            None,
            win32con.OPEN_EXISTING,
            win32con.FILE_FLAG_BACKUP_SEMANTICS | win32file.FILE_FLAG_OVERLAPPED,
            None
        )

        results = win32file.ReadDirectoryChangesW (
            handle,
            self.buffer,
            True, # subtree
            win32con.FILE_NOTIFY_CHANGE_FILE_NAME | win32con.FILE_NOTIFY_CHANGE_DIR_NAME |
            win32con.FILE_NOTIFY_CHANGE_ATTRIBUTES | win32con.FILE_NOTIFY_CHANGE_SIZE |
            win32con.FILE_NOTIFY_CHANGE_LAST_WRITE | win32con.FILE_NOTIFY_CHANGE_SECURITY,
            self.overlapped
            )

        # Wait for our event or timeout
        rc = win32event.WaitForSingleObject(self.overlapped.hEvent, self.timeout)
        if rc == win32event.WAIT_OBJECT_0:
            change_flag = True
        return change_flag

