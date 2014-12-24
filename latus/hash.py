import hashlib
import time
import os

from . import util
from latus import logger

def calc_sha512(path, time_it = False):
    if time_it:
        start_time = time.time()
    else:
        start_time = 0

    this_hash = hashlib.sha512()

    # execution times on sample 'big file':
    # sha512 : 0.5 sec
    # sha256 : 0.75 sec
    # md5 : 0.35 sec
    # generally SHA512 is 1.4-1.5x MD5 (experiment done on a variety of files and sizes)

    # it's a lot faster taking a buffer at a time vs 1 byte at a time (2 orders of magnitude faster)
    bucket_size = 4096 # just a guess ...
    try:
        f = open(path, "rb")
        val = f.read(bucket_size)
        while len(val):
            this_hash.update(val)
            val = f.read(bucket_size)
        f.close()
    except IOError:
        logger.log.warn('hash: could not read "%s"', path)
        return None, None

    sha512_val = this_hash.hexdigest()

    if time_it:
        elapsed_time = time.time() - start_time
    else:
        elapsed_time = None
    # print ("calc_hash," + path + "," + sha512_val + ',' + str(elapsed_time))

    return sha512_val, elapsed_time

