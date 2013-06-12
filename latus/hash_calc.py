
import hashlib
import time
import os
from . import util, logger

def calc_sha512(path, include_attrib, hoh, time_it = True):
    if time_it:
        start_time = time.time()
    size = 0
    this_hash = hashlib.sha512()

    # execution times on sample 'big file':
    # sha512 : 0.5 sec
    # sha256 : 0.75 sec
    # md5 : 0.35 sec
    # generally SHA512 is 1.4-1.5x MD5 (experiment done on a variety of files and sizes)

    if os.path.isfile(path):
        update_digest(path, this_hash, include_attrib)
        size = os.path.getsize(path)
    elif os.path.isdir(path):
        # This should provide the same hash as DirHash by Mounir IDRASSI (mounir@idrix.fr) (good for testing)
        # HOWEVER, it seems that DirHash and this program don't agree if there is a compressed file (e.g. .zip or .gz)
        # in the folder anywhere.  Not sure why this is ...
        paths = []
        for root, dirs, files in os.walk(path):
            for names in files:
                paths.append(os.path.join(root,names))
        for path in sorted(paths, key=str.lower):
            if hoh:
                # hash of hashes (so we can lookup the file hashes in the database)
                file_hash, file_size, file_time = calc_sha512(path, include_attrib, True, False) # always a file
                this_hash.update(bytearray.fromhex(file_hash)) # use binary (bytes), not string
                size += file_size
            else:
                # regular (AKA non-hoh)
                update_digest(path, this_hash, include_attrib)
                size += os.path.getsize(path)
    sha512_val = this_hash.hexdigest()

    if time_it:
        elapsed_time = time.time() - start_time
    else:
        elapsed_time = None
    #print ("calc_hash," + path + "," + str(elapsed_time))

    return sha512_val, size, elapsed_time

def update_digest(file_path, this_hash, include_attrib):
    if util.get_file_attributes(file_path) <= include_attrib:
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

