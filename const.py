
# not sure if this is terribly pythonic, but it's pretty clean ...
NAME = u"latus"
TEST_DIR = u"tstfiles" # must not match nose's regex for test files/directories, since nose errors out on the unicode files
LOG_FILE = NAME + u".log"
METADATA_DIR_NAME = u"." + NAME
LFS_DB_NAME = u"lfs" # local file system
DB_EXT = u".db"
OUTPUT_FILE = u"domerge.bat"