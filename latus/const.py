
from enum import IntEnum

# not sure if this is terribly pythonic, but it's pretty clean ...
COMPANY = 'abel'
NAME = 'latus'
LOG_FILE = NAME + '.log'
LATUS_KEY_FILE_EXT = '.lky'
DB_EXTENSION = '.db'
ENCRYPTION_EXTENSION = '.fer'
UNENCRYPTED_EXTENSION = '.une'
URL = 'www.lat.us'
EMAIL = 'j@abel.co'
AUTHOR = 'James Abel'
DESCRIPTION = 'Secure file sync with low impact to cloud storage.'
MAIN_FILE = 'main.py'

API_ABEL_CO = 'https://api.abel.co'
USAGE_API_URL = API_ABEL_CO + '/usage'

BIG_FILE_SIZE = 1024 * 1024
MAX_HASH_PERF_VALUES = 10  # determine how many longest hash times to store in the db
ASYMMETRIC_KEY_LENGTH = 1024  # Asymmetric key size (in bits)

TIME_OUT = 10  # seconds

FILTER_TIME_OUT = 5  # seconds


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
    event = 3       # FileSystemEvent
    detection = 4   # DetectionSource
    path = 5
    srcpath = 6
    size = 7
    hash = 8
    mtime = 9
    pending = 10  # this node has not yet acted on it
    timestamp = 11
