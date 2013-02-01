
import os
import sys
import time
import win32api
import win32con

class fsinfo:
    def __init__(self, root):
        self.root = root
        self.earliest_believable_time = 365 * 24 * 60 * 60 # some (relatively short) time after the epoch
        #print time.asctime(time.localtime(self.earliest_believable_time))

    def run(self):
        print "path", "\"" + self.root + "\""
        self.file_count = 0
        self.dir_count = 0
        self.total_size = 0
        self.system_count = 0
        self.hidden_count = 0
        self.not_accessible = 0
        self.earliest_path = None
        self.earliest_time = -1
        self.latest_path = None
        self.latest_time = -1
        for root, dirs, files in os.walk(self.root):
            for name in files:
                path = os.path.join(root, name)
                self.file_count += 1
                # files in use, access denied, etc.
                try:
                    self.total_size += os.path.getsize(path)

                    self.attrib = win32api.GetFileAttributes(path)
                    if self.attrib & win32con.FILE_ATTRIBUTE_HIDDEN:
                        self.hidden_count += 1
                    if self.attrib & win32con.FILE_ATTRIBUTE_SYSTEM:
                        self.system_count += 1

                    mtime = os.path.getmtime(path)
                    # Some mtime are not valid.  Try to filter out the bad ones.
                    # If a file says its from the future or very short period of time after the epoch, don't believe it.
                    if mtime >= self.earliest_believable_time and mtime <= time.time():
                        if self.earliest_path is None or mtime < self.earliest_time:
                            self.earliest_path = path
                            self.earliest_time = mtime
                        if self.latest_path is None or mtime > self.latest_time:
                            self.latest_path = path
                            self.latest_time = mtime
                except:
                    self.not_accessible += 1
                    print "not_accessible", path
            for dir in dirs:
                self.dir_count += 1
        print "file_count", self.file_count
        print "system_count", self.system_count
        print "hidden_count", self.hidden_count
        print "total_size", self.total_size
        print "dir_count", self.dir_count
        print "not_accessible", self.not_accessible
        if self.earliest_path is not None:
            print "earliest", "\"" + self.earliest_path + "\"", "\"" + time.asctime(time.localtime(self.earliest_time)) + "\"", self.earliest_time
        if self.latest_path is not None:
            print "latest", "\"" + self.latest_path + "\"", "\"" + time.asctime(time.localtime(self.latest_time)) + "\"", self.latest_time

if __name__ == "__main__":
    if len(sys.argv) < 2:
        path = "."
    else:
        path = sys.argv[1]
    info = fsinfo(path)
    info.run()
