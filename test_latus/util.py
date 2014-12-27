
import os
import time

# get an mtime back in time
def get_mtime_time():
    return time.mktime(time.strptime("12", "%y"))

def make_dirs(p):
    if not os.path.exists(p):
        os.makedirs(p)