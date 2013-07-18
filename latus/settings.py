
import os
import configparser
from . import const, logger

class Settings:
    def __init__(self, app_data_folder = None):
        if app_data_folder is None:
            # Use the 'local' app data location since the settings could be different across
            # machines.  e.g. the latus folder could be on a sufficiently large internal drive on one machine and
            # an external drive on a machine where the internal drive doesn't have sufficient space.
            app_data_folder = os.environ['LOCALAPPDATA']
        self.file_path = os.path.join(app_data_folder, const.SETTINGS_FILE_NAME)
        self.log = logger.get_log()

    # if does not exists, may want to take the user through setup
    def exists(self):
        return os.path.exists(self.file_path)

    # some simple section and key checking
    def check(self, section, key):
        sects_and_keys = {'folder' : ['cloud', 'local']}
        if section not in sects_and_keys:
            raise Exception("bad section: %s" % section)
        if key not in sects_and_keys[section]:
            raise Exception("bad key: %s" % key)

    def read(self):
        config_exists = False
        self.config = configparser.ConfigParser() # start anew each time in case the file changed
        if self.exists():
            self.config.read(self.file_path)
            config_exists = True
        return config_exists

    # read in all entries (good for dumping all settings)
    def get_all(self):
        self.read()
        settings = {}
        for section_name, section_proxy in self.config.items():
            settings[section_name] = self.config.items(section_name)
        return settings

    # get one section/key entry
    def get(self, section, key):
        val = None
        self.read()
        if self.config.has_section(section):
            if self.config.has_option(section, key):
                val = self.config.get(section, key)
        if val is None:
            self.log.warn("can not get : section=%s key=%s" % (section, key))
        return val

    def set(self, section, key, value):
        self.check(section, key)
        exists = self.read() # need to get current state since we write out entire file after setting one entry
        if not exists:
            self.log.info("creating settings file %s" % self.file_path)
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, value)
        with open(self.file_path,'w') as f:
            self.config.write(f)


