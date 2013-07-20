
import os
import msvcrt
import time
from latus import settings, const, hash, util, metadata_location

class sync():
    def __init__(self, settings_override_folder = None, verbose = False):
        self.settings = settings.Settings(settings_override_folder)
        self.verbose = verbose
        self.settings_section = 'latus'

    def help(self, c = None):
        s = "hit 'q' to quit"
        if c:
            s += " (you hit '%s')" % c
        print(s)

    def get_cloud_folder(self):
        return self.settings.get(self.settings_section, 'cloud')

    def get_local_folder(self):
        return self.settings.get(self.settings_section, 'local')

    def get_uuid(self):
        return self.settings.get(self.settings_section, 'uuid')

    def get_metadata(self):
        return util.Metadata(self.get_cloud_folder(), self.get_uuid())

    # user exit control
    def continue_running(self, do_help = False):
        continue_running_flag = True
        if msvcrt.kbhit():
            c = msvcrt.getwch()
            if c == 'q':
                continue_running_flag = False
            else:
                if do_help:
                    self.help(c)
        return continue_running_flag

    def run(self):
        self.help()
        if (self.verbose):
            print('settings file : %s' % self.settings.get_settings_file_path())
            print('cloud folder : %s' % self.get_cloud_folder())
            print('metadata file : %s' % metadata_location.get_metadata_db_path(self.get_metadata()))
            print('local folder : %s' % self.get_local_folder())
        while (self.continue_running(True)):
            self.scan()
            time.sleep(3)

    def scan(self):
        cloud_folder = self.get_cloud_folder()
        local_folder = self.get_local_folder()
        metadata = self.get_metadata()

