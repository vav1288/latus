
import os
import unittest
import merge_cli

# todo : refactor merge_cli so I don't need this class
class my_args():
    root = os.path.join("test", "simple")
    source = os.path.join(root, "src")
    dest = os.path.join(root, "dest_temp")
    mode = "move"

class test_merge_cli(unittest.TestCase):

    def test_basic(self):
        lm_cli = merge_cli.merge_cli()
        lm_cli.args = my_args()
        lm_cli.verbose = True
        lm_cli.metadata_path = "test"
        lm_cli.run()
