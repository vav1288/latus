
import os
import threading
import time

import latus.gui_preferences
import latus.util

if latus.util.is_mac():
    import pyautogui

g_coord = None


def automation():
    global g_coord
    timeout_count = 0
    while g_coord is None and timeout_count < 60:
        print('try %s : start locateCenterOnScreen' % timeout_count)
        g_coord = pyautogui.locateCenterOnScreen(os.path.join('test_latus', 'ok_image.png'))
        print('try %s : end locateCenterOnScreen' % timeout_count)
        timeout_count += 1
        if g_coord is None:
            time.sleep(1)
    assert(g_coord is not None)
    pyautogui.moveTo(g_coord, duration=1)
    pyautogui.click(g_coord)


def test_gui_preferences():
    global g_coord
    if latus.util.is_mac():
        # todo: get this to work on Windows (I use virtualization - that might be a problem)

        # Timing of this is tricky.  We have to launch the automation thread that looks for the image of the OK button
        # *then* launch the preferences GUI, since the preferences GUI will block once it starts running.  But since
        # the preferences GUI won't be on the screen when the automation thread starts, the automation thread may
        # have to search multiple times (and pause momentarily between searches to give the GUI time to come up
        # if it hasn't already).
        t = threading.Thread(target=automation)
        t.start()
        latus.gui_preferences.main()  # must be in main thread
        t.join()
        assert(g_coord is not None)


def main():
    test_gui_preferences()

if __name__ == '__main__':
    main()