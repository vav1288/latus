import os
import sys
import win32api
import platform
import socket

import win32con
import pywintypes

import core.logger

WINDOWS_SEP = "\\"
LINUX_SEP = '/'

def get_folder_sep():
    if is_windows():
        sep = WINDOWS_SEP
    else:
        sep = LINUX_SEP
    return sep[-1]

def is_windows():
    is_win = False
    plat = platform.system()
    plat = plat.lower()
    if plat[0] == 'w':
        is_win = True
    return is_win

def is_linux():
    is_lin = False
    plat = platform.system()
    plat = plat.lower()
    if plat[0] == 'l':
        is_lin = True
    return is_lin

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

def is_hidden(in_path):
    is_hidden_flag = False
    attrib = 0
    if is_windows():
        long_abs_path = get_long_abs_path(in_path)
        try:
            attrib = win32api.GetFileAttributes(long_abs_path)
        except pywintypes.error:
            core.logger.log.error(long_abs_path)
        is_hidden_flag = (attrib & win32con.FILE_ATTRIBUTE_HIDDEN > 0)
    return is_hidden_flag

def is_system(in_path):
    is_system_flag = False
    attrib = 0
    if is_windows():
        long_abs_path = get_long_abs_path(in_path)
        try:
            attrib = win32api.GetFileAttributes(long_abs_path)
        except pywintypes.error:
            core.logger.log.error(long_abs_path)
        is_system_flag = (attrib & win32con.FILE_ATTRIBUTE_SYSTEM > 0)
    return is_system_flag

def is_locked(in_path):
    try:
        open(in_path, 'r')
        locked = False
    except(IOError):
        locked = True
    return locked


def make_hidden(in_path):
    win32api.SetFileAttributes(in_path, win32con.FILE_ATTRIBUTE_HIDDEN)

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

def get_plaform_info():
    prefix = 'platform_'
    platform_info = {}
    platform_info[prefix + 'node'] = platform.node()
    platform_info[prefix + 'machine'] = platform.machine()
    platform_info[prefix + 'processor'] = platform.processor()
    platform_info[prefix + 'python_version'] = platform.python_version()
    platform_info[prefix + 'release'] = platform.release()
    platform_info[prefix + 'system'] = platform.system()
    platform_info['local_host'] = socket.gethostname()
    platform_info['local_ip'] = socket.gethostbyname(socket.gethostname())
    return platform_info