
import hashlib
import os
import unittest
import binascii

from .. import hash, util
from . import test_latus

class TestHash(unittest.TestCase):

    def setUp(self):
        # From execution of DirHash (see dirhash_result.txt)
        self.hash_from_dirhash = \
            "2D408A0717EC188158278A796C689044361DC6FDDE28D6F04973B80896E1823975CDBF12EB63F9E0591328EE235D80E9B5BF1AA6A44F4617FF3CAF6400EB172D"
        self.hoh_from_dirhash = \
            "A40FB6247BF9AA223348EB8C99DCEA9D198694B805AE85BCBFD5FFD33F8EF42C07DD4946FFA68654FD19026EE2723D7ECB2868C3134CE960981156B2120EF62C"
        a = bytearray.fromhex('61') # 'a'
        b = bytearray.fromhex('62') # 'b'

        # concatenated
        self.hash_of_a_b = self.hash_it(a+b)

        # hash-of-hash
        ha = self.hash_it(a)
        hb = self.hash_it(b)
        self.hoh_of_a_b = self.hash_it(ha+hb)
        self.write_as_binary_to_file("a_hash_binary.tmp", ha)
        self.write_as_binary_to_file("b_hash_binary.tmp", hb)

    # tests the math behind the hoh calculations (but not testing the latus code itself)
    def test_hoh(self):
        self.assertEqual(self.hash_of_a_b, bytearray.fromhex(self.hash_from_dirhash))
        print("regular_hash",  binascii.hexlify(self.hash_of_a_b))

        # getting a hash of the hashes of the two files
        self.assertEqual(self.hoh_of_a_b, bytearray.fromhex(self.hoh_from_dirhash))
        print("hash-of-hash",  binascii.hexlify(self.hoh_of_a_b))

    # tests latus level implementation of hoh
    def test_latus_hoh(self):
        p = test_latus.get_hash_root()
        md = util.Metadata(test_latus.get_root(), self.__module__) # keep the metadata out of the folder with the test files
        cat_hash = hash.hash(p, metadata=md, hoh=False)
        hoh_hash = hash.hash(p, metadata=md)

        hash_val = cat_hash.get_hash(p)
        print(hash_val)
        self.assertEqual(hash_val.sha512.lower(), self.hash_from_dirhash.lower())

        hoh_val = hoh_hash.get_hash(p) # hoh is the default
        print(hoh_val)
        self.assertEqual(hoh_val.sha512.lower(), self.hoh_from_dirhash.lower())

    def hash_it(self, val):
        h = hashlib.sha512()
        h.update(val)
        return h.digest()

    def write_as_binary_to_file(self, file_name, data):
        dir = os.path.join("temp", "hash_test")
        if not os.path.exists(dir):
            os.mkdir(dir)
        file_path = os.path.join(dir, file_name)
        with open(file_path, "wb") as f:
            f.write(data)
        print(file_path, binascii.hexlify(data))