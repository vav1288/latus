
# not sure if this is terribly pythonic, but it's pretty clean ...
NAME = "latus"
TEST_DIR = "tstfiles" # must not match nose's regex for test files/directories, since nose errors out on the unicode files
LOG_FILE = NAME + ".log"
METADATA_DIR_NAME = "." + NAME
LFS_DB_NAME = "lfs" # local file system
DB_EXT = ".db"
OUTPUT_FILE = "domerge.bat"