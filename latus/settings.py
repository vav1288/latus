
import os
import const
import configparser
import time

class Settings:
    def __init__(self, app_data_folder = None):
        if app_data_folder is None:
            # Use the 'local' app data location since the settings could be different across
            # machines.  e.g. the latus folder could be on a sufficiently large internal drive on one machine and
            # an external drive on a machine where the internal drive doesn't have sufficient space.
            app_data_folder = os.environ['LOCALAPPDATA']
        self.file_path = os.path.join(app_data_folder, const.SETTINGS_FILE_NAME)
        self.sect_name = 'user'
        self.config = configparser.ConfigParser()

    def read_settings(self):
        settings = {}
        if os.path.exists(self.file_path):
            self.config.read(self.file_path)
            for section in self.config.sections():
                for option in self.config.options(section):
                    val = self.config.get(section, option)
                    settings[option] = val
        else:
            if not self.config.has_section(self.sect_name):
                self.config.add_section(self.sect_name)
        return settings

    def write_settings(self):
        f = open(self.file_path,'w')
        self.config.write(f)
        f.close()

    def set(self, key, value):
        self.read_settings()
        self.config.set(self.sect_name, key, value)
        self.write_settings()

my_settings = Settings()
print(my_settings.file_path)
print(my_settings.read_settings())
my_settings.set('csfpath', 'dropbox')
my_settings.set('lsfpath', 'latus')
print(my_settings.read_settings())
