
import unittest
from .. import finddup, folder, util
from . import test_latus


class test_finddup(unittest.TestCase):
    def setUp(self):
        root = test_latus.get_root()
        # Load up metadata from the root (this way we have many duplicate files, so we can make sure
        # we only get the subset in simple we're looking for).
        md = util.Metadata(root, self.__module__)
        f = folder.folder(root=root, metadata_root=md)
        f.scan()
        self.dup = finddup.finddup(path=root, metadata_root_override=md, verbose=True)

    def tearDown(self):
        del self.dup

    def test_a_finddup(self):
        # check we found the right number of files
        hashes = self.dup.run()
        # todo : figure out how to not have these constants of 2 and - 1
        self.assertEqual(len(hashes), 2) # 2 different file contents
        # Check for the file that appears the most often. For this input case this works OK since
        # we have one file contents that the vast majority of the files have, and one other that only appears
        # a small number of times.
        n_found = max(hashes.values())
        t = test_latus.test_latus()
        n_files_written = t.write_files(force=True, write_flag=False)
        self.assertEqual(n_found, n_files_written - 1) # -1 since we have one other contents (different_test_string)

if __name__ == "__main__":
    unittest.main()

