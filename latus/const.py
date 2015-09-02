
# not sure if this is terribly pythonic, but it's pretty clean ...
NAME = 'latus'
LOG_FILE = NAME + '.log'
LATUS_KEY_FILE_NAME = 'latus.lky'
DB_EXTENSION = '.db'
URL = 'www.lat.us'
EMAIL = 'j@abel.co'
AUTHOR = 'James Abel'
DESCRIPTION = 'Secure file sync with low impact to cloud storage.'
MAIN_FILE = 'latus_main.py'

BIG_FILE_SIZE = 1024 * 1024
MAX_HASH_PERF_VALUES = 10  # determine how many longest hash times to store in the db
ASYMMETRIC_KEY_LENGTH = 1024  # Asymmetric key size (in bits)
TIME_OUT = 60  # seconds

