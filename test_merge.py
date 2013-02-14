
import os
import unittest
import test_latus
import merge

class test_merge(unittest.TestCase):
    def setUp(self):
        test_latus.write_files()
        self.simple_root = os.path.join(test_latus.TEST_ROOT, test_latus.SIMPLE)
        self.unicode_root = os.path.join(test_latus.TEST_ROOT, test_latus.TEST_UNICODE)
        self.a_file = "a.txt"
        self.src_root = os.path.join(self.simple_root, test_latus.SRC)
        self.out_file_path = os.path.join(self.simple_root, "domerge.bat")
        self.create_merge_object()
        self.m.clean() # start with a fresh database
        # Load up the database with file info.  Generally this is run in run(), but since we're
        # doing one file at at file for some of these tests we need to do this separately.
        self.m.scan(self.simple_root)

    def tearDown(self):
        del self.m

    # note that this is dest then src, since usually we change the dest so it has to be first
    def create_merge_object(self, dest_root = None, src_root = None):
        if src_root is None:
            src_root = self.src_root
        self.m = merge.merge(src_root, self.out_file_path, dest_root, True, test_latus.TEST_ROOT, get_log_file_path = test_latus.get_log_file_path)

    # a single file
    def test_single_file_does_not_exist(self):
        self.create_merge_object(os.path.join(self.simple_root, test_latus.DEST_EMPTY))
        search_result, search_paths = self.m.merge_file(self.a_file)
        assert(search_result == merge.DOES_NOT_EXIST)

    def test_single_file_exists_exact(self):
        self.create_merge_object(os.path.join(self.simple_root, test_latus.DEST_EXISTS_EXACT))
        search_result, search_paths = self.m.merge_file(self.a_file)
        assert(search_result == merge.EXISTS_EXACT)

    def test_single_file_exists_different(self):
        self.create_merge_object(os.path.join(self.simple_root, test_latus.DEST_EXISTS_DIFFERENT))
        search_result, search_paths = self.m.merge_file(self.a_file)
        assert(search_result == merge.EXISTS_CONFLICT)

    def test_single_file_exists(self):
        self.create_merge_object(os.path.join(self.simple_root, test_latus.DEST_EXISTS_UNDER_DIFFERENT_NAME))
        search_result, search_paths = self.m.merge_file(self.a_file)
        assert(search_result == merge.EXISTS_ELSEWHERE)

    def test_unicode_filename(self):
        self.create_merge_object(None, self.unicode_root)
        self.m.scan(self.unicode_root)

    def test_run(self):
        self.create_merge_object(os.path.join(self.simple_root, "dest_empty"), self.simple_root)
        self.m.run()
        # todo: what do I test for?

if __name__ == "__main__":
    unittest.main()