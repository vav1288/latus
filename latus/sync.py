
import msvcrt
from latus import settings

class sync():
    def __init__(self, settings_override_folder = None, verbose = False):
        self.settings = settings.Settings(settings_override_folder)
        self.verbose = verbose

    def run(self):
        if (self.verbose):
            print('settings file : %s' % self.settings.get_settings_file_path())
        self.help()
        continue_running = True
        while (continue_running):

            # user exit control
            if msvcrt.kbhit():
                c = msvcrt.getwch()
                if c == 'q':
                    continue_running = False
                else:
                    self.help(c)

    def help(self, c = None):
        s = "hit 'q' to quit"
        if c:
            s += " (you hit '%s')" % c
        print(s)