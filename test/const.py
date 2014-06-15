
import core.const

QUICK_TEST = True # set to False for full test (takes longer)
HASH_TEST_FILE_PREFIX = 'big'
HASH_TEST_FILE_SUFFIX = '.txt'
HASH_TEST_BASE_FILE_SIZE = 1024 * 1024
HASH_TEST_FILE_MIN = 1
if QUICK_TEST:
    HASH_TEST_FILE_MAX = 3
else:
    # careful with this - files can get big
    HASH_TEST_FILE_MAX = core.const.MAX_HASH_PERF_VALUES + 2

X_FOLDER = 'x'
Y_FOLDER = 'y'