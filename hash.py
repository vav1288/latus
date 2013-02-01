
import hashlib
import os
import logging
import sqlite
import logger

# todo: check the disk space where the cache resides and make sure we don't consume too much space
#
# todo: improve the speed by by keeping a dict of open db connections (will only be 2, generally)
#       e.g. dbs = {}
#            dbs[metadata_db_fn] = amerge_sqlite.amerge_sqlite(metadata_db_fn)

class hash():
    """ Return the hash value of a file.

    Also maintains a hash cache to avoid unnecessary recalculations/
    """

    def __init__(self, metadata_root_override = None):
        self.SUITE_NAME = "latus"
        self.METADATA_DIR_NAME = "." + self.SUITE_NAME
        self.DB_NAME = "lfs" # local file system
        self.HASH_TABLE_NAME = "hash"
        self.ABS_PATH_STRING = "abspath"
        self.MTIME_STRING = "mtime"
        self.SIZE_STRING = "size"
        self.SHA512_STRING = "sha512"
        self.metadata_root_override = metadata_root_override
        self.log = logging.getLogger(__name__)
        self.log_handlers = logger.setup(self.log)

    def __del__(self):
        logger.remove_handlers(self.log, self.log_handlers)

    # this is the main function to call
    # todo: clean up these 'return's
    def get_hash(self, path):
        if not os.path.exists(path):
            return None, None
        # don't allow the calculation or caching of metadata hashes
        if self.is_metadata_root(os.path.split(path)[0]):
            self.log.error("tried to get hash of metadata," + path)
            return None, None

        self.init_db(self.get_metadata_db_fn(path))
        # use the absolute path, but w/o the drive specification in the hash table
        abs_path_no_drive = os.path.splitdrive(os.path.abspath(path))[1]
        #print "abs_path_no_drive", abs_path_no_drive
        # Trick to get around 260 char limit
        # http://msdn.microsoft.com/en-us/library/aa365247.aspx#maxpath
        try:
            abs_path = u"\\\\?\\" + os.path.abspath(path)
            mtime = os.path.getmtime(path)
            size = os.path.getsize(path)
        except UnicodeDecodeError, details:
            self.log.error(str(details) + "," + path)
            return None, None
        if self.is_in_table(abs_path_no_drive):
            hash = self.get_hash_from_db(abs_path_no_drive, mtime, size)
            if hash is None:
                # file has changed - update the hash (since file mtime or size has changed, hash is no longer valid)
                hash = self.calc_hash(abs_path)
                self.db.update({self.MTIME_STRING : os.path.getmtime(abs_path),
                                self.SIZE_STRING : os.path.getsize(abs_path),
                                self.SHA512_STRING : hash },
                               {self.ABS_PATH_STRING : abs_path_no_drive})
                got_from_cache = False
            else:
                got_from_cache = True
        else:
            hash = self.calc_hash(abs_path)
            self.db.insert((abs_path_no_drive, mtime, size, hash))
            got_from_cache = False
        self.db.close()
        ret = (hash, got_from_cache)
        #print "__get_hash_debug__", self.get_metadata_db_fn(), abs_path_no_drive, hash, got_from_cache
        return ret

    def get_paths_from_hash(self, hash, root = None):
        self.init_db(self.get_metadata_db_fn())
        path_desc = {}
        operators = {}
        path_desc[self.SHA512_STRING] = hash
        operators[self.SHA512_STRING] = "="
        if root is not None:
            path_desc[self.ABS_PATH_STRING] = root + "%"#
            operators[self.ABS_PATH_STRING] = "LIKE"
        paths = self.db.get(path_desc, self.ABS_PATH_STRING, operators)
        #print "__get_paths_from_hash_debug__", self.get_metadata_db_fn(), hash, paths
        self.db.close()
        return paths

    # mainly for testing purposes
    # relies on the 'user' of this class to provide their own get_metadata_root()
    def clean(self):
        metadata_db_fn = self.get_metadata_db_fn()
        #print metadata_db_fn
        db = sqlite.sqlite(metadata_db_fn)
        db.clean()
        db.close()

    # use this to avoid copying metadata when doing a merge
    def is_metadata_root(self, path):
        return path == self.get_metadata_dir_path(path)

    def get_metadata_root(self, path):
        if self.metadata_root_override:
            metadata_root = self.metadata_root_override
        else:
            metadata_root = os.path.abspath(path)
            while os.path.split(metadata_root)[1]:
                metadata_root = os.path.split(metadata_root)[0]
        return metadata_root

    def get_metadata_dir_path(self, path):
        return os.path.join(self.get_metadata_root(path), self.METADATA_DIR_NAME)

    def get_metadata_dir_name(self):
        return self.METADATA_DIR_NAME

    # from a target file, determine the metadata sqlite filename
    def get_metadata_db_fn(self, path = None):
        return os.path.join(self.get_metadata_dir_path(path), self.DB_NAME + ".db")

    def init_db(self, db_path):
        db_dir = os.path.split(db_path)[0]
        if not os.path.exists(db_dir):
            os.mkdir(db_dir)

        #print db_path
        self.db = sqlite.sqlite(db_path)
        self.db.connect_to_table(self.HASH_TABLE_NAME)
        if not self.db.exists():
            self.db.add_col_text(self.ABS_PATH_STRING)
            self.db.add_col_float(self.MTIME_STRING)
            self.db.add_col_integer(self.SIZE_STRING)
            self.db.add_col_text(self.SHA512_STRING)
            self.db.add_col_timestamp()
            self.db.add_col_auto_index()
            self.db.create_table(self.HASH_TABLE_NAME)
        else:
            self.db.set_cols([self.ABS_PATH_STRING, self.MTIME_STRING, self.SIZE_STRING, self.SHA512_STRING])

    def calc_hash(self, path):
        #start_time = time.time()

        # execution times on sample 'big file':
        # sha512 : 0.5 sec
        # sha256 : 0.75 sec
        # md5 : 0.35 sec

        if not os.path.isfile(path):
            self.log.error("%s is not a file", path)
            return None
        file_hash = hashlib.sha512()
        # it's a lot faster taking a buffer at a time vs 1 byte at a time (2 orders of magnitude faster)
        bucket_size = 4096 # just a guess ...
        try:
            f = open(path, "rb")
            val = f.read(bucket_size)
            while len(val):
                file_hash.update(val)
                val = f.read(bucket_size)
            sha512_val = file_hash.hexdigest()
            f.close()
        except IOError, details:
            self.log.error(str(details) + "," + path)
            sha512_val = None

        #elapsed_time = time.time() - start_time
        #print ("calc_hash," + path + "," + str(elapsed_time))

        return sha512_val

    # Look up the hash from the table, assuming if a file path, mtime and size are the same it's
    # truely the same file and therefore the same hash.
    def get_hash_from_db(self, path, mtime, size):
        # todo: make this dict creation nicer looking
        file_info = {}
        file_info[self.ABS_PATH_STRING] = path
        file_info[self.MTIME_STRING] = mtime
        file_info[self.SIZE_STRING] = size
        hash = None
        hash_list = self.db.get(file_info, self.SHA512_STRING)
        if hash_list is not None:
            hash = hash_list[0]
        return hash

    # look to see if this path is in the table at all
    def is_in_table(self, path):
        file_info = {}
        file_info['abspath'] = path
        return self.db.get(file_info, "sha512") is not None



