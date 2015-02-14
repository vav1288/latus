
import os
import win32api

import latus.util
import latus.const

# setup wizard

class FolderWizard():
    def __init__(self):
        self.cloud_folders = []

    def get_folders(self):
        return self.cloud_folders

    # child classes can override this to get progress
    def progress(self, path):
        print(path)

    def try_dropbox_folder(self, candidate_path):
        # dropbox appears to use this layout ...
        candidate = os.path.join(candidate_path, 'Dropbox')
        if os.path.exists(candidate) and os.path.exists(os.path.join(candidate, '.dropbox')):
            if candidate not in self.cloud_folders:
                self.cloud_folders.append(candidate)

    def find_folders(self, exhaustive=False):
        self.cloud_folders = []
        home_folder = os.path.expanduser('~')
        # first, try the normal location
        self.try_dropbox_folder(home_folder)
        if exhaustive or len(self.cloud_folders) == 0:
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
                self.progress(root)
                for path, dirs, _ in os.walk(root):
                    for d in dirs:
                        candidate = os.path.join(path, d)
                        self.try_dropbox_folder(candidate)
                        self.progress(candidate)
        return self.cloud_folders

    def latus_folder(self):
        return os.path.join(os.path.dirname(self.cloud_folders[0]), latus.const.NAME)

if __name__ == "__main__":
    w = FolderWizard()
    print(w.find_folders())
    print(w.find_folders(True))