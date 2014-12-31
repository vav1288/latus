import os
import platform

import win32con
import pywintypes

import latus.logger
import latus.const

WINDOWS_SEP = "\\"
LINUX_SEP = '/'


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


if is_windows():
    import win32api


def get_folder_sep():
    if is_windows():
        sep = WINDOWS_SEP
    else:
        sep = LINUX_SEP
    return sep[-1]


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
            latus.logger.log.error(long_abs_path)
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
            latus.logger.log.error(long_abs_path)
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


def get_latus_appdata_folder():
    """
    Things like config files are stored here.
    :return: the latus appdata folder
    """
    return os.path.join(get_os_appdata_folder(), latus.const.NAME)


def get_latus_log_folder():
    # use appdata local (log files can get big, so they shouldn't be in roaming)
    return os.path.join(get_os_appdata_local_folder(), latus.const.NAME, 'log')


def get_os_appdata_folder():
    # I'd like to use winpaths.get_local_appdata() but it doesn't seem to work with Python 3, so I'll
    # rely on the environment variable.
    return os.environ['APPDATA']


def get_os_appdata_local_folder():
    return os.environ['LOCALAPPDATA']


def make_dirs(path):
    """
    Make a directory as specified by path.  If it already exists, simply return (don't raise an error).

    :param path: path of directories/folders to create
    """
    if not os.path.exists(path):
        os.makedirs(path)


def get_latus_guid():
    """
    This is a GUID we can include in files to ensure it comes from this program.  For example, when we generate
    a key or a database we can put this GUID in there to prevent aliasing and collisions.  Note that this doesn't
    prohibit maliciousness - it only prevents accidental 'good faith' collisions.
    :return: the latus GUID as a string
    """
    guid = '3E7A7DB0-3B15-416E-93D6-0FCF52BAEA38'
    return guid