
import os
import unittest
import test_latus
import merge
import merge_cli

class test_merge_cli(unittest.TestCase):
    def setUp(self):
        self.lm_cli = merge_cli.merge_cli()
        self.lm_cli.verbose = True
        root = os.path.join(test_latus.get_root(), "simple")
        self.lm_cli.metadata_path = root
        self.lm_cli.source = os.path.join(root, "src")
        self.lm_cli.dest = os.path.join(root, "dest_temp")
        self.lm_cli.out_file_path = os.path.join(root,"domerge.bat")

    def tearDown(self):
        del self.lm_cli

    def test_move(self):
        self.lm_cli.mode = merge.str_to_mode("move")
        self.lm_cli.run()
        data = open(self.lm_cli.out_file_path).read()
        found_it = False
        if "move" in data:
            found_it = True
        assert(found_it)

    def test_copy(self):
        self.lm_cli.mode = merge.str_to_mode("copy")
        self.lm_cli.run()
        data = open(self.lm_cli.out_file_path).read()
        found_it = False
        if "copy" in data:
            found_it = True
        assert(found_it)