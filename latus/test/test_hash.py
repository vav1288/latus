
import os
import shutil
import unittest

# todo: make it so the tests run OK w/o relying the order of _a, _b, etc.
from .. import hash, folder, logger, util
from . import test_latus


class TestHash(unittest.TestCase):
    def setUp(self):
        self.log = logger.get_log()
        # sha512 of "a"
        self.correct_hash_val = "1f40fc92da241694750979ee6cf582f2d5d7d28e18335de05abc54d0560e0f5302860c652bf08d560252aa5e74210546f369fbbbce8c12cfc7957b2652fe9a75"
        self.root = test_latus.get_simple_root() # should this be get_root()?  make sure some test covers unicode...
        # load up metadata
        md = util.Metadata(self.root, self.__module__)
        self.target = folder.folder(root=self.root, metadata_root=md)
        self.hash = hash.hash(metadata_root=md)
        self.static_test_file_path = os.path.join(test_latus.get_simple_root(), test_latus.SRC, "a.txt")
        self.dynamic_test_file_path = os.path.join(test_latus.get_simple_root(), test_latus.DEST_EXISTS_UNDER_DIFFERENT_NAME, "a_but_different_name.txt")

    def tearDown(self):
        # this test perturbs the files - put them back the way they were
        t = test_latus.test_latus()
        t.write_files(force=True) # force is needed to ensure we do the writes

    # clean
    def test_a_clean(self):
        self.hash.clean()

    # new table entry
    def test_b_new_table_entry(self):
        hash_val, cache_flag = self.hash.get_hash(self.static_test_file_path)
        #print "b", hash_val, cache_flag
        self.assertEqual(hash_val, self.correct_hash_val)
        self.assertTrue(cache_flag is False)

    # lookup hash in table
    def test_c_lookup_hash(self):
        self.target.scan() # load metadata
        # get hash twice so 2nd time it's in the cache
        self.hash.get_hash(self.static_test_file_path)
        hash_val, cache_flag = self.hash.get_hash(self.static_test_file_path)
        #print "c", hash_val, cache_flag
        self.assertEqual(hash_val, self.correct_hash_val)
        self.assertTrue(cache_flag is True)

    # lookup file via hash
    def test_d_lookup_file_via_hash(self):
        self.target.scan() # load metadata
        paths = self.hash.get_paths_from_hash(self.correct_hash_val)
        self.assertIsNotNone(paths)
        self.assertIn(util.get_abs_path_wo_drive(self.static_test_file_path), paths)
        #print paths
        #self.assertEqual(os.path.abspath(paths[0]), os.path.abspath(self.static_test_file_path))

    # update table
    def test_e_update_table(self):
        self.target.scan() # load metadata
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
        self.assertNotEqual(hash_val, new_hash_val)

if __name__ == "__main__":
    unittest.main()