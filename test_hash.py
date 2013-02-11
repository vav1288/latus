
import os
import shutil
import unittest
import logging
import logger
import hash
import test_latus

# todo: make it so the tests run OK w/o relying the order of _a, _b, etc.

class TestHash(unittest.TestCase):
    def setUp(self):
        test_latus.write_files() # make sure this is first, since log files will go here
        self.log = logging.getLogger(__name__)
        self.handlers = logger.setup(self.log, test_latus.get_log_file_path)
        # sha512 of "a"
        self.correct_hash_val = "1f40fc92da241694750979ee6cf582f2d5d7d28e18335de05abc54d0560e0f5302860c652bf08d560252aa5e74210546f369fbbbce8c12cfc7957b2652fe9a75"
        self.root = test_latus.get_test_root()
        self.hash = hash.hash(self.root, test_latus.get_log_file_path)
        self.static_test_file_path = os.path.join(self.root, "simple", "src", "a.txt")
        self.dynamic_test_file_path = os.path.join(self.root, "simple", "dest_exists_under_different_name", "a_but_different_name.txt")

    def tearDown(self):
        logger.remove_handlers(self.log, self.handlers)

    # clean
    def test_a_clean(self):
        self.hash.clean()

    # new table entry
    def test_b_new_table_entry(self):
        hash_val, cache_flag = self.hash.get_hash(self.static_test_file_path)
        #print "b", hash_val, cache_flag
        self.assertTrue(hash_val == self.correct_hash_val)
        self.assertTrue(cache_flag is False)

    # lookup hash in table
    def test_c_lookup_hash(self):
        # get hash twice so 2nd time it's in the cache
        self.hash.get_hash(self.static_test_file_path)
        hash_val, cache_flag = self.hash.get_hash(self.static_test_file_path)
        #print "c", hash_val, cache_flag
        self.assertTrue(hash_val == self.correct_hash_val)
        self.assertTrue(cache_flag is True)

    # lookup file via hash
    def test_d_lookup_file_via_hash(self):
        paths = self.hash.get_paths_from_hash(self.correct_hash_val)
        #print paths[0]
        self.assertTrue(os.path.abspath(paths[0]) == os.path.abspath(self.static_test_file_path))

    # update table
    def test_e_update_table(self):
        if os.path.exists(self.dynamic_test_file_path):
            os.remove(self.dynamic_test_file_path)
        shutil.copy(self.static_test_file_path, self.dynamic_test_file_path)
        hash_val, cache_flag = self.hash.get_hash(self.dynamic_test_file_path)
        self.assertTrue(cache_flag is False)
        #print hash_val, cache_flag
        f = open(self.dynamic_test_file_path, "w")
        f.write("u") # to signify updated
        f.close()
        # this causes the table to be updated
        new_hash_val, new_cache_flag = self.hash.get_hash(self.dynamic_test_file_path)
        #print new_hash_val, new_cache_flag
        self.assertTrue(cache_flag is False)
        self.assertTrue(hash_val != new_hash_val)
