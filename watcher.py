
import sys
import msvcrt
from latus import watcher

if __name__  == "__main__":
    path = sys.argv[1]
    w = watcher.Watcher()
    continue_flag = True
    while continue_flag:
        if msvcrt.kbhit():
            continue_flag = False
        change = w.wait(path)
        if change:
            print("change in %s" % path)
            continue_flag = False