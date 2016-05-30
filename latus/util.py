import os
import platform
import uuid
import datetime
import appdirs

import latus.logger
import latus.const

#WINDOWS_SEP = "\\"
#LINUX_SEP = '/'


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
    import win32con


#def get_folder_sep():
#    if is_windows():
#        sep = WINDOWS_SEP
#    else:
#        sep = LINUX_SEP
#    return sep[-1]


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
        abs_path += os.sep
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
        p += os.sep
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
        except: ## pywintypes.error:  todo: pywintypes.error seems to be wrong ... find the correct way to do this
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
        except:  ## pywintypes.error:  todo: pywintypes.error seems to be wrong ... find the correct way to do this
            latus.logger.log.error(long_abs_path)
        is_system_flag = (attrib & win32con.FILE_ATTRIBUTE_SYSTEM > 0)
    return is_system_flag


def make_hidden(in_path):
    attribute = win32api.GetFileAttributes(in_path)
    if not (attribute & win32con.FILE_ATTRIBUTE_HIDDEN):
        win32api.SetFileAttributes(in_path, win32con.FILE_ATTRIBUTE_HIDDEN)


#def get_latus_appdata_roaming_folder():
#    return appdirs.user_config_dir(latus.const.NAME, latus.const.COMPANY)


#def get_latus_appdata_local_folder():
#    return appdirs.user_config_dir(latus.const.NAME, latus.const.COMPANY)
#    return os.path.join(__get_os_appdata_local_folder(), latus.const.NAME)


#def get_latus_log_folder():
#    # use appdata local (log files can get big, so they shouldn't be in roaming)
#    return os.path.join(__get_os_appdata_local_folder(), latus.const.NAME, 'log')


#def __get_os_appdata_roaming_folder():
#    # Things stored here: preferences, etc.
#    #
#    # I'd like to use winpaths.get_local_appdata() but it doesn't seem to work with Python 3, so I'll
#    # rely on the environment variable.
#    return os.environ['APPDATA']


#def __get_os_appdata_local_folder():
#    # Things stored here: logs, etc.
#    # Can be larger files.
#    key = 'LOCALAPPDATA'
#    try:
#        local_app_data = os.environ[key]
#    except KeyError:
#        print('No %s' % key)
#        local_app_data = None
#        raise
#    return local_app_data


def make_dirs(path):
    """
    Make a directory as specified by path.  If it already exists, simply return (don't raise an error).

    :param path: path of directories/folders to create
    """
    try:
        os.makedirs(path)
    except FileExistsError:
        pass


def make_dir(path, hidden=False):
    try:
        os.mkdir(path)
    except FileExistsError:
        pass
    if hidden:
        make_hidden(path)


def get_latus_guid():
    """
    This is a GUID we can include in files to ensure it comes from this program.  For example, when we generate
    a key or a database we can put this GUID in there to prevent aliasing and collisions.  Note that this doesn't
    prohibit maliciousness - it only prevents accidental 'good faith' collisions.
    :return: the latus GUID as a string
    """
    guid = '3E7A7DB0-3B15-416E-93D6-0FCF52BAEA38'
    return guid


def new_node_id():
    return str(uuid.uuid4())


def version_string():
    return datetime.datetime.utcnow().strftime("%y%m%d")


def wait_random_avg_1_sec():
    import random
    import time

    time.sleep(0.5 + random.random())