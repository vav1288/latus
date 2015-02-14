
import os
import win32api

import latus.util

# setup wizard

class Wizard():
    def __init__(self):
        pass

    def try_dropbox_folder(self, candidate_path):
        # candidate_path is that folder that potentially contains the dropbox folder
        cloud_folder = None
        # dropbox appears to use this layout ...
        candidate = os.path.join(candidate_path, 'Dropbox')
        if os.path.exists(candidate) and os.path.exists(os.path.join(candidate, '.dropbox')):
            cloud_folder = candidate
        return cloud_folder

    def find_cloud_folder(self, exhaustive=False):
        cloud_folders = []
        home_folder = os.path.expanduser('~')
        # first, try the normal location
        if self.try_dropbox_folder(home_folder):
            cloud_folders.append(self.try_dropbox_folder(home_folder))
        if exhaustive or len(cloud_folders) == 0:
            # If we couldn't find a cloud folder in the normal location, search more possible
            # locations (will take longer).
            roots = []
            if latus.util.is_windows():
                drives = win32api.GetLogicalDriveStrings().split('\0')[:-1]
                for drive in drives:
                    root = os.path.join(drive, os.sep)
                    if os.path.exists(os.path.join(root, 'Windows')):
                        # only look in the user area for the drive that has Windows, etc.
                        roots.append(home_folder)
                    else:
                        roots.append(root)
            elif latus.util.is_linux():
                pass  # todo: get possible location roots for Linux
            for root in roots:
                candidate = self.try_dropbox_folder(root)
                if candidate:
                    if candidate not in cloud_folders:
                        cloud_folders.append(candidate)
                for path, dirs, _ in os.walk(root):
                    for d in dirs:
                        candidate = self.try_dropbox_folder(os.path.join(path, d))
                        if candidate:
                            if candidate not in cloud_folders:
                                cloud_folders.append(candidate)
        return cloud_folders

if __name__ == "__main__":
    w = Wizard()
    print(w.find_cloud_folder())
    print(w.find_cloud_folder(True))