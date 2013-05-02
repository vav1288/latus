
import hashlib
import time
import os
from . import util, logger

def calc_sha512(path, include_attrib):
    start_time = time.time()
    this_hash = hashlib.sha512()

    # execution times on sample 'big file':
    # sha512 : 0.5 sec
    # sha256 : 0.75 sec
    # md5 : 0.35 sec
    # generally SHA512 is 1.4-1.5x MD5 (experiment done on a variety of files and sizes)

    if os.path.isfile(path):
        update_digest(path, this_hash, include_attrib)
    elif os.path.isdir(path):
        # this should provide the same hash as DirHash by Mounir IDRASSI (mounir@idrix.fr) (good for testing)
        # todo : a flag to control if we use system and hidden files or not
        paths = []
        for root, dirs, files in os.walk(path):
            for names in files:
                paths.append(os.path.join(root,names))
        paths.sort(key=lambda y: y.lower())
        for path in paths:
            update_digest(path, this_hash, include_attrib)
    sha512_val = this_hash.hexdigest()

    elapsed_time = time.time() - start_time
    #print ("calc_hash," + path + "," + str(elapsed_time))

    return sha512_val, elapsed_time

def update_digest(file_path, this_hash, include_attrib):
    attributes = util.get_file_attributes(file_path)
    if not attributes or attributes <= include_attrib:
        # it's a lot faster taking a buffer at a time vs 1 byte at a time (2 orders of magnitude faster)
        bucket_size = 4096 # just a guess ...
        try:
            f = open(file_path, "rb")
            val = f.read(bucket_size)
            while len(val):
                this_hash.update(val)
                val = f.read(bucket_size)
            f.close()
        except IOError: # , details:
            logger.get_log().warn(file_path)