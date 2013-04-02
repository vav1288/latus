
# latus-wide testing routines

import os
import shutil

SRC = u"src"
DEST_EMPTY = u"dest_empty"
DEST_EXISTS_EXACT = u"dest_exists_exact"
DEST_EXISTS_DIFFERENT = u"dest_exists_different"
DEST_EXISTS_UNDER_DIFFERENT_NAME = u"dest_exists_under_different_name"

N_UNICODE = 63
TEST_MAX_CODE = 8192

class test_latus():
    def __init__(self):
        self.files_written = 0

    # This writes various input files.  The goal is to not have to package up test files in the repo, if we
    # can avoid it.  Also, this way we can readily re-initialize and fully clean up test files.
    #
    # todo: determine if we already have these written out so we can avoid time consuming deletes and re-writes
    def write_files(self):
        test_string = "a"
        different_test_string = "b"
        a_file_name = u"a.txt"
        # todo: see if the directories already exist, and if so don't re-create them (speeds up testing)
        removed = False
        while not removed:
            try:
                shutil.rmtree(get_root())
                removed = True
            except:
                pass
        self.write_to_file(os.path.join(get_simple_root(), SRC, a_file_name), test_string)
        make_dirs(os.path.join(get_simple_root(), DEST_EMPTY))
        self.write_to_file(os.path.join(get_simple_root(), DEST_EXISTS_EXACT, a_file_name), test_string)
        self.write_to_file(os.path.join(get_simple_root(), DEST_EXISTS_DIFFERENT, a_file_name), different_test_string)
        self.write_to_file(os.path.join(get_simple_root(), DEST_EXISTS_UNDER_DIFFERENT_NAME, u"a_but_different_name.txt"), test_string)
        self.write_unicode_files(get_unicode_root(), test_string)

    # note that this makes the required dirs if necessary
    def write_to_file(self, p, contents):
        #print "p", p
        make_dirs(os.path.split(p)[0])
        f = open(p, "w")
        f.write(contents)
        f.close()
        self.files_written += 1

    def write_unicode_files(self, root_dir, test_string):
        paths = get_unicode_file_paths(root_dir)
        for file_path in paths:
            self.write_to_file(file_path, test_string)

    def number_of_files_written(self):
        return self.files_written

def get_root():
    return u"test"

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
