
import os
import unittest
import win32event
import time
import collections
from .. import sync, logger, settings, exitcontrol, const
from . import test_latus

class TestSync(unittest.TestCase):
    def setUp(self):
        self.log = logger.get_log()
        self.sync_node_info = test_latus.get_sync_node_info()
        self.NodeConfig = collections.namedtuple('NodeConfig', ['settings_folder', 'local_folder', 'cloud_folder'])

    def tearDown(self):
        pass

    def make_sync_node(self, root):

        # write to the settings file
        sync_node_config = self.NodeConfig(os.path.join(root, 'appdata', const.METADATA_DIR_NAME),
                                           os.path.join(root, const.NAME),
                                           os.path.join(root, 'cloud')
                                          )
        user_settings = settings.Settings(sync_node_config.settings_folder)
        user_settings.set(settings.NODE_SECTION, 'cloud', sync_node_config.cloud_folder)
        user_settings.set(settings.NODE_SECTION, 'local', sync_node_config.local_folder)

        # create the sync node
        sync_node = sync.sync(sync_node_config.settings_folder, verbose=True)

        return sync_node, TstExitControl()

    def test_single(self):
        root, id = self.sync_node_info[0]
        node, exit_control = self.make_sync_node(root)
        node.run(exit_control)

    def test_two(self):
        nodes = []
        for root, id in self.sync_node_info:
            nodes.append(self.make_sync_node(root))
        for node, exit_control in nodes:
            node.run(exit_control)
        # test that the files synced across the nodes
        p = os.path.join(self.sync_node_info[0][0], "b.txt")
        self.assertTrue(os.path.exists(p), p)
        p = os.path.join(self.sync_node_info[1][0], "a.txt")
        self.assertTrue(os.path.exists(p), p)

class TstExitControl(exitcontrol.ExitControl):

    def run(self):
        time.sleep(5) # todo: test the sync here ... exit this routine once things are OK or we timeout
        self.trigger_all_events()
        # returning (falling through) makes this thread no longer 'alive'

if __name__ == "__main__":
    unittest.main()
