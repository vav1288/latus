
import win32event
import msvcrt
import threading

class KBHit(threading.Thread):

    # this must be called before run()
    def setup(self, exit_char = 'q', win32event_handles = [], events = []):
        # events to awaken when we get a keyboard hit
        self.win32event_handles = win32event_handles # windows style
        self.events = events # python style
        self.exit_char = exit_char

    def run(self):
        this_char = ''
        while this_char != self.exit_char:
            msvcrt.kbhit() # waits for the keyboard hit
            this_char = msvcrt.getwch() # eats the character just hit
            if this_char == self.exit_char:
            # wake up all the events we've been given
                for win32event_handle in self.win32event_handles:
                    win32event.PulseEvent(win32event_handle)
                for evt in self.events:
                    evt.set()
            else:
                print("waiting for '%s' : got '%s'" % (self.exit_char, this_char))
        # returning (falling through) makes this thread no longer 'alive'
