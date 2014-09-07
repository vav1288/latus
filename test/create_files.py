
"""
create the test files
"""

import os
import shutil
import random

from core import const
import core.logger
import test.const
import test.util

SRC = "src"
DEST = "dest"
DEST_EMPTY = "dest_empty"
DEST_EXISTS_EXACT = "dest_exists_exact"
DEST_EXISTS_DIFFERENT = "dest_exists_different"
DEST_EXISTS_UNDER_DIFFERENT_NAME = "dest_exists_under_different_name"
DEST_BEST = "dest_best"
DEST_CONFLICT = "dest_conflict"

A_STRING = "a"
B_STRING = "b"
C_STRING = "c"
A_FILE_NAME = "a.txt"
B_FILE_NAME = "b.txt"
C_FILE_NAME = "c.txt"

# something to give good unicode coverage ...
UNICODE_FILE_NAME_LENGTH = 63
SMALL_MAX_CODE = 512
BIG_MAX_CODE = 8192

y_folder_files = None


def get_data_root():
    return os.path.join("test", "data")


def get_files_root():
    return os.path.join(get_data_root(), "files")


def get_metadata_root():
    # must not match nose's regex for test_latus files/directories below the main directory "test_latus",
    # since nose errors out on the unicode files
    return os.path.join(get_data_root(), "metadata")


def get_unicode_root():
    return os.path.join(get_files_root(), "unicode")


def get_simple_root():
    return os.path.join(get_files_root(), "simple")


def get_mtime_root():
    return os.path.join(get_files_root(), "mtime")


def get_merge_root():
    return os.path.join(get_files_root(), "merge")


def get_compare_root():
    return os.path.join(get_files_root(), "compare")


def get_hash_root():
    return os.path.join(get_files_root(), "hash")


def get_random_roots():
    root = os.path.join(get_files_root(), "random")
    return os.path.join(root, 'a'), os.path.join(root, 'b')


class SyncNodesTestInfo():
    nodes = ['a', 'b']
    folder_names = ['latus', 'dropbox']
    def __init__(self):
        self.sync_root = os.path.join(get_files_root(), "sync")

    def write(self):
        for node in self.nodes:
            for folder_name in self.folder_names:
                os.makedirs(os.path.join(self.sync_root, node, folder_name))

    def get_local_folder(self, node):
        return os.path.join(self.sync_root, node, self.folder_names[0])

    def get_cloud_folder(self, node):
        return os.path.join(self.sync_root, node, self.folder_names[1])

    def get_file_name(self, node):
        return node + '.txt'


def clean(do_all):
    """
    clean up the test data
    :param do_all: True to delete all test files and metadata, False for test files only.
    :return:
    """
    path = get_files_root()
    if do_all:
        path = get_data_root()
    core.logger.log.info("cleaning:" + path)
    if os.path.exists(path):
        shutil.rmtree(path)


