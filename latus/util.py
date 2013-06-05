import os
import sys
import win32api
import platform
import collections

import win32con
import pywintypes

from . import logger

WINDOWS_SEP = "\\"
LINUX_SEP = '/'

def get_folder_sep():
    if is_windows():
        sep = WINDOWS_SEP
    else:
        sep = LINUX_SEP
    return sep[-1]

# @lru_cache()
def is_windows():
    is_win = False
    plat = platform.system()
    plat = plat.lower()
    if plat[0] == 'w':
        is_win = True
    return is_win

def is_a_file_path(p):
    return not is_a_dir_path(p)

def is_a_dir_path(p):
    # todo: why doesn't this work????  Both Windows and Linux separators should only be used as separators
    #if (p[-1] == WINDOWS_SEP) or (p[-1] != LINUX_SEP):

    if (p[-1] == get_folder_sep()):
        is_a_dir = True
    else:
        is_a_dir = False
    return is_a_dir

def remove_dirs_from_list(paths):
    new_paths = []
    for p in paths:
        if is_a_file_path(p):
            new_paths.append(p)
    return new_paths

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
    if os.path.isdir(abs_path):
        abs_path += get_folder_sep()
    return abs_path

# if this path has a drive specifier (as found in Windows), remove it
def remove_drive_spec(p):
    if p[0].isalpha() and p[1] == ":":
        p = os.path.splitdrive(p)[1]
    return p

def get_abs_path_wo_drive(p):
    p = os.path.abspath(p)
    is_dir = os.path.isdir(p)
    p = remove_drive_spec(p)
    if is_dir:
        p += get_folder_sep()
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

# Unfortunately, cx-freeze does not utilize PYTHONIOENCODING environment variable, so
# this is useless until I either use a different .exe generator or they fix this issue.
# In the mean time, use lprint.lprint() .
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
            print ("set PYTHONIOENCODING=UTF-8")
        if do_exit:
            exit("proper text encoding not set up ... exiting")
    return ok

def decode_text(s):
    return s