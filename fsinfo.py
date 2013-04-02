
import os
import sys
import win32con
import time
import util
import logger

class fsinfo:
    def __init__(self, root):
        self.root = util.decode_text(root)
        self.earliest_believable_time = 365 * 24 * 60 * 60 # some (relatively short) time after the epoch
        #print time.asctime(time.localtime(self.earliest_believable_time))

    def run(self):
        print u"path", u"\"" + self.root + u"\""
        self.file_count = 0
        self.dir_count = 0
        self.total_size = 0
        self.system_count = 0
        self.hidden_count = 0
        self.earliest_path = None
        self.earliest_time = -1
        self.latest_path = None
        self.latest_time = -1
        for root, dirs, files in os.walk(self.root):
            for name in files:
                path = os.path.join(root, name)
                long_abs_path = util.get_long_abs_path(path)
                self.file_count += 1
                self.total_size += os.path.getsize(long_abs_path)
                attributes = util.get_file_attributes(path)
                if win32con.FILE_ATTRIBUTE_HIDDEN in attributes:
                    self.hidden_count += 1
                if win32con.FILE_ATTRIBUTE_SYSTEM in attributes:
                    self.system_count += 1
                mtime = os.path.getmtime(long_abs_path)
                # Some mtime are not valid.  Try to filter out the bad ones.
                # If a file says its from the future or very short period of time after the epoch, don't believe it.
                if mtime >= self.earliest_believable_time and mtime <= time.time():
                    if self.earliest_path is None or mtime < self.earliest_time:
                        self.earliest_path = path
                        self.earliest_time = mtime
                    if self.latest_path is None or mtime > self.latest_time:
                        self.latest_path = path
                        self.latest_time = mtime
            for d in dirs:
                self.dir_count += 1
        print u"file_count", self.file_count
        print u"system_count", self.system_count
        print u"hidden_count", self.hidden_count
        print u"total_size", self.total_size
        print u"dir_count", self.dir_count
        if self.earliest_path is not None:
            print u"earliest \"" + self.earliest_path + u"\"", u"\"" + time.asctime(time.localtime(self.earliest_time)) + u"\"", self.earliest_time
        if self.latest_path is not None:
            print u"latest \"" + self.latest_path + u"\"", u"\"" + time.asctime(time.localtime(self.latest_time)) + u"\"", self.latest_time

if __name__ == "__main__":
    logger.setup()
    if len(sys.argv) < 2:
        path = u"."
    else:
        path = sys.argv[1]
    path = util.decode_text(path)
    info = fsinfo(path)
    info.run()
