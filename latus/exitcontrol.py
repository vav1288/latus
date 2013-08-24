
import win32event
import msvcrt
import threading

# This exit control is a little tricky.  It's used like this:
# 1) Code that uses this module must first create events to be triggered up by ExitControl (actually a class derived
#    from ExitControl).  These can be either win32events or regular Python events.  The idea is that when these
#    events are triggered, the code that uses this module will test is_alive() and if it's False, the code will exit.
# 2) An instance of a class derived from ExitControl is created.
# 3) ExitControl.setup() is called with a list of events to be woken up at end end of ExitControl.run()
#    ( run() is used since ExitControl is derived from threading.Thread )
# 4) Code that uses this module can loop until get_exit_control_flag() returns False.
#
# See latus/sync.py for an example.

# Base class for all exit control classes (not usable by itself since it has no run() method)
# (test code can also derive from this to control program exit)
class ExitControl(threading.Thread):

    # this must be called before run()
    def setup(self, win32event_handles = [], events = [], exit_criteria = None):
        # events to awaken when we get a keyboard hit
        self.win32event_handles = win32event_handles # windows style
        self.events = events # python style
        self.exit_criteria = exit_criteria # generic - derived class determines what to do with this
        self.exit_control_flag = False # set once we've triggered all the events that we want to exit

    def get_exit_control_flag(self):
        return self.exit_control_flag

    # Trigger all the events we've been given.
    # This MUST be called this just before the derived class' run() exits.
    def trigger_all_events(self):
        for win32event_handle in self.win32event_handles:
            win32event.PulseEvent(win32event_handle)
        for evt in self.events:
            evt.set()
        self.exit_control_flag = True

# keyboard hit exit control
class KBHit(ExitControl):

    def run(self):
        this_char = ''
        while this_char != self.exit_criteria:
            # print("waiting for", self.exit_criteria)
            msvcrt.kbhit() # waits for the keyboard hit
            this_char = msvcrt.getwch() # eats the character just hit
            if this_char == self.exit_criteria:
                self.trigger_all_events()
            else:
                print("waiting for '%s' : got '%s'" % (str(self.exit_criteria), this_char))
        # returning (falling through) makes this thread no longer 'alive'
