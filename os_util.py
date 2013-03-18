
import os
import platform

def is_windows():
    is_win = False
    plat = platform.system()
    plat = plat.lower()
    if plat[0] == 'w':
        is_win = True
    return is_win

def get_long_abs_path(in_path):
    # Trick to get around 260 char limit
    # http://msdn.microsoft.com/en-us/library/aa365247.aspx#maxpath
    if is_windows():
        abs_path = u"\\\\?\\" + os.path.abspath(in_path)
    else:
        abs_path = os.path.abspath(in_path)
    return abs_path