import os
import sys
import win32api
import platform
import collections

import win32con
import pywintypes

from . import logger

# @lru_cache()
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
    long_prefix = "\\\\?\\"
    prefix_len = len(long_prefix)
    starts_with = in_path[:4].startswith(long_prefix)
    if is_windows() and ((len(in_path) < prefix_len) or not starts_with):
        abs_path = long_prefix + os.path.abspath(in_path)
    else:
        abs_path = os.path.abspath(in_path)
    return abs_path

# if this path has a drive specifier (as found in Windows), remove it
def remove_drive_spec(p):
    if p[0].isalpha() and p[1] == ":":
        p = os.path.splitdrive(p)[1]
    return p

def get_abs_path_wo_drive(p):
    p = os.path.abspath(p)
    p = remove_drive_spec(p)
    return p

def del_files(file_list):
    for f in file_list:
        if os.path.exists(f):
            os.remove(f)

def get_file_attributes(in_path):
    attrib = 0
    attributes = []
    if is_windows():
        long_abs_path = get_long_abs_path(in_path)
        try:
            attrib = win32api.GetFileAttributes(long_abs_path)
        except pywintypes.error:
            #logger.get_log().error()
            logger.get_log().error(long_abs_path)
        if attrib & win32con.FILE_ATTRIBUTE_HIDDEN:
            attributes.append(win32con.FILE_ATTRIBUTE_HIDDEN)
        if attrib & win32con.FILE_ATTRIBUTE_SYSTEM:
            attributes.append(win32con.FILE_ATTRIBUTE_SYSTEM)
    # todo : Linux version of this
    return attributes

def make_hidden(in_path):
    win32api.SetFileAttributes(in_path, win32con.FILE_ATTRIBUTE_HIDDEN)

# supplying metadata location is handy for testing
Metadata = collections.namedtuple('metadata', ['root', 'name'])

# call this for all strings we read in
# (this was used for Python 2.x and actually did a decode ... may not need to do that anymore)
def decode_text(in_text):
    # todo: check that this is UTF-8 and if not convert
    return in_text

def check_text_encoding(do_exit = False, give_help = True):
    # required for printing unicode to console
    # http://daveagp.wordpress.com/2010/10/26/what-a-character/
    desired_encoding = "UTF-8"
    ok = (sys.stdin.encoding == desired_encoding)
    if not ok:
        if give_help:
            print ("current text encoding:", sys.stdin.encoding)
            print ("desired text encoding:", desired_encoding)
            print ("This can be fixed by setting the PYTHONIOENCODING environment variable.")
            print ("Please do this (e.g. Windows environment variable setup or console):")
            print ("set PYTHONIOENCODING=utf_8")
        if do_exit:
            exit("proper text encoding not set up ... exiting")
    return ok

