
import os
import unittest
import win32event
import time
from .. import sync, logger, settings, exitcontrol
from . import test_latus

class TestSync(unittest.TestCase):
    def setUp(self):
        self.log = logger.get_log()
        self.root = os.path.join(test_latus.get_root(), test_latus.SYNC)
        self.settings_folder = os.path.join(self.root, 'appdata', 'latus')

        settings_section = 'latus'
        user_settings = settings.Settings(self.settings_folder)
        user_settings.set(settings_section, 'cloud', os.path.join(self.root, 'cloud'))
        local_folder = os.path.join(self.root, 'latus')
        os.makedirs(local_folder)
        user_settings.set(settings_section, 'local', local_folder)

    def tearDown(self):
        pass

    def test_sync(self):
        do_sync = sync.sync(self.settings_folder, True)
        exit_control = TstExitControl() # use the exit control written just for testing
        do_sync.run(exit_control)
        # todo: test the actual sync

class TstExitControl(exitcontrol.ExitControl):

    def run(self):
        time.sleep(5) # todo: test the sync here ... exit this routine once things are OK or we timeout
        self.trigger_all_events()
        # returning (falling through) makes this thread no longer 'alive'

if __name__ == "__main__":
    unittest.main()
