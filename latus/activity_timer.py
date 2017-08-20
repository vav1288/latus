
import time
import threading
import logging

import latus.logger
import latus.const


class ActivityTimer:

    def __init__(self, timer_name='ActivityTimer'):
        """
        Monitors how long a function runs when it's called.  Can also be used as a 'activity' monitor
        to see if the program is doing anything.
        """
        self.timeout_seconds = latus.const.ACTIVITY_PERIOD
        self.timer_name = timer_name
        self.timer = None

        self.timer_state = False  # timer based
        self.active_count = 0  # call based

    def is_active(self):
        """
        True if timer is set (active), False otherwise
        :return: timer state
        """
        return self.timer_state or (self.active_count > 0)

    # every call to enter_trigger() must be followed by a call to exit_trigger()
    def enter_trigger(self, trigger_name=''):
        self.active_count += 1
        latus.logger.log.info('%s : active : enter : %d : %s' % (self.timer_name, self.active_count, trigger_name))
        return self._trigger()

    def exit_trigger(self, trigger_name=''):
        self.active_count -= 1
        latus.logger.log.info('%s : active : exit : %d : %s' % (self.timer_name, self.active_count, trigger_name))
        return self._trigger()

    def _trigger(self):
        """
        trigger (or retrigger) the timer
        :return: timer state
        """
        self.timer_state = True
        if self.timer:
            self.timer.cancel()
        # timers can only be started once
        self.timer = threading.Timer(self.timeout_seconds, self.reset)
        latus.logger.log.info('setting timer %s for %f seconds' % (self.timer_name, self.timeout_seconds))
        self.timer.start()
        return self.timer_state

    def reset(self):
        # 'reset' is essentially 'inactive'
        latus.logger.log.info('%s : reset : %d' % (self.timer_name, self.active_count))
        if self.timer:
            self.timer.cancel()
        self.timer_state = False


if __name__ == '__main__':
    # test
    latus.logger.init('temp')
    latus.logger.set_console_log_level(logging.INFO)

    def interval(start):
        return int(time.time() - start + 0.5)
    start_time = time.time()
    my_timeout = 3
    my_timer = ActivityTimer(my_timeout, 'my_timer_name')
    actions = [my_timer.is_active, my_timer.enter_trigger, my_timer.exit_trigger, my_timer.enter_trigger,
               my_timer.exit_trigger, my_timer.is_active, my_timer.is_active, my_timer.is_active, my_timer.is_active,
               my_timer.enter_trigger, my_timer.is_active, my_timer.is_active,  my_timer.is_active,
               my_timer.exit_trigger,  my_timer.is_active, my_timer.is_active, my_timer.is_active, my_timer.is_active]
    for action in actions:
        if action.__name__ == 'is_active':
            print(action.__name__, interval(start_time), action())
        else:
            print(action.__name__, interval(start_time), action('my_trigger_name'))
        time.sleep(1)
