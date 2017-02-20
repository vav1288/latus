import hashlib
import time

from latus import logger


def calc_sha512(path, latus_key, time_it=False):
    if time_it:
        start_time = time.time()
    else:
        start_time = None

    this_hash = hashlib.sha512()

    if latus_key:
        # For encrypted files, hashes in the DB are initialized with the latus key so an attacker can't
        # ascertain the file contents by doing a dictionary lookup on the hash value.
        if isinstance(latus_key, str):
            latus_key = latus_key.encode()
        this_hash.update(latus_key)

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

    return sha512_val, elapsed_time

