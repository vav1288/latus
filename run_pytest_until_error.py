
import os
import sys
import signal
import logging

import pytest

import latus.logger

os.environ["PYTHONPATH"] = '.'

g_keep_running = True


def control_key_handler(signal, frame):
    global g_keep_running
    print('%s : ctrl-c detected - exiting' % __file__)
    g_keep_running = False


def run_pytest_until_error():
    global g_keep_running

    g_keep_running = True

    latus.logger.init(os.path.join('temp', __file__), 'log')
    latus.logger.set_console_log_level(logging.INFO)

    print('hit ctrl-c to exit')
    signal.signal(signal.SIGINT, control_key_handler)
    signal.signal(signal.SIGTSTP, control_key_handler)

    count = {'fail': 0, 'pass': 0}
    # target = os.path.join('test_latus', 'test_z_gui_preferences.py::test_gui_preferences')
    while g_keep_running:
        if len(sys.argv) > 1:
            r = pytest.main([sys.argv[1]])  # command line '-s' to see output
        else:
            r = pytest.main()
        if r != 0:
            count['fail'] += 1
            print('pytest got an error - exiting')
            g_keep_running = False
        else:
            count['pass'] += 1
        print('test iteration : %s : return=%s' % (str(count), str(r)))


def main():
    run_pytest_until_error()

if __name__ == '__main__':
    main()
