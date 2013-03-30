
import os
import win32api
import win32con
import platform
import pywintypes
import unicodedata
import logger

text_normalization = 'NFC'
text_encoding = 'utf8'

# for when we go to Python 3.x:
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
    if is_windows():
        abs_path = u"\\\\?\\" + os.path.abspath(in_path)
    else:
        abs_path = os.path.abspath(in_path)
    return abs_path

# if this path has a drive specifier (as found in Windows), remove it
def remove_drive_spec(p):
    if p[0].isalpha() and p[1] == u":":
        p = os.path.splitdrive(p)[1]
    return p

def get_abs_path_wo_drive(p):
    p = os.path.abspath(p)
    p = remove_drive_spec(p)
    return p

def get_file_attributes(in_path):
    attrib = 0
    hidden_flag = False
    system_flag = False
    if is_windows():
        long_abs_path = get_long_abs_path(in_path)
        try:
            attrib = win32api.GetFileAttributes(long_abs_path)
        except pywintypes.error, details:
            logger.get_log().error(details + u"," + long_abs_path)
        except UnicodeDecodeError, details:
            logger.get_log().error(details + u"," + long_abs_path)
        hidden_flag = attrib & win32con.FILE_ATTRIBUTE_HIDDEN
        system_flag = attrib & win32con.FILE_ATTRIBUTE_SYSTEM
    # todo : Linux version of this
    return hidden_flag, system_flag

# From: "Getting unicode right in Python" by Nick Johnson
# 1) All text strings, everywhere should be of type unicode, not str. If you're handling text, and your variable is a
#    str, it's a bug!
# 2) To decode a byte string as text, use var.decode(encoding) (eg, var.decode('utf-8'), with the correct encoding.
#    To encode a text string as bytes, use var.encode(encoding).
# 3) Never ever use str() on a unicode string, or unicode() on a byte string without a second argument specifying the
#    encoding.
# 4) Whenever you read data from outside your app, expect it to be bytes - eg, of type str - and call .decode() on
#    it to interpret it as text. Likewise, always call .encode() on text you want to send to the outside world.
# 5) If a string literal in your code is intended to represent text, it should always be prefixed with 'u'. In fact,
#    you probably never want to define a raw string literal in your code at all.

# Unicode Normalization Forms
# https://www.dropbox.com/developers/core/api
# http://unicode.org/reports/tr15/
# http://docs.python.org/2/library/unicodedata.html

# call this for all strings we read in
def decode_text(in_text):
    return in_text.decode(text_encoding)

# call this for all string we write out (e.g. to database or print statements)
def encode_text(in_text):
    norm_text = unicodedata.normalize(text_normalization, in_text)
    e_text = norm_text.encode(text_encoding)
    return e_text


