
import os
import threading
import time
import logging

import latus.gui_preferences
import latus.util
import latus.logger
from test_latus.tstutil import get_data_root, logger_init

if latus.util.is_mac():
    import pyautogui

g_coord = None
g_window_closed = False


def get_gui_preferences_root():
    return os.path.join(get_data_root(), "test_gui_preferences")


def automation():
    global g_coord, g_window_closed

    attempt_count = 0
    time.sleep(1)  # time for window to paint
    while not g_window_closed:
        image_path = os.path.join('test_latus', 'ok_cancel_image.png')
        latus.logger.log.info('try %d : %s : start locateOnScreen' % (attempt_count, image_path))
        g_coord = pyautogui.locateOnScreen(image_path, grayscale=True)
        latus.logger.log.info('try %d : %s : end locateOnScreen - returned %s' % (attempt_count, image_path, str(g_coord)))
        attempt_count += 1
        if g_coord is None:
            time.sleep(1)  # just in case the search is very fast (but it usually is on the order of 1 sec)
        else:
            approx_center_of_button = (g_coord[0] + g_coord[2]/2, g_coord[1] + g_coord[3]/20)
            pyautogui.moveTo(approx_center_of_button, duration=1)
            time.sleep(0.5)
            pyautogui.click(approx_center_of_button)
            time.sleep(0.5)


def test_gui_preferences(session_setup, module_setup):
    global g_coord, g_window_closed

    log_folder = os.path.join(get_gui_preferences_root(), 'log')
    logger_init(log_folder)
    latus.logger.set_console_log_level(logging.INFO)

    if latus.util.is_mac():
        # todo: get this to work on Windows (I use virtualization - that might be a problem)

        # Timing of this is tricky.  We have to launch the automation thread that looks for the image of the OK button
        # *then* launch the preferences GUI, since the preferences GUI will block once it starts running.  But since
        # the preferences GUI won't be on the screen when the automation thread starts, the automation thread may
        # have to search multiple times (and pause momentarily between searches to give the GUI time to come up
        # if it hasn't already).
        automation_thread = threading.Thread(target=automation)
        automation_thread.start()
        g_window_closed = False
        latus.gui_preferences.main()  # must be in main thread
        g_window_closed = True
        automation_thread.join()


#if __name__ == '__main__':
#    test_gui_preferences(None, None)