
import os
import win32api
import threading
import time

import latus.util
import latus.const

# setup wizard


class FolderWizard(threading.Thread):

    def __init__(self):
        super().__init__()
        self.potential_cloud_folders = []
        self.selected_latus_folder = None
        self.found_alert = self.default_found_alert
        self.progress = self.default_progress
        self.request_exit_flag = False

    def default_found_alert(self, _):
        print('default_found_alert')

    def default_progress(self, _):
        print('default_progress')

    def set_found_alert(self, method):
        self.found_alert = method

    def set_progress(self, method):
        self.progress = method

    def get_potential_cloud_folders(self):
        return self.potential_cloud_folders

    def request_exit(self):
        self.request_exit_flag = True

    def try_dropbox_folder(self, candidate_path):
        # dropbox appears to use this layout ...
        candidate = os.path.join(candidate_path, 'Dropbox')
        if os.path.exists(candidate) and os.path.exists(os.path.join(candidate, '.dropbox')):
            if candidate not in self.potential_cloud_folders:
                self.potential_cloud_folders.append(candidate)
                if self.found_alert:
                    self.found_alert(self.potential_cloud_folders)

    def run(self):
        self.potential_cloud_folders = []
        home_folder = os.path.expanduser('~')
        # first, try the normal location
        self.try_dropbox_folder(home_folder)

        # Search more possible locations (will take longer).
        roots = []
        if latus.util.is_windows():
            drives = win32api.GetLogicalDriveStrings().split('\0')[:-1]
            for drive in drives:
                root = os.path.join(drive, os.sep)
                if os.path.exists(os.path.join(root, 'Windows')):
                    # only look in the user area for the drive that has Windows, Program Files, etc.
                    roots.append(home_folder)
                else:
                    roots.append(root)
        elif latus.util.is_linux():
            pass  # todo: get possible location roots for Linux
        for root in roots:
            self.try_dropbox_folder(root)
            for path, dirs, _ in os.walk(root):
                for d in dirs:
                    if self.request_exit_flag:
                        return
                    candidate = os.path.join(path, d)
                    self.try_dropbox_folder(candidate)
                    self.progress(candidate)
        self.progress(None)


def latus_folder_from_cloud_folder(path):
    return os.path.join(os.path.dirname(path), latus.const.NAME)

if __name__ == "__main__":
    def my_alert(folders):
        print(folders)

    w = FolderWizard()
    w.set_found_alert(my_alert)
    w.start()
    while w.is_alive():
        time.sleep(0.1)
    print('Done!')
    print(w.get_potential_cloud_folders())
