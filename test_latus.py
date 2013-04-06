
# latus-wide testing routines

import os
import logging
import const
import util

SRC = u"src"
DEST_EMPTY = u"dest_empty"
DEST_EXISTS_EXACT = u"dest_exists_exact"
DEST_EXISTS_DIFFERENT = u"dest_exists_different"
DEST_EXISTS_UNDER_DIFFERENT_NAME = u"dest_exists_under_different_name"

N_UNICODE = 63
TEST_MAX_CODE = 8192

class test_latus():

    # This writes various input files.  The goal is to not have to package up test files in the repo, if we
    # can avoid it.  Also, this way we can readily re-initialize and fully clean up test files.
    #
    # todo: determine if we already have these written out so we can avoid time consuming deletes and re-writes
    def write_files(self, force = False, write_flag = True):
        test_string = u"a"
        different_test_string = u"b"
        a_file_name = u"a.txt"

        self.files_written = 0
        util.del_files((os.path.join(get_root(), const.METADATA_DIR_NAME, const.LFS_DB_NAME + const.DB_EXT),
                       os.path.join(get_simple_root(), const.METADATA_DIR_NAME, const.LFS_DB_NAME + const.DB_EXT),
                       os.path.join(get_simple_root(), const.OUTPUT_FILE)))

        if force or not os.path.exists(get_simple_root()):
            self.write_to_file(os.path.join(get_simple_root(), SRC, a_file_name), test_string, write_flag)
            make_dirs(os.path.join(get_simple_root(), DEST_EMPTY))
            self.write_to_file(os.path.join(get_simple_root(), DEST_EXISTS_EXACT, a_file_name), test_string, write_flag)
            self.write_to_file(os.path.join(get_simple_root(), DEST_EXISTS_DIFFERENT, a_file_name), different_test_string, write_flag)
            self.write_to_file(os.path.join(get_simple_root(), DEST_EXISTS_UNDER_DIFFERENT_NAME, u"a_but_different_name.txt"), test_string, write_flag)
        if force or not os.path.exists(get_unicode_root()):
            self.write_unicode_files(get_unicode_root(), test_string, write_flag)

        return self.files_written

    # note that this makes the required dirs if necessary
    def write_to_file(self, p, contents, write_flag):
        # turn off writing to enable us to merely count the files we would have written
        # (we need to know how many files written for testing purposes)
        if write_flag:
            make_dirs(os.path.split(p)[0])
            f = open(p, "w")
            f.write(contents)
            f.close()
        self.files_written += 1

    def write_unicode_files(self, root_dir, test_string, write_flag):
        paths = get_unicode_file_paths(root_dir)
        for file_path in paths:
            self.write_to_file(file_path, test_string, write_flag)

def get_root():
    return const.TEST_DIR

def get_unicode_root():
    return os.path.join(get_root(), u"unicode")

def get_simple_root():
    return os.path.join(get_root(), u"simple")

def make_dirs(p):
    if not os.path.exists(p):
        os.makedirs(p)

def make_unicode_string(start, length, inc = 1):
    s = u''
    c = start
    space = 32 # ' '
    # Avoid / and \ so we don't mistakenly create a folder, as well as other illegal filename chars
    illegal_chars = [ u'/', u"\\", u";", u"*", u"?", u'"', u"<", u">", u"|", u":"]
    while len(s) < length:
        if (c >= space) and not (unichr(c) in illegal_chars):
            s = s + unichr(c)
        c = c + inc
    return s

def get_unicode_file_paths(root_dir):
    paths = []
    space = 32 # ' '
    length = N_UNICODE
    max_code =  TEST_MAX_CODE - space # fairly arbitrary max - perhaps this should be a different value?
    for start in range(space, max_code, length):
        # start and end with something always valid
        file_name = u'A' + make_unicode_string(start, length) + u'.txt'
        paths.append(os.path.join(root_dir, file_name))
    return paths

if __name__ == "__main__":
    test = test_latus()
    test.write_files()
