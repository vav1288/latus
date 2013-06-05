
import unittest
import os
from .. import finddup, hash, util
from . import test_latus

class test_finddup(unittest.TestCase):
    def setUp(self):
        root = test_latus.get_root()
        # Load up metadata from the root (this way we have many duplicate files, so we can make sure
        # we only get the subset in simple we're looking for).
        md = util.Metadata(root, self.__module__)
        h = hash.hash(root, metadata_root=md)
        h.scan(root)
        self.dup = finddup.finddup(path=root, metadata_override=md, verbose=True)

    def tearDown(self):
        del self.dup

    def test_a_finddup(self):
        # check we found the right number of files
        dups = self.dup.run()
        print("dups", dups)
        self.assertEqual(len(dups), 2) # there are two files that appear more than once (have contents of 'a' and 'b')
        # Check for the file that appears the most often. For this input case this works OK since
        # we have one file contents that the vast majority of the files have, and one other that only appears
        # a small number of times.
        n_found = 0
        for d in dups:
            n_found = max(n_found, len(dups[d])) # is there a more Pythonic way to do this?
        t = test_latus.test_latus()
        n_files_written = t.write_files(force=True, write_flag=False)
        # todo : figure out how to not have this constants of -5 (count the 'a' and 'b' files)
        self.assertEqual(n_found, n_files_written - 5) # -5 since we have 5 other files that have 'b' in them

    # test that we can do a finddup on another drive (a drive that is not where our cwd is on)
    # NOTES: IF THIS TEST FAILS, YOU MAKE HAVE TO MANUALLY DELETE c:\.latus\*.db SINCE THIS TEST PROGRAM
    # DOES NOT INITIALIZE IT.
    def test_b_non_exec_drive(self):
        d = test_latus.write_non_execution_test_dir_files()
        print ("d", d)
        h = hash.hash(d, None)
        h.scan(d)
        finder = finddup.finddup(path=d, metadata_override=None, verbose=True)
        dups_list = finder.run()
        self.assertEqual(len(dups_list), 1) # we only have the 2 files, and they are identical
        dups = dups_list[0]
        print ("dups", dups)
        # check that we have the correct number of dups and they are the right files
        self.assertEqual(len(dups), len(test_latus.NON_EXECUTION_DRIVE_TEST_FILES))
        for file in dups:
            self.assertIn(os.path.split(file)[1], test_latus.NON_EXECUTION_DRIVE_TEST_FILES)

if __name__ == "__main__":
    unittest.main()

