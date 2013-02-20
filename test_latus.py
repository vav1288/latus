
# latus-wide testing routines

import os
import const

SRC = u"src"
DEST_EMPTY = u"dest_empty"
DEST_EXISTS_EXACT = u"dest_exists_exact"
DEST_EXISTS_DIFFERENT = u"dest_exists_different"
DEST_EXISTS_UNDER_DIFFERENT_NAME = u"dest_exists_under_different_name"

def get_root():
    return u"test"

def get_unicode_root():
    return os.path.join(get_root(), u"unicode")

def get_simple_root():
    return os.path.join(get_root(), u"simple")

# use this instead of logger.py's get_log_file_path() so the log file is put in the proper place for testing
def get_log_file_path():
    return os.path.join(get_root(), const.LOG_FILE)

# note that this makes the required dirs if necessary
def write_to_file(p, contents):
    #print "p", p
    make_dirs(os.path.split(p)[0])
    f = open(p, "w")
    f.write(contents)
    f.close()

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
    length = 64
    max_code =  4096 - space # fairly arbitrary max - perhaps this should be a different value?
    for start in range(space, max_code, length):
        # start and end with something always valid
        file_name = u'A' + make_unicode_string(start, length) + u'.txt'
        paths.append(os.path.join(root_dir, file_name))
    return paths

def write_unicode_files(root_dir, test_string):
    paths = get_unicode_file_paths(root_dir)
    for file_path in paths:
        write_to_file(file_path, test_string)

# This writes various input files.  The goal is to not have to package up test files in the repo, if we
# can avoid it.  Also, this way we can readily re-initialize and fully clean up test files.
def write_files():
    test_string = "a"
    different_test_string = "b"
    a_file_name = u"a.txt"
    write_to_file(os.path.join(get_simple_root(), SRC, a_file_name), test_string)
    make_dirs(os.path.join(get_simple_root(), DEST_EMPTY))
    write_to_file(os.path.join(get_simple_root(), DEST_EXISTS_EXACT, a_file_name), test_string)
    write_to_file(os.path.join(get_simple_root(), DEST_EXISTS_DIFFERENT, a_file_name), different_test_string)
    write_to_file(os.path.join(get_simple_root(), DEST_EXISTS_UNDER_DIFFERENT_NAME, u"a_but_different_name.txt"), test_string)
    write_unicode_files(get_unicode_root(), test_string)

if __name__ == "__main__":
    write_files()
