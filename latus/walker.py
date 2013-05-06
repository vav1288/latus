import os
import msvcrt

from . import const, util

class walker:
    def __init__(self, root):
        self.root = util.decode_text(root) # safety net for str root paths that have unicode children

    def __iter__(self):
        return next(self)

    def create_partial_path(self, name, dirpath):
        p = os.path.join(dirpath, name)
        full_abs_path = os.path.abspath(p)
        root_abs_path = os.path.abspath(self.root)
        partial_path = full_abs_path.replace(root_abs_path, "")
        if partial_path[0] == util.get_folder_sep():
            # Generally these strings end up with an extra separator at the start we need to remove.
            # These should cover both Windows and Linux.
            partial_path = partial_path[1:]
        return partial_path

    def __next__(self):
        for dirpath, dirnames, filenames in os.walk(self.root):
            metadata_dir_name = const.METADATA_DIR_NAME
            # todo: also check that it's a hidden directory before we decide to remove it (at least in Windows)
            if metadata_dir_name in dirnames:
                # don't visit metadata directories (see os.walk docs - this is a little tricky)
                dirnames.remove(metadata_dir_name)
            if msvcrt.kbhit():
                print ("keyboard interrupt")
                break
            else:
                for name in filenames:
                    partial_path = self.create_partial_path(name, dirpath)
                    yield partial_path # just the part to the right of the 'root'
                for name in dirnames:
                    # note the separator delineates a folder/directory
                    partial_path = self.create_partial_path(name, dirpath) + util.get_folder_sep()
                    yield partial_path

    def get_path(self, partial_path):
        #print(partial_path)
        p = os.path.join(self.root, partial_path)
        if partial_path[:-1] == util.get_folder_sep():
            # folder/directory
            p += util.get_folder_sep()
        #print(p)
        return p