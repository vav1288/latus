
import os
import threading
import time

import pyautogui

import latus.gui_preferences


def automation():
    time.sleep(2)
    coord = pyautogui.locateCenterOnScreen(os.path.join('test_latus', 'ok_image.png'))
    assert(coord is not None)
    pyautogui.moveTo(coord, duration=1)
    pyautogui.click(coord)
    time.sleep(1)


def test_gui_preferences():
    t = threading.Thread(target=automation)
    t.start()
    latus.gui_preferences.main()
    t.join()
    time.sleep(1)
