
import os
import unittest
import merge

class test_merge(unittest.TestCase):
    def setUp(self):
        self.test_root = os.path.join("test", "simple")
        self.a_file = "a.txt"
        self.src_root = os.path.join(self.test_root, "src")
        m = merge.merge(self.src_root, None, True, self.test_root)
        m.clean() # start with a fresh database
        # Load up the database with file info.  Generally this is run in run(), but since we're
        # doing one file at at file for some of these tests we need to do this separately.
        m.scan(self.test_root)

    def tearDown(self):
        del self.m

    # a single file
    def test_single_file_does_not_exist(self):
        dest_root = os.path.join(self.test_root, "dest_empty")
        self.m = merge.merge(self.src_root, dest_root, True, self.test_root)
        search_result, search_paths = self.m.merge_file(self.a_file)
        assert(search_result == merge.DOES_NOT_EXIST)

    def test_single_file_exists_exact(self):
        dest_root = os.path.join(self.test_root, "dest_exists_exact")
        self.m = merge.merge(self.src_root, dest_root, True, self.test_root)
        search_result, search_paths = self.m.merge_file(self.a_file)
        assert(search_result == merge.EXISTS_EXACT)

    def test_single_file_exists_different(self):
        dest_root = os.path.join(self.test_root, "dest_exists_different")
        self.m = merge.merge(self.src_root, dest_root, True, self.test_root)
        search_result, search_paths = self.m.merge_file(self.a_file)
        assert(search_result == merge.EXISTS_CONFLICT)

    def test_single_file_exists(self):
        dest_root = os.path.join(self.test_root, "dest_exists_under_different_name")
        self.m = merge.merge(self.src_root, dest_root, True, self.test_root)
        search_result, search_paths = self.m.merge_file(self.a_file)
        assert(search_result == merge.EXISTS_ELSEWHERE)

    def test_run(self):
        self.m = merge.merge(self.src_root, os.path.join(self.test_root, "dest_empty"), True, self.test_root)
        self.m.run()
        # todo: what do I test for?

if __name__ == "__main__":
    unittest.main()