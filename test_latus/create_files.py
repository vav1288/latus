
"""
create the test files
"""

import os
import shutil
import random
import time

import test_latus.util
import test_latus.paths

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

def clean():
    """
    clean up the test data
    :return:
    """
    path = test_latus.paths.get_data_root()
    try_count = 10
    while os.path.exists(path) and try_count:
        try:
            shutil.rmtree(path)
        except PermissionError as e:
            # log isn't set up yet, so just print
            print('can not rmtree %s - retrying' % path)
            print(str(e))
            time.sleep(1)
            try_count -= 1
    assert(try_count > 0)
    if try_count == 0:
        exit('clean failed')


def write_to_file(p, contents):
    test_latus.util.make_dirs(os.path.dirname(p))
    with open(p, "w") as f:
        f.write(contents)
        f.close()

