
# latus-wide testing routines

import os
import shutil
import time
import win32api
from .. import util, const

SRC = "src"
DEST = "dest"
DEST_EMPTY = "dest_empty"
DEST_EXISTS_EXACT = "dest_exists_exact"
DEST_EXISTS_DIFFERENT = "dest_exists_different"
DEST_EXISTS_UNDER_DIFFERENT_NAME = "dest_exists_under_different_name"
DEST_BEST = "dest_best"
DEST_CONFLICT = "dest_conflict"
NON_EXECUTION_DRIVE_TEST_FILES = ["a.txt", "aa.txt"]

# something to give good unicode coverage ...
N_UNICODE = 63
SMALL_MAX_CODE = 512
BIG_MAX_CODE = 8192

class test_latus():

    # This writes various input files.  The goal is to not have to package up test files in the repo, if we
    # can avoid it.  Also, this way we can readily re-initialize and fully clean up test files.
    def write_files(self, force = False, write_flag = True):
        a_test_string = "a"
        b_test_string = "b"
        c_test_string = "c"
        a_file_name = "a.txt"
        b_file_name = "b.txt"
        c_file_name = "c.txt"

        self.files_written = 0

        # todo: this doesn't delete the files used only for testing - update it somehow to the new format
        # that has the test name in the metadata file.

        util.del_files((os.path.join(get_root(), const.METADATA_DIR_NAME, const.LFS_DB_NAME + const.DB_EXT),
                       os.path.join(get_simple_root(), const.METADATA_DIR_NAME, const.LFS_DB_NAME + const.DB_EXT),
                       os.path.join(get_simple_root(), const.OUTPUT_FILE)))

        if force or not os.path.exists(get_simple_root()):
            self.write_to_file(os.path.join(get_simple_root(), SRC, a_file_name), a_test_string, write_flag)
            make_dirs(os.path.join(get_simple_root(), DEST_EMPTY))
            self.write_to_file(os.path.join(get_simple_root(), DEST_EXISTS_EXACT, a_file_name), a_test_string, write_flag)
            self.write_to_file(os.path.join(get_simple_root(), DEST_EXISTS_DIFFERENT, a_file_name), b_test_string, write_flag)
            self.write_to_file(os.path.join(get_simple_root(), DEST_EXISTS_UNDER_DIFFERENT_NAME, "a_but_different_name.txt"), a_test_string, write_flag)
        if force or not os.path.exists(get_unicode_root()):
            self.write_unicode_files(get_unicode_root(), a_test_string, write_flag)
        if force or not os.path.exists(get_mtime_root()):
            f = os.path.join(get_mtime_root(), a_file_name)
            t = get_mtime_time()
            self.write_to_file(f, a_test_string, write_flag)
            os.utime(f, (t, t))
        if force or not os.path.exists(get_merge_root()):
            self.write_to_file(os.path.join(get_merge_root(), SRC, a_file_name), a_test_string, write_flag)
            self.write_to_file(os.path.join(get_merge_root(), SRC, b_file_name), b_test_string, write_flag)
            self.write_to_file(os.path.join(get_merge_root(), SRC, c_file_name), c_test_string, write_flag)
            self.write_to_file(os.path.join(get_merge_root(), DEST, DEST_BEST, a_file_name), a_test_string, write_flag)
            self.write_to_file(os.path.join(get_merge_root(), DEST, DEST_CONFLICT, a_file_name), b_test_string, write_flag)
            self.write_to_file(os.path.join(get_merge_root(), DEST, DEST_CONFLICT, b_file_name), b_test_string, write_flag)
        if force or not os.path.exists(get_hash_root()):
            self.write_to_file(os.path.join(get_hash_root(), a_file_name), a_test_string, write_flag)
            self.write_to_file(os.path.join(get_hash_root(), b_file_name), b_test_string, write_flag)

        print("files_written:" + str(self.files_written))
        return self.files_written

    # note that this makes the required dirs if necessary
    def write_to_file(self, p, contents, write_flag):
        # turn off writing to enable us to merely count the files we would have written
        # (we need to know how many files written for testing purposes)
        if write_flag:
            #print("writing:" + p)
            d = os.path.dirname(p)
            make_dirs(d)
            f = open(p, "w")
            f.write(contents)
            f.close()
        self.files_written += 1

    def write_unicode_files(self, root_dir, test_string, write_flag):
        paths = get_unicode_file_paths(root_dir)
        for file_path in paths:
            self.write_to_file(file_path, test_string, write_flag)

    def clean(self):
        if os.path.exists(get_root()):
            shutil.rmtree(get_root())

def get_root():
    # must not match nose's regex for test files/directories below the main directory "test",
    # since nose errors out on the unicode files
    return os.path.join("test", "data")

def get_unicode_root():
    return os.path.join(get_root(), "unicode")

def get_simple_root():
    return os.path.join(get_root(), "simple")

def get_mtime_root():
    return os.path.join(get_root(), "mtime")

def get_merge_root():
    return os.path.join(get_root(), "merge")

def get_hash_root():
    return os.path.join(get_root(), "hash")

# get an mtime back in time
def get_mtime_time():
    return time.mktime(time.strptime("12", "%y"))

def make_dirs(p):
    if not os.path.exists(p):
        os.makedirs(p)

def make_unicode_string(start, length, inc = 1):
    out_string = ''
    char_codepoint = start
    # Avoid / and \ so we don't mistakenly create a folder, as well as other illegal filename chars
    illegal_chars = [ '/', "\\", ";", "*", "?", '"', "<", ">", "|", ":"]
    while len(out_string) < length:
        unicode_char = chr(char_codepoint)
        if (char_codepoint >= ord(' ')) and not (unicode_char in illegal_chars):
            out_string = out_string + unicode_char
        char_codepoint = char_codepoint + inc
    return out_string

def get_unicode_file_paths(root_dir):
    paths = []
    space = 32 # ' '
    length = N_UNICODE

    # todo: make these 3 separate tests
    # PICK ONE:
    #max_code = space # omit all unicode - this is required since the sqlite database browser can't read some unicode, apparently
    max_code = SMALL_MAX_CODE - space # small test
    #max_code = BIG_MAX_CODE - space # big test

    for start in range(space, max_code, length):
        # start and end with something always valid
        file_name = 'A' + make_unicode_string(start, length) + '.txt'
        paths.append(os.path.join(root_dir, file_name))
    return paths

# This returns a path that is not on the same drive as we're executing on
# that we can use for testing across drives.  Also writes a file into this dir.
def write_non_execution_test_dir_files():
    candidate_drives = []
    # get the drive letters that aren't what we're currently executing on
    for drive in win32api.GetLogicalDriveStrings().split("\x00"):
        if len(drive) > 0:
            if drive[0] != os.getcwd()[0]:
                candidate_drives.append(drive[0])
    dir = None
    # now, see which drive we can use - i.e. is writable
    for drive in candidate_drives:
        if dir is None:
            dir_to_try = os.path.join(drive + ":", "/", "temp", const.NAME, get_root())
            if os.path.exists(dir_to_try):
                dir = dir_to_try
            else:
                try:
                    os.makedirs(dir_to_try)
                    dir = dir_to_try
                except:
                    pass
            if dir is not None:
                try:
                    for file_name in NON_EXECUTION_DRIVE_TEST_FILES:
                        with open(os.path.join(dir, file_name), "w") as f:
                            f.write("a")
                except:
                    dir = None
    return dir


