
import msvcrt
from latus import settings, const, hash, util, metadata_location, watcher, kbhit

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

        # This is a little tricky.
        # We set up a file system watcher, which has an event that it will use to wake up on (see the watcher module).
        # This event can be 'triggered' either by a file system change or a keyboard press (via the
        # kbhit module).  If the kbhit thread is still alive (no quit key press yet), then we assume the file system
        # change event (in the watcher module) was what made us exit so we do a scan.

        # we'll do a scan at this interval, even if the watcher module hasn't detected a change in the file system
        watcher_timeout = 60 * 60 * 1000 # mS
        fs_watcher = watcher.Watcher(watcher_timeout)
        watcher_event_handle = fs_watcher.create_change_event()

        kbh = kbhit.KBHit()
        # give kbhit the handle of the event to wake up when the 'quit' key is pressed
        kbh.latus_setup('q', win32event_handles=[watcher_event_handle])
        kbh.start() # kbhit (quit key detect) runs in a separate thread

        while kbh.is_alive():
            if fs_watcher.wait(self.get_local_folder()):
                if kbh.is_alive():
                    self.scan()

    def scan(self):
        if self.verbose:
            print("scanning %s" % self.get_local_folder())
        cloud_folder = self.get_cloud_folder()
        local_folder = self.get_local_folder()
        metadata = self.get_metadata()

