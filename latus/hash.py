
import os
import time
from collections import namedtuple

from . import sqlite, util, metadata_location, logger, walker, hash_calc, lprint

# todo: check the disk space where the cache resides and make sure we don't consume too much space
#
# todo: improve the speed by by keeping a dict of open db connections (will only be 2, generally)
#       e.g. dbs = {}
#            dbs[metadata_db_fn] = amerge_sqlite.amerge_sqlite(metadata_db_fn)

class hash():
    """ Return the hash value of a file.

    Also maintains a hash cache to avoid unnecessary recalculations/
    """

    def __init__(self, root, metadata_root, verbose = False, include_attrib = set(), hoh = True):
        self.HASH_TABLE_NAME = "hash"
        self.HASH_BASE_TABLE_NAME = "base" # might rename this ...
        self.ABS_PATH_STRING = "abspath"
        self.MTIME_STRING = "mtime"
        self.SIZE_STRING = "size"
        self.SHA512_VAL_STRING = "sha512_val"
        self.SHA512_TIME_STRING = "sha512_time"
        self.COUNT_STRING = "count"
        self.metadata_root = metadata_root # should only be None if we're not using metadata
        self.verbose = verbose
        self.include_attrib = include_attrib
        self.hoh = hoh
        self.HashTuple = namedtuple("hash", ['sha512', 'got_from_cache', 'entry_count'])
        self.log = logger.get_log()

        # While we shouldn't _necessarily_ need to know the root yet, since
        # using the database is integral to the operation of most of this module we require it upfront.
        # In other words, some functions will need it for functionality, and others for speed (only open and
        # close the db once per use of this module).
        self.root = root
        self.db_path = metadata_location.get_metadata_db_path(self.metadata_root, root)
        self.init_db(self.db_path)

    def __del__(self):
        self.db.close()

    def calc_or_lookup_hash(self, path):
        abs_path = util.get_long_abs_path(path) # to get around 260 char limit
        entry_count = None
        try:
            mtime = os.path.getmtime(abs_path)
            size = os.path.getsize(abs_path)
        except UnicodeDecodeError:
            self.log.error(abs_path)
            return None, None, None
        # use the absolute path, but w/o the drive specification in the hash table
        canon_abs_path_no_drive = util.get_abs_path_wo_drive(path)
        if self.is_in_table(canon_abs_path_no_drive):
            sha512_hash, entry_count = self.get_hash_from_db(canon_abs_path_no_drive, mtime, size)
            if sha512_hash is None:
                # file has changed - update the hash (since file mtime or size has changed, hash is no longer valid)
                sha512_hash, size, sha512_calc_time = hash_calc.calc_sha512(abs_path, self.include_attrib, self.hoh)
                mtime = os.path.getmtime(abs_path)
                self.db.update(self.HASH_TABLE_NAME,
                               [self.MTIME_STRING, self.SIZE_STRING, self.SHA512_VAL_STRING], [mtime, size, sha512_hash],
                               {self.ABS_PATH_STRING : canon_abs_path_no_drive}, count_flag=True)
                # read back in the count string
                unused, entry_count = self.get_hash_from_db(canon_abs_path_no_drive, mtime, size)
                got_from_cache = False
            else:
                got_from_cache = True
        else:
            # new entry
            sha512_hash, size, sha512_calc_time = hash_calc.calc_sha512(abs_path, self.include_attrib, self.hoh)
            self.db.insert(self.HASH_TABLE_NAME, [canon_abs_path_no_drive, mtime, size, sha512_hash, sha512_calc_time, 0])
            got_from_cache = False
        return sha512_hash, got_from_cache, entry_count

    # todo: clean up these 'return's
    def get_hash(self, path):
        #print ("get_hash.db_path", db_path)
        abs_path = util.get_long_abs_path(path) # to get around 260 char limit
        if not os.path.exists(abs_path):
            self.log.error("path does not exist," + abs_path)
            return self.HashTuple(None, None, None)
        # don't allow the calculation or caching of metadata hashes
        if self.metadata_root is not None:
            if metadata_location.is_metadata_root(path, self.metadata_root):
                self.log.error("tried to get hash of metadata - path:" + path)
                self.log.error("tried to get hash of metadata - metadata_root:" + self.metadata_root.root)
                return self.HashTuple(None, None, None)

        sha512_hash, got_from_cache, entry_count = self.calc_or_lookup_hash(path)
        return self.HashTuple(sha512_hash, got_from_cache, entry_count)

    # update the metadata
    def scan(self, path):
        scan_walker = walker.walker(path)
        for partial_path in scan_walker:
            start_time = time.time()
            full_path = scan_walker.get_path(partial_path)
            attributes = util.get_file_attributes(full_path)
            if not attributes or attributes <= self.include_attrib:
                self.calc_or_lookup_hash(full_path)
            if self.verbose:
                lprint.lprint(full_path + " , " + str(time.time()-start_time) + " sec")

    def get_paths_from_hash(self, this_hash):
        path_desc = {}
        operators = {}
        path_desc[self.SHA512_VAL_STRING] = this_hash
        operators[self.SHA512_VAL_STRING] = "="
        path_desc[self.ABS_PATH_STRING] = util.get_abs_path_wo_drive(self.root) + "%"
        operators[self.ABS_PATH_STRING] = "LIKE"
        paths = self.db.get(self.HASH_TABLE_NAME, path_desc, self.ABS_PATH_STRING, operators)
        return paths

    # mainly for testing purposes
    def clean(self):
        db = sqlite.sqlite(metadata_location.get_metadata_db_path(self.metadata_root))
        db.clean()
        db.close()

    def init_db(self, db_path):
        db_dir = os.path.split(db_path)[0]
        if not os.path.exists(db_dir):
            os.mkdir(db_dir)
            util.make_hidden(db_dir)

        #print ("init_db.db_path", db_path)
        self.db = sqlite.sqlite(db_path)
        self.db.table = self.HASH_TABLE_NAME
        if not self.db.exists():
            self.db.connect() # will create the db
            self.db.add_col_text(self.ABS_PATH_STRING)
            self.db.add_col_float(self.MTIME_STRING)
            self.db.add_col_integer(self.SIZE_STRING)
            self.db.add_col_text(self.SHA512_VAL_STRING)
            self.db.add_col_float(self.SHA512_TIME_STRING)
            self.db.add_col_integer(self.COUNT_STRING)
            self.db.add_col_timestamp()
            self.db.add_col_auto_index()
            self.db.create_table(self.HASH_TABLE_NAME)
            # use indices to speed access
            self.db.create_index(self.HASH_TABLE_NAME, self.ABS_PATH_STRING)
            self.db.create_index(self.HASH_TABLE_NAME, self.SHA512_VAL_STRING)
        else:
            self.db.connect() # db already exists
            self.db.set_cols([self.ABS_PATH_STRING, self.MTIME_STRING, self.SIZE_STRING, self.SHA512_VAL_STRING,
                              self.SHA512_TIME_STRING, self.COUNT_STRING])

    # Look up the hash from the table, assuming if a file path, mtime and size are the same it's
    # truely the same file and therefore the same hash.
    def get_hash_from_db(self, path, mtime, size):
        # todo: this does a float compare with an =.  Figure out how in sqlite to do a compare so the float
        # just has to be close (e.g. within 1 sec) so we don't get into trouble with float equality compare.
        #
        # todo: make this dict creation nicer looking
        file_info = {}
        operators = {}

        file_info[self.ABS_PATH_STRING] = path
        operators[self.ABS_PATH_STRING] = "="
        file_info[self.SIZE_STRING] = size
        operators[self.SIZE_STRING] = "="
        file_info[self.MTIME_STRING] = mtime
        operators[self.MTIME_STRING] = "BETWEEN"

        # todo: get hash and count both in one call to db.get()
        this_hash = None
        this_count = None
        hash_list = self.db.get(self.HASH_TABLE_NAME, file_info, self.SHA512_VAL_STRING, operators)
        count_list = self.db.get(self.HASH_TABLE_NAME, file_info, self.COUNT_STRING, operators)
        if hash_list is not None:
            this_hash = hash_list[0]
        if count_list is not None:
            this_count = count_list[0]
        return this_hash, this_count

    # look to see if this path is in the table at all
    def is_in_table(self, path):
        file_info = {}
        file_info['abspath'] = path
        return self.db.get(self.HASH_TABLE_NAME, file_info, self.SHA512_VAL_STRING) is not None

