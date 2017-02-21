
import os
import threading
import time

import pyautogui

import latus.gui_preferences
import latus.util

coord = None


def automation():
    time.sleep(2)
    coord = pyautogui.locateCenterOnScreen(os.path.join('test_latus', 'ok_image.png'))
    assert(coord is not None)
    pyautogui.moveTo(coord, duration=1)
    pyautogui.click(coord)
    time.sleep(1)


def test_gui_preferences():
    if latus.util.is_mac():
        # todo: get this to work on Windows (I use virtualization - that might be a problem)
        t = threading.Thread(target=automation)
        t.start()
        latus.gui_preferences.main()
        t.join()
        time.sleep(1)
        assert(coord is not None)  # for PyCharm to flag test as failed the assert needs to be in the main thread
