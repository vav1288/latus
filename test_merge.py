
import os
import unittest
import test_latus
import merge

class test_merge(unittest.TestCase):
    def setUp(self):
        test_latus.write_files()
        self.test_root = os.path.join(test_latus.TEST_ROOT, test_latus.SIMPLE)
        self.a_file = "a.txt"
        self.src_root = os.path.join(self.test_root, test_latus.SRC)
        self.out_file_path = os.path.join(self.test_root, "domerge.bat")
        m = merge.merge(self.src_root, self.out_file_path, verbose=True, metadata_root_override=self.test_root, get_log_file_path = test_latus.get_log_file_path)
        m.clean() # start with a fresh database
        # Load up the database with file info.  Generally this is run in run(), but since we're
        # doing one file at at file for some of these tests we need to do this separately.
        m.scan(self.test_root)

    def tearDown(self):
        del self.m

    # a single file
    def test_single_file_does_not_exist(self):
        dest_root = os.path.join(self.test_root, test_latus.DEST_EMPTY)
        self.m = merge.merge(self.src_root, self.out_file_path, dest_root, True, self.test_root, get_log_file_path = test_latus.get_log_file_path)
        search_result, search_paths = self.m.merge_file(self.a_file)
        assert(search_result == merge.DOES_NOT_EXIST)

    def test_single_file_exists_exact(self):
        dest_root = os.path.join(self.test_root, test_latus.DEST_EXISTS_EXACT)
        self.m = merge.merge(self.src_root, self.out_file_path, dest_root, True, self.test_root, get_log_file_path = test_latus.get_log_file_path)
        search_result, search_paths = self.m.merge_file(self.a_file)
        assert(search_result == merge.EXISTS_EXACT)

    def test_single_file_exists_different(self):
        dest_root = os.path.join(self.test_root, test_latus.DEST_EXISTS_DIFFERENT)
        self.m = merge.merge(self.src_root, self.out_file_path, dest_root, True, self.test_root, get_log_file_path = test_latus.get_log_file_path)
        search_result, search_paths = self.m.merge_file(self.a_file)
        assert(search_result == merge.EXISTS_CONFLICT)

    def test_single_file_exists(self):
        dest_root = os.path.join(self.test_root, test_latus.DEST_EXISTS_UNDER_DIFFERENT_NAME)
        self.m = merge.merge(self.src_root, self.out_file_path, dest_root, True, self.test_root, get_log_file_path = test_latus.get_log_file_path)
        search_result, search_paths = self.m.merge_file(self.a_file)
        assert(search_result == merge.EXISTS_ELSEWHERE)

    def test_run(self):
        self.m = merge.merge(self.src_root, self.out_file_path, os.path.join(self.test_root, "dest_empty"), True, self.test_root, get_log_file_path = test_latus.get_log_file_path)
        self.m.run()
        # todo: what do I test for?

if __name__ == "__main__":
    unittest.main()