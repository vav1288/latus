
import os
import unittest
import test_latus
import folder
import analyze

class test_analyze(unittest.TestCase):
    def setUp(self):
        self.test_latus = test_latus.test_latus()
        self.test_latus.write_files()
        root = test_latus.get_root()
        # Load up metadata from the root (this way we have many duplicate files, so we can make sure
        # we only get the subset in simple we're looking for).
        f = folder.folder(root, root)
        f.scan()
        self.analyze = analyze.analyze(root, root, True)

    def tearDown(self):
        del self.analyze

    def test_analyze(self):
        # check we found the right number of files
        hashes = self.analyze.run()
        # todo : figure out how to not have these constants of 2 and - 1
        self.assertEqual(len(hashes), 2) # 2 different file contents
        n_found = hashes[hashes.keys()[0]]
        self.assertEqual(n_found, self.test_latus.number_of_files_written() - 1) # -1 since we have one other type of contents

if __name__ == "__main__":
    unittest.main()

