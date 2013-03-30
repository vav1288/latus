
import os
import unittest
import test_latus
import merge
import logging

class test_merge_cli(unittest.TestCase):
    def setUp(self):
        root = os.path.join(test_latus.get_root(), "simple")
        self.lm_cli = merge.merge(os.path.join(root, "src"), os.path.join(root,"domerge.bat"),
                                  os.path.join(root, "dest_temp"), True, root)

    def tearDown(self):
        del self.lm_cli

    def test_copy(self):
        self.lm_cli.mode = merge.str_to_mode("copy")
        self.lm_cli.run()
        self.lm_cli.close()
        data = open(self.lm_cli.out_file_path).read()
        found_it = False
        if "copy" in data:
            found_it = True
        assert(found_it)

    def test_move(self):
        self.lm_cli.mode = merge.str_to_mode("move")
        self.lm_cli.run()
        self.lm_cli.close()
        data = open(self.lm_cli.out_file_path).read()
        found_it = False
        if "move" in data:
            found_it = True
        assert(found_it)

