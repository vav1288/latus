import hashlib
import os
import time

import win32con

from . import sqlite
from . import util
from . import metadata_location
from . import logger

# todo: check the disk space where the cache resides and make sure we don't consume too much space
#
# todo: improve the speed by by keeping a dict of open db connections (will only be 2, generally)
#       e.g. dbs = {}
#            dbs[metadata_db_fn] = amerge_sqlite.amerge_sqlite(metadata_db_fn)

class hash():
    """ Return the hash value of a file.

    Also maintains a hash cache to avoid unnecessary recalculations/
    """

    def __init__(self, metadata_root = None, verbose = False, include_attrib = []):
        self.HASH_TABLE_NAME = "hash"
        self.ABS_PATH_STRING = "abspath"
        self.MTIME_STRING = "mtime"
        self.SIZE_STRING = "size"
        self.SHA512_VAL_STRING = "sha512_val"
        self.SHA512_TIME_STRING = "sha512_time"
        self.COUNT_STRING = "count"
        self.metadata_root = metadata_root # should only be None if we're not using metadata
        self.verbose = verbose
        self.include_attrib = include_attrib
        self.log = logger.get_log()

    # todo: clean up these 'return's
    def get_hash(self, path):
        abs_path = util.get_long_abs_path(path) # to get around 260 char limit
        if not os.path.exists(abs_path):
            self.log.error("path does not exist," + abs_path)
            return None, None
        # don't allow the calculation or caching of metadata hashes
        if metadata_location.is_metadata_root(os.path.split(path)[0], self.metadata_root):
            self.log.error("tried to get hash of metadata," + path)
            return None, None

        if self.metadata_root is not None:
            self.init_db(metadata_location.get_metadata_db_path(path, self.metadata_root))
            try:
                mtime = os.path.getmtime(abs_path)
                size = os.path.getsize(abs_path)
            except UnicodeDecodeError: # , details:
                # self.log.error(str(details) + "," + abs_path)
                self.log.error(abs_path)
                return None, None
            # use the absolute path, but w/o the drive specification in the hash table
            canon_abs_path_no_drive = util.encode_text(util.get_abs_path_wo_drive(path))
            #print util.printable_text(canon_abs_path_no_drive)
            if self.is_in_table(canon_abs_path_no_drive):
                sha512_hash = self.get_hash_from_db(canon_abs_path_no_drive, mtime, size)
                if sha512_hash is None:
                    # file has changed - update the hash (since file mtime or size has changed, hash is no longer valid)
                    sha512_hash, sha512_calc_time = self.calc_sha512(abs_path)
                    self.db.update({self.MTIME_STRING : os.path.getmtime(abs_path),
                                    self.SIZE_STRING : os.path.getsize(abs_path),
                                    self.SHA512_VAL_STRING : sha512_hash,
                                    self.COUNT_STRING : self.COUNT_STRING + " + 1"},
                                   {self.ABS_PATH_STRING : canon_abs_path_no_drive})
                    got_from_cache = False
                else:
                    got_from_cache = True
            else:
                sha512_hash, sha512_calc_time = self.calc_sha512(abs_path)
                self.db.insert((canon_abs_path_no_drive, mtime, size, sha512_hash, sha512_calc_time, 0))
                got_from_cache = False
            self.db.close()
        else:
            sha512_hash, sha512_calc_time = self.calc_sha512(abs_path)
            got_from_cache = False
        ret = (sha512_hash, got_from_cache)
        return ret

    def get_paths_from_hash(self, hash, root = None):
        self.init_db(metadata_location.get_metadata_db_path(None, self.metadata_root))
        path_desc = {}
        operators = {}
        path_desc[self.SHA512_VAL_STRING] = hash
        operators[self.SHA512_VAL_STRING] = "="
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
        metadata_db_fn = metadata_location.get_metadata_db_path(None, self.metadata_root)
        #print metadata_db_fn
        db = sqlite.sqlite(metadata_db_fn)
        db.clean()
        db.close()

    def init_db(self, db_path):
        db_dir = os.path.split(db_path)[0]
        if not os.path.exists(db_dir):
            os.mkdir(db_dir)
            util.make_hidden(db_dir)

        #print db_path
        self.db = sqlite.sqlite(db_path)
        self.db.connect_to_table(self.HASH_TABLE_NAME)
        if not self.db.exists():
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
            self.db.create_index(self.ABS_PATH_STRING)
            self.db.create_index(self.SHA512_VAL_STRING)
        else:
            self.db.set_cols([self.ABS_PATH_STRING, self.MTIME_STRING, self.SIZE_STRING, self.SHA512_VAL_STRING,
                              self.SHA512_TIME_STRING, self.COUNT_STRING])

    def update_digest(self, file_path, hash):
        attributes = util.get_file_attributes(file_path)
        if not attributes or attributes <= self.include_attrib:
            if self.verbose:
                print((util.encode_text(file_path)))
            # it's a lot faster taking a buffer at a time vs 1 byte at a time (2 orders of magnitude faster)
            bucket_size = 4096 # just a guess ...
            try:
                f = open(file_path, "rb")
                val = f.read(bucket_size)
                while len(val):
                    hash.update(val)
                    val = f.read(bucket_size)
                f.close()
            except IOError: # , details:
                self.log.warn(file_path)

    def calc_sha512(self, path):
        start_time = time.time()
        hash = hashlib.sha512()

        # execution times on sample 'big file':
        # sha512 : 0.5 sec
        # sha256 : 0.75 sec
        # md5 : 0.35 sec
        # generally SHA512 is 1.4-1.5x MD5 (experiment done on a variety of files and sizes)

        if os.path.isfile(path):
            self.update_digest(path, hash)
        elif os.path.isdir(path):
            # this should provide the same hash as DirHash by Mounir IDRASSI (mounir@idrix.fr) (good for testing)
            # todo : a flag to control if we use system and hidden files or not
            paths = []
            for root, dirs, files in os.walk(path):
                for names in files:
                    paths.append(os.path.join(root,names))
            paths.sort(key=lambda y: y.lower())
            for path in paths:
                self.update_digest(path, hash)
        sha512_val = hash.hexdigest()

        elapsed_time = time.time() - start_time
        #print ("calc_hash," + path + "," + str(elapsed_time))

        return sha512_val, elapsed_time

    # Look up the hash from the table, assuming if a file path, mtime and size are the same it's
    # truely the same file and therefore the same hash.
    def get_hash_from_db(self, path, mtime, size):
        # todo: make this dict creation nicer looking
        file_info = {}
        file_info[self.ABS_PATH_STRING] = path
        file_info[self.MTIME_STRING] = mtime
        file_info[self.SIZE_STRING] = size
        hash = None
        hash_list = self.db.get(file_info, self.SHA512_VAL_STRING)
        if hash_list is not None:
            hash = hash_list[0]
        return hash

    # look to see if this path is in the table at all
    def is_in_table(self, path):
        file_info = {}
        file_info['abspath'] = path
        return self.db.get(file_info, self.SHA512_VAL_STRING) is not None

if __name__ == "__main__":
    import sys
    import argparse

    logger.setup()

    epilog = """
example:
""" + os.path.split(sys.argv[0])[-1] + " -p myfolder"

    parser = argparse.ArgumentParser(epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-p", "--path", default='.', help="path to source directory/folder")
    parser.add_argument("-a", "--all", action="store_true", help="hash all files (default is to ignore hidden and system files")
    parser.add_argument("-v", "--verbose", action="store_true", help="print informational messages")

    args = parser.parse_args()
    if args.all:
        file_attrib = (win32con.FILE_ATTRIBUTE_HIDDEN, win32con.FILE_ATTRIBUTE_SYSTEM)
    else:
        file_attrib = []
    f = hash(verbose=args.verbose, include_attrib=file_attrib)
    hash, cache_flag = f.get_hash(args.path)
    print (hash)