class TestFiles():
    def __init__(self):
        self.files_written = 0

    # This writes various input files.  The goal is to not have to package up test_latus files in the repo, if we
    # can avoid it.  Also, this way we can readily re-initialize and fully clean up test_latus files.
    def write_files(self, force = False, write_flag = True):

        self.files_written = 0

        if force or not os.path.exists(get_simple_root()):
            self.write_to_file(os.path.join(get_simple_root(), SRC, A_FILE_NAME), A_STRING, write_flag)
            test.util.make_dirs(os.path.join(get_simple_root(), DEST_EMPTY))
            self.write_to_file(os.path.join(get_simple_root(), DEST_EXISTS_EXACT, A_FILE_NAME), A_STRING, write_flag)
            self.write_to_file(os.path.join(get_simple_root(), DEST_EXISTS_DIFFERENT, A_FILE_NAME), B_STRING, write_flag)
            self.write_to_file(os.path.join(get_simple_root(), DEST_EXISTS_UNDER_DIFFERENT_NAME, "a_but_different_name.txt"), A_STRING, write_flag)
        if force or not os.path.exists(get_unicode_root()):
            self.write_unicode_files(get_unicode_root(), A_STRING, write_flag)
        if force or not os.path.exists(get_mtime_root()):
            f = os.path.join(get_mtime_root(), A_FILE_NAME)
            t = test.util.get_mtime_time()
            self.write_to_file(f, A_STRING, write_flag)
            os.utime(f, (t, t))
        if force or not os.path.exists(get_merge_root()):
            self.write_to_file(os.path.join(get_merge_root(), SRC, A_FILE_NAME), A_STRING, write_flag)
            self.write_to_file(os.path.join(get_merge_root(), SRC, B_FILE_NAME), B_STRING, write_flag)
            self.write_to_file(os.path.join(get_merge_root(), SRC, C_FILE_NAME), C_STRING, write_flag)
            self.write_to_file(os.path.join(get_merge_root(), DEST, DEST_BEST, A_FILE_NAME), A_STRING, write_flag)
            self.write_to_file(os.path.join(get_merge_root(), DEST, DEST_CONFLICT, A_FILE_NAME), B_STRING, write_flag)
            self.write_to_file(os.path.join(get_merge_root(), DEST, DEST_CONFLICT, B_FILE_NAME), B_STRING, write_flag)
        if force or not os.path.exists(get_hash_root()):
            self.write_to_file(os.path.join(get_hash_root(), A_FILE_NAME), A_STRING, write_flag)
            self.write_to_file(os.path.join(get_hash_root(), B_FILE_NAME), B_STRING, write_flag)
            for big_count in range(test.const.HASH_TEST_FILE_MIN, test.const.HASH_TEST_FILE_MAX + 1):
                # use an exponentially increasing size so we have a large difference in hash times (since time is often imprecise)
                self.write_big_file(os.path.join(get_hash_root(), test.const.HASH_TEST_FILE_PREFIX + str(big_count) + test.const.HASH_TEST_FILE_SUFFIX),
                                    pow(1.3, big_count)*test.const.HASH_TEST_BASE_FILE_SIZE, write_flag)
        if force or not os.path.exists(get_compare_root()):
            self.write_to_file(os.path.join(get_compare_root(), test.const.X_FOLDER, A_FILE_NAME), A_STRING, write_flag)
            self.write_to_file(os.path.join(get_compare_root(), test.const.X_FOLDER, B_FILE_NAME), B_STRING, write_flag)

            global y_folder_files
            self.write_to_file(os.path.join(get_compare_root(), test.const.Y_FOLDER, B_FILE_NAME), B_STRING, write_flag)
            y_folder_files = [os.path.join(test.const.Y_FOLDER, B_FILE_NAME)] # keep a list of files in y folder
            self.write_to_file(os.path.join(get_compare_root(), test.const.Y_FOLDER, C_FILE_NAME), C_STRING, write_flag)
            y_folder_files.append(os.path.join(test.const.Y_FOLDER, C_FILE_NAME))
        if force or not os.path.exists(get_random_roots()[0]):
            self.write_pseudo_random_files(write_flag)

        sync_nodes = SyncNodesTestInfo()
        if force or not os.path.exists(sync_nodes.sync_root):
            for node in sync_nodes.nodes:
                self.write_to_file(os.path.join(sync_nodes.get_local_folder(node), sync_nodes.get_file_name(node)), node, write_flag)

        core.logger.log.info("files_written:" + str(self.files_written))
        return self.files_written

    def write_big_file(self, path, size, write_flag):
        if write_flag or not os.path.exists(path):
            with open(path,'w') as f:
                f.seek(size-1) # trick to make the write fast
                f.write('\0')

    def write_to_file(self, p, contents, write_flag):
        """
        makes the required dirs if necessary
        """
        # turn off writing to enable us to merely count the files we would have written
        # (we need to know how many files written for testing purposes)
        if write_flag:
            #print("writing:" + p)
            d = os.path.dirname(p)
            test.util.make_dirs(d)
            f = open(p, "w")
            f.write(contents)
            f.close()
        self.files_written += 1

    def write_unicode_files(self, root_dir, test_string, write_flag):
        paths = self.get_unicode_file_paths(root_dir)
        for file_path in paths:
            self.write_to_file(file_path, test_string, write_flag)

    def make_unicode_string(self, start, length, inc = 1):
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

    def get_unicode_file_paths(self, root_dir):
        paths = []
        space = 32 # ' '

        # todo: make these 3 separate tests
        # PICK ONE:
        #max_code = space # omit all unicode - this is required since the sqlite database browser can't read some unicode, apparently
        max_code = SMALL_MAX_CODE - space # small test_latus
        #max_code = BIG_MAX_CODE - space # big test_latus

        for start in range(space, max_code, UNICODE_FILE_NAME_LENGTH):
            # start and end with something always valid
            file_name = 'A' + self.make_unicode_string(start, UNICODE_FILE_NAME_LENGTH) + '.txt'
            paths.append(os.path.join(root_dir, file_name))
        return paths

    def write_pseudo_random_files(self, write_flag):

        def one_entry_in_both(xs, ys):
            found = False
            for xk in xs.keys():
                for yk in ys.keys():
                    if xk == yk and xs[xk] == ys[yk]:
                        # done if there is one entry in both x and y
                        found = True
            return found

        def write_files(root, contents):
            for level_0 in contents.keys():
                for level_1 in contents[level_0].keys():
                    path = os.path.join(root, level_0, level_1 + '.txt')
                    self.write_to_file(path, contents[level_0][level_1], write_flag)

        random.seed(0) # make this deterministic
        base_ord = ord('a')
        span = 3 # larger span causes larger number of files
        c_range = range(base_ord, base_ord + span)
        choices = [chr(c) + chr(c2) for c in c_range for c2 in c_range]

        a = {}
        b = {}
        while not one_entry_in_both(a,b):
            a[random.choice(choices)] = { random.choice(choices) : random.choice(choices) }
            b[random.choice(choices)] = { random.choice(choices) : random.choice(choices) }
        a_folder, b_folder = get_random_roots()
        write_files(a_folder, a)
        write_files(b_folder, b)



