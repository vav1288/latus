
# latus-wide testing routines

import os

SIMPLE = "simple"
SRC = "src"
DEST_EMPTY = "dest_empty"
DEST_EXISTS_EXACT = "dest_exists_exact"
DEST_EXISTS_DIFFERENT = "dest_exists_different"
DEST_EXISTS_UNDER_DIFFERENT_NAME = "dest_exists_under_different_name"

TEST_ROOT = "test"

def get_test_root():
    return TEST_ROOT

# use this instead of logger.py's get_log_file_path() so the log file is put in the proper place for testing
def get_log_file_path():
    return os.path.join(TEST_ROOT, __name__  + ".log")

# note that this makes the required dirs if necessary
def write_to_file(p, contents):
    make_dirs(os.path.split(p)[0])
    f = open(p, "w")
    f.write(contents)
    f.close()

def make_dirs(p):
    if not os.path.exists(p):
        os.makedirs(p)

# This writes various input files.  The goal is to not have to package up test files in the repo, if we
# can avoid it.  Also, this way we can readily re-initialize and fully clean up test files.
def write_files():
    test_string = "a"
    different_test_string = "b"
    simple_path = os.path.join(get_test_root(), SIMPLE)
    write_to_file(os.path.join(simple_path, SRC, "a.txt"), test_string)
    make_dirs(os.path.join(simple_path, DEST_EMPTY))
    write_to_file(os.path.join(simple_path, DEST_EXISTS_EXACT, "a.txt"), test_string)
    write_to_file(os.path.join(simple_path, DEST_EXISTS_DIFFERENT, "a.txt"), different_test_string)
    write_to_file(os.path.join(simple_path, DEST_EXISTS_UNDER_DIFFERENT_NAME, "a_but_different_name.txt"), test_string)
