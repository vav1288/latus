import os

from . import util
from latus import const

class Walker:
    def __init__(self, root, do_dirs = False, ignore = []):
        """
        root: the directory to start the walk from
        do_dirs: if True, return directories (as opposed to only files).
        ignore: a list of folder/directory names to not traverse (e.g. metadata folder names)
        """
        self.root = root
        self.do_dirs = do_dirs
        self.ignore = ignore
        self.keyboard_hit_exit = False

    def __iter__(self):
        return next(self)

    def create_partial_path(self, name, dirpath):
        p = os.path.join(dirpath, name)
        full_abs_path = os.path.abspath(p)
        root_abs_path = os.path.abspath(self.root)
        partial_path = full_abs_path.replace(root_abs_path, "")
        if partial_path[0] == util.get_folder_sep():
            # Generally these strings end up with an extra separator at the start we need to remove.
            # This should cover both Windows and Linux.
            partial_path = partial_path[1:]
        return partial_path

    def __next__(self):
        # provides just the part to the right of the 'root'
        for dirpath, dirnames, filenames in os.walk(self.root):
            # todo: also check that it's a hidden directory before we decide to remove it (at least in Windows)
            for folder in self.ignore:
                if folder in dirnames:
                    dirnames.remove(folder)

            # do the directories/folders first
            for name in dirnames:
                # note the separator delineates a folder/directory
                partial_path = self.create_partial_path(name, dirpath) + util.get_folder_sep()
                if self.check_exit():
                    break
                else:
                    yield partial_path

            for name in filenames:
                partial_path = self.create_partial_path(name, dirpath)
                if self.check_exit():
                    break
                else:
                    yield partial_path

    def full_path(self, partial_path):
        return os.path.join(self.root, partial_path)



