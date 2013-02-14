
# latus-wide testing routines

import os

SIMPLE = u"simple"
TEST_UNICODE = u"unicode"
SRC = u"src"
DEST_EMPTY = u"dest_empty"
DEST_EXISTS_EXACT = u"dest_exists_exact"
DEST_EXISTS_DIFFERENT = u"dest_exists_different"
DEST_EXISTS_UNDER_DIFFERENT_NAME = u"dest_exists_under_different_name"

TEST_ROOT = "test"

def get_test_root():
    return TEST_ROOT

# use this instead of logger.py's get_log_file_path() so the log file is put in the proper place for testing
def get_log_file_path():
    return os.path.join(TEST_ROOT, __name__  + u".log")

# note that this makes the required dirs if necessary
def write_to_file(p, contents):
    print "p", p
    make_dirs(os.path.split(p)[0])
    f = open(p, "w")
    f.write(contents)
    f.close()

def make_dirs(p):
    if not os.path.exists(p):
        os.makedirs(p)

def make_unicode_string(start, inc, length):
    s = u''
    c = start
    # Avoid / and \ so we don't mistakenly create a folder, as well as other illegal filename chars
    illegal_chars = [ u'/', u"\\", u";", u"*", u"?", u'"', u"<", u">", u"|", u":"]
    while len(s) < length:
        if (c >= 32) and not (unichr(c) in illegal_chars):
            s = s + unichr(c)
        c = c + inc
    return s

def get_unicode_test_filename():
    # todo : dynamically determine how many chars we can go to in this total path length  ... there seems to be a limit
    return u'A' + make_unicode_string(0, 1, 217) + u'.txt'

# This writes various input files.  The goal is to not have to package up test files in the repo, if we
# can avoid it.  Also, this way we can readily re-initialize and fully clean up test files.
def write_files():
    test_string = "a"
    different_test_string = "b"
    a_file_name = u"a.txt"
    simple_path = os.path.join(get_test_root(), SIMPLE)
    write_to_file(os.path.join(simple_path, SRC, a_file_name), test_string)
    make_dirs(os.path.join(simple_path, DEST_EMPTY))
    write_to_file(os.path.join(simple_path, DEST_EXISTS_EXACT, a_file_name), test_string)
    write_to_file(os.path.join(simple_path, DEST_EXISTS_DIFFERENT, a_file_name), different_test_string)
    write_to_file(os.path.join(simple_path, DEST_EXISTS_UNDER_DIFFERENT_NAME, u"a_but_different_name.txt"), test_string)
    # todo : make the contents unicode characters (write doesn't seem to allow non-ASCII)
    write_to_file(os.path.join(get_test_root(), TEST_UNICODE, get_unicode_test_filename()), test_string)

if __name__ == "__main__":
    write_files()
