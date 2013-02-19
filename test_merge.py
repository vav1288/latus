
import os
import unittest
import test_latus
import merge
import hash

class test_merge(unittest.TestCase):
    def setUp(self):
        test_latus.write_files()
        self.a_file = "a.txt"
        self.src_root = os.path.join(test_latus.get_simple_root(), test_latus.SRC)
        self.out_file_path = os.path.join(test_latus.get_simple_root(), "domerge.bat")
        self.create_merge_object()
        self.m.clean() # start with a fresh database
        # Load up the database with file info.  Generally this is run in run(), but since we're
        # doing one file at at file for some of these tests we need to do this separately.
        self.m.scan(test_latus.get_simple_root())

    def tearDown(self):
        del self.m

    # note that this is dest then src, since usually we change the dest so it has to be first
    def create_merge_object(self, dest_root = None, src_root = None):
        if src_root is None:
            src_root = self.src_root
        self.m = merge.merge(src_root, self.out_file_path, dest_root, True, test_latus.get_root(), get_log_file_path = test_latus.get_log_file_path)

    # a single file
    def test_single_file_does_not_exist(self):
        self.create_merge_object(os.path.join(test_latus.get_simple_root(), test_latus.DEST_EMPTY))
        search_result, search_paths = self.m.merge_file(self.a_file)
        assert(search_result == merge.DOES_NOT_EXIST)

    def test_single_file_exists_exact(self):
        self.create_merge_object(os.path.join(test_latus.get_simple_root(), test_latus.DEST_EXISTS_EXACT))
        search_result, search_paths = self.m.merge_file(self.a_file)
        assert(search_result == merge.EXISTS_EXACT)

    def test_single_file_exists_different(self):
        self.create_merge_object(os.path.join(test_latus.get_simple_root(), test_latus.DEST_EXISTS_DIFFERENT))
        search_result, search_paths = self.m.merge_file(self.a_file)
        assert(search_result == merge.EXISTS_CONFLICT)

    def test_single_file_exists(self):
        self.create_merge_object(os.path.join(test_latus.get_simple_root(), test_latus.DEST_EXISTS_UNDER_DIFFERENT_NAME))
        search_result, search_paths = self.m.merge_file(self.a_file)
        assert(search_result == merge.EXISTS_ELSEWHERE)

    def test_unicode_filename(self):
        self.create_merge_object(None, test_latus.get_unicode_root())
        self.m.scan(test_latus.get_unicode_root())

    def test_analyze(self):
        self.create_merge_object(src_root = test_latus.get_root())
        self.m.analyze()
        h = hash.hash()
        for file_path in test_latus.get_unicode_file_paths(test_latus.get_unicode_root()):
            # todo : I don't like to have to do the abspath to get this to work ... figure out how to remove it
            abs_path = os.path.abspath(file_path)[2:]
            hash_val, cache_flag = h.get_hash(abs_path)
            print abs_path, hash_val, cache_flag
            assert(hash_val is not None)

    def test_run(self):
        self.create_merge_object(os.path.join(test_latus.get_simple_root(), "dest_empty"), test_latus.get_simple_root())
        self.m.run()
        # todo: what do I test for?

