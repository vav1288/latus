
import os
import unittest
import test_latus
import analyze
import hash

class test_analyze(unittest.TestCase):
    def setUp(self):
        test_latus.write_files()
        self.a_file = "a.txt"
        self.root = os.path.join(test_latus.get_root(), test_latus.SRC)
        self.a = analyze.analyze(self.root, test_latus.get_root(), True)

    def tearDown(self):
        del self.a

    def test_analyze(self):
        self.a.run()
        h = hash.hash(test_latus.get_root())
        for file_path in test_latus.get_unicode_file_paths(test_latus.get_unicode_root()):
            hash_val, cache_flag = h.get_hash(file_path)
            self.assertNotEqual(hash_val, None)

if __name__ == "__main__":
    unittest.main()

