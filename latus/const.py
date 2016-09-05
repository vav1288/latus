
from enum import IntEnum

# not sure if this is terribly pythonic, but it's pretty clean ...
COMPANY = 'abel'
NAME = 'latus'
LOG_FILE = NAME + '.log'
LATUS_KEY_FILE_NAME = 'latus.lky'
DB_EXTENSION = '.db'
ENCRYPTION_EXTENSION = '.fer'
UNENCRYPTED_EXTENSION = '.une'
URL = 'www.lat.us'
EMAIL = 'j@abel.co'
AUTHOR = 'James Abel'
DESCRIPTION = 'Secure file sync with low impact to cloud storage.'
MAIN_FILE = 'main.py'

BIG_FILE_SIZE = 1024 * 1024
MAX_HASH_PERF_VALUES = 10  # determine how many longest hash times to store in the db
ASYMMETRIC_KEY_LENGTH = 1024  # Asymmetric key size (in bits)

# todo: make this longer once I fix some bugs that this influences
TIME_OUT = 3  # seconds

FILTER_TIME_OUT = 60  # seconds


class FileSystemEvent(IntEnum):
    unknown = 0
    created = 1
    modified = 2
    deleted = 3
    moved = 4
    any = 5


# this level of detail aides in debug
class DetectionSource(IntEnum):
    unknown = 0
    initial_scan = 1
    watchdog = 2
    periodic_poll = 3


# DB columns
class ChangeAttributes(IntEnum):
    index = 0
    seq = 1
    originator = 2
    event = 3       # ChangeEvents
    detection = 4   # DetectionSource
    path = 5
    size = 6
    hash = 7
    mtime = 8
    timestamp = 9
