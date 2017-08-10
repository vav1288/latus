
import latus

from enum import IntEnum

LOG_FILE = latus.__application_name__ + '.log'
LATUS_KEY_FILE_EXT = '.lky'
DB_EXTENSION = '.db'
ENCRYPTION_EXTENSION = '.fer'
UNENCRYPTED_EXTENSION = '.une'
DESCRIPTION = 'Secure file sync with low impact to cloud storage.'
MAIN_FILE = 'main.py'

MAKE_DIRS_MODE = 0o775

# todo: make this https once I get the SSL Error fixed
API_ABEL_CO = 'http://api.abel.co'
USAGE_API_URL = API_ABEL_CO + '/latus/usage'

BIG_FILE_SIZE = 1024 * 1024
MAX_HASH_PERF_VALUES = 10  # determine how many longest hash times to store in the db
ASYMMETRIC_KEY_LENGTH = 1024  # Asymmetric key size (in bits)

TIME_OUT = 10  # seconds

# todo: this should probably be longer in a 'production' release
FILTER_TIME_OUT = 2.0  # seconds

FOLDER_PREFERENCE_DEFAULTS = (True, False, False)  # encrypt, shared, cloud


class LatusFileSystemEvent(IntEnum):
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
    mivui = 1
    originator = 2
    event_type = 3  # FileSystemEvent
    detection = 4  # DetectionSource
    file_path = 5
    src_path = 6  # for moves file_path is the dest
    size = 7
    file_hash = 8
    mtime = 9
    pending = 10  # this node has not yet acted on it
    timestamp = 11
