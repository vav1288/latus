
import os
import configparser
import uuid
from . import const, logger

class Settings:
    def __init__(self, settings_folder_override = None):
        self.log = logger.get_log()
        if settings_folder_override:
            settings_folder_path = settings_folder_override
        else:
            # Use the 'local' app data location since the settings could be different across
            # machines.  e.g. the latus folder could be on a sufficiently large internal drive on one machine and
            # an external drive on a machine where the internal drive doesn't have sufficient space.
            settings_folder_path = os.path.join(os.environ['LOCALAPPDATA'], const.NAME)
        if not os.path.exists(settings_folder_path):
            self.log.info("creating %s" % settings_folder_path)
            os.makedirs(settings_folder_path)
        self.settings_file_path = os.path.join(settings_folder_path, const.SETTINGS_FILE_NAME)
        self.log.info("settings file '%s'" % self.settings_file_path)

    # if settings do not yet exist, may want to take the user through soem sort of setup
    def exists(self):
        return os.path.exists(self.settings_file_path)

    def get_settings_file_path(self):
        return self.settings_file_path

    # some simple section and key checking
    def check(self, section, key):
        sects_and_keys = {'sync' : ['cloud', 'local'], 'node' : ['uuid']}
        if section not in sects_and_keys:
            raise Exception("bad section: %s" % section)
        if key not in sects_and_keys[section]:
            raise Exception("bad key: %s" % key)

    def read(self):
        config_exists = False
        self.config = configparser.ConfigParser() # start anew each time in case the file changed
        if self.exists():
            self.config.read(self.settings_file_path)
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
        return val

    def set(self, section, key, value):
        self.check(section, key)
        exists = self.read() # need to get current state since we write out entire file after setting one entry
        if not exists:
            self.log.info("creating settings file %s" % self.settings_file_path)
            # http://stackoverflow.com/questions/703035/when-are-you-truly-forced-to-use-uuid-as-part-of-the-design
            node_uuid = uuid.uuid1()
            self.config.add_section('node')
            self.config.set('node', 'uuid', node_uuid.hex)
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, value)
        with open(self.settings_file_path,'w') as f:
            self.config.write(f)


