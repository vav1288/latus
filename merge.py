
# merge - merge two directories (aka folders)

import copy
import os
import platform
import pywintypes
import win32api, win32con
import msvcrt
import logging
import logger
import hash

EXISTS_EXACT, EXISTS_ELSEWHERE, EXISTS_CONFLICT, DOES_NOT_EXIST = tuple(range(4))
COMMAND_COPY, COMMAND_MOVE = tuple(range(2))

def str_to_command(str):
    command = COMMAND_MOVE
    c = str[0].lower()
    if c == 'c':
        COMMAND_COPY
    return command

def command_to_str(command):
    str = None
    if command == COMMAND_MOVE:
        str = "move"
    elif command == COMMAND_COPY:
        str = "copy"
    return str

def search_result_to_str(search_result):
    str = None
    if search_result == DOES_NOT_EXIST:
        str = "does_not_exist"
    elif search_result == EXISTS_CONFLICT:
        str = "conflict"
    elif search_result == EXISTS_ELSEWHERE:
        str = "exists_elsewhere"
    elif search_result == EXISTS_EXACT:
        str = "exists_exact"
    elif search_result is None:
        str = "not_accessible"
    return str

class merge:
    def __init__(self, source_root, dest_root = None, verbose = False, metadata_root_override = None, command = COMMAND_MOVE):
        self.log = logging.getLogger(__name__)
        self.log_handlers = logger.setup(self.log)

        self.command = command
        self.verbose = verbose
        self.metadata_path = None

        self.dest_root = dest_root
        self.source_root = source_root

        self.log.info('"computer","%s"',platform.node())
        self.log.info('"source_root","%s"',self.source_root)
        if self.dest_root is not None:
            self.log.info('"dest_root","%s"', self.dest_root)

        if metadata_root_override is not None:
            self.metadata_path = metadata_root_override
            if self.verbose:
                print "metadata_path :", self.metadata_path

        self.hash_obj = hash.hash(self.metadata_path)

    def __iter__(self):
        return self.next()

    def next(self):
        for dirpath, dirnames, filenames in os.walk(self.source_root):
            metadata_dir_name = self.hash_obj.get_metadata_dir_name()
            if metadata_dir_name in dirnames:
                # don't visit metadata directories (see os.walk docs - this is a little tricky)
                dirnames.remove(metadata_dir_name)
            if msvcrt.kbhit():
                print ("keyboard interrupt")
                break
            else:
                for name in filenames:
                    full_abs_path = os.path.abspath(os.path.join(dirpath, name))
                    abs_source_path = os.path.abspath(self.source_root)
                    path = full_abs_path.replace(abs_source_path,"")
                    if (path[0] == "\\") or (path[0] == "/"):
                        # Generally these strings end up with an extra separator at the start we need to remove.
                        # These should cover both Windows and Linux.
                        path = path[1:]
                    yield path # just the part to the right of the source 'root'

    # Analyze a single file.
    # Path is the partial path from the 'root' of the source (or dest).
    def analyze_file(self, path):
        result = None
        found_paths = None
        dest_path = os.path.join(self.dest_root, path)
        src_hash_obj = hash.hash(self.metadata_path)
        dest_hash_obj = hash.hash(self.metadata_path)
        dest_dir_abs_path_no_drive = os.path.abspath(self.dest_root)[2:]
        attrib = 0
        try:
            source_path = os.path.join(self.source_root, path)
            # Trick to get around 260 char limit
            # http://msdn.microsoft.com/en-us/library/aa365247.aspx#maxpath
            abs_source_path = u"\\\\?\\" + os.path.abspath(source_path)
            #abs_source_path = os.path.abspath(source_path) # the old simple way ...
            attrib = win32api.GetFileAttributes(abs_source_path)
        except pywintypes.error, details:
            self.log.error(str(details) + "," + source_path)
        except UnicodeDecodeError, details:
            self.log.error(str(details) + "," + source_path)
        # todo: make this check an option
        if not (attrib & win32con.FILE_ATTRIBUTE_HIDDEN or attrib & win32con.FILE_ATTRIBUTE_SYSTEM):
            source_hash, source_cache_flag = src_hash_obj.get_hash(source_path)
            dest_hash, dest_cache_flag = dest_hash_obj.get_hash(dest_path)
            if source_hash == dest_hash:
                result = EXISTS_EXACT
                found_paths = dest_path
            else:
                if os.path.exists(dest_path):
                    # not the same contents, but already exists
                    result = EXISTS_CONFLICT
                else:
                    # Doesn't exist at dest, but first see if it exists anywhere
                    # in order to avoid making redundant copies.
                    found_paths = None
                    paths_from_hash = dest_hash_obj.get_paths_from_hash(source_hash, os.path.splitdrive(os.path.abspath(self.dest_root))[1])
                    # remove the 'source' entry in the list as well as any others that are outside of dest
                    if paths_from_hash is not None:
                        for single_path_from_hash in copy.copy(paths_from_hash):
                            if single_path_from_hash.find(dest_dir_abs_path_no_drive) != 0:
                                paths_from_hash.remove(single_path_from_hash)
                        if len(paths_from_hash) > 0:
                            found_paths = paths_from_hash
                    if found_paths is None:
                        result = DOES_NOT_EXIST
                    else:
                        result = EXISTS_ELSEWHERE
        #print result, found_paths
        return result, found_paths

    # Merge a file.
    # file_path is the path inside the src or dest (the 'right side' of the path, removing the source root)
    def merge_file(self, file_path):
        search_result, search_paths = self.analyze_file(file_path)
        if self.dest_root is not None:
            # if there is no dest_path, then we are merely indexing
            # todo: does it make sense to separate out the indexing capability from the merging?  It seems confusing for them to be 'one thing'.
            if search_result == DOES_NOT_EXIST:
                print command_to_str(self.command), os.path.join(self.source_root, file_path), os.path.join(self.dest_root, file_path)
            else:
                print "REM" , search_result_to_str(search_result), os.path.join(self.source_root, file_path), os.path.join(self.dest_root, file_path)
        return search_result, search_paths

    # Recursively scan a directory and write to the database
    def scan(self, root_dir):
        if self.verbose:
            print "Scanning :", root_dir
        hash_obj = hash.hash(self.metadata_path)
        for dirpath, dirnames, filenames in os.walk(root_dir):
            for name in filenames:
                path = os.path.join(dirpath, name)
                source_hash, source_cache_flag = hash_obj.get_hash(path)
                # print source_hash, source_cache_flag
        if self.verbose:
            print "Scanning complete"

    def run(self):
        if self.verbose:
            print "REM", __name__
            print "REM source", self.source_root
            if self.dest_root is not None:
                print "REM dest", self.dest_root
        if not os.path.exists(self.source_root):
            print "Source does not exist :", self.source_root
            print "Exiting"
            return False
        if self.dest_root is None:
            if self.verbose:
                print "No dest given - doing a scan on source only"
            self.scan(self.source_root)
        else:
            self.scan(self.dest_root)
            for path in self:
                self.merge_file(path)

    def clean(self):
        hash_obj = hash.hash(self.metadata_path)
        hash_obj.clean()

if __name__ == "__main__":
    print "Do not use this program directly."
    print "Use merge_cli."