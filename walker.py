
import os
import const
import msvcrt

def get_long_abs_path(in_path):
    # Trick to get around 260 char limit
    # http://msdn.microsoft.com/en-us/library/aa365247.aspx#maxpath
    return u"\\\\?\\" + os.path.abspath(in_path)

class walker:
    def __init__(self, root):
        self.root = root

    def __iter__(self):
        return self.next()

    def next(self):
        for dirpath, dirnames, filenames in os.walk(self.root):
            metadata_dir_name = const.METADATA_DIR_NAME
            if metadata_dir_name in dirnames:
                # don't visit metadata directories (see os.walk docs - this is a little tricky)
                dirnames.remove(metadata_dir_name)
            if msvcrt.kbhit():
                print ("keyboard interrupt")
                break
            else:
                for name in filenames:
                    full_abs_path = os.path.abspath(os.path.join(dirpath, name))
                    root_abs_path = os.path.abspath(self.root)
                    partial_path = full_abs_path.replace(root_abs_path, "")
                    if (partial_path[0] == u"\\") or (partial_path[0] == u"/"):
                        # Generally these strings end up with an extra separator at the start we need to remove.
                        # These should cover both Windows and Linux.
                        partial_path = partial_path[1:]
                    yield partial_path # just the part to the right of the 'root'

    def get_path(self, partial_path):
        return os.path.join(self.root, partial_path)