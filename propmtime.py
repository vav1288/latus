
# propagate the modification time of a folder/directory from its children (files or folders/directories)

# discussion:
# Many OSs (including Windows) only change the modification time of a folder/directory based on its
# immediate children.  This code analyzes a folder and its children, propagating (changing) the
# modification times of each folder to be the most recent time of all of its children

import win32con
import os
import argparse
import time
from . import util

class propmtime():
    def __init__(self, root, process_hidden = False, process_system = False, print_flag = False):
        self.root = util.decode_text(root)
        self.process_hidden = process_hidden
        self.process_system = process_system
        self.print_flag = print_flag

    def run(self):
        self.error_count = 0
        self.files_folders_count = 0
        start_time = time.time()

        for path, dirs, files in os.walk(self.root, topdown=False):
            latest_time = 0 # empty folders get an mtime of the epoch
            for fs_obj in dirs + files:
                long_full_path = util.get_long_abs_path(os.path.join(path, fs_obj))

                # decide if we're going to process this file
                process_the_file = self.process_hidden and self.process_system # if were processing all files, avoid the call to get the attributes
                if not process_the_file:
                    file_attrib = util.get_file_attributes(long_full_path)
                    process_the_file = not file_attrib or \
                                       (self.process_hidden and win32con.FILE_ATTRIBUTE_HIDDEN in file_attrib) or\
                                       (self.process_system and win32con.FILE_ATTRIBUTE_SYSTEM in file_attrib)

                if process_the_file:
                    self.files_folders_count += 1
                    try:
                        mtime = os.path.getmtime(long_full_path)
                        if mtime > start_time:
                            # Sometimes mtime can be in the future (and thus invalid).
                            # Try to use the ctime if it is.
                            mtime = os.path.getctime(long_full_path)
                    except WindowsError:
                        if self.print_flag:
                            print((util.encode_text(long_full_path), details))
                        self.error_count += 1
                    # make sure it's still not in the future ... if it is, ignore it
                    if mtime <= start_time:
                        latest_time = max(mtime, latest_time)

            long_path = util.get_long_abs_path(path)
            try:
                mtime = os.path.getmtime(long_path)
                # don't change it if it's close (there can be rounding errors, etc.)
                if abs(latest_time - mtime) > 2:
                    os.utime(long_path, (latest_time, latest_time))
            except WindowsError:
                if self.print_flag:
                    print((util.default_text_encoding(long_path), details))
                self.error_count += 1

        self.total_time = time.time() - start_time

        return os.path.getmtime(self.root)

    def print_stats(self):
        if self.error_count > 0:
            print((self.error_count, "total errors"))
        print(("total files/folders/directories:", self.files_folders_count))
        print(("elapsed time:", self.total_time, "sec"))

if __name__ == "__main__":
    desc = """Many OSs (including Windows) only change the modification time of a folder/directory based on its
immediate children.  This code analyzes a folder and all of its children, and propagates (changes) the
modification times of each folder to be the most recent time of all of its children."""
    epi = """Examples:
propmtime.py -p documents          # process all normal files in the 'documents' folder
propmtime.py -p documents -a h s   # process hidden and system files as well as normal files
propmtime.py -p documents -a s -v  # process system files as well as normal files, and turn on verbose"""
    parser = argparse.ArgumentParser(description=desc, epilog=epi, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-p", "--path", required=True, help="path to folder or directory")
    parser.add_argument("-a", "--attrib", nargs = "+", default = (''),
                        help="""ATTRIB can be h(idden) and/or s(ystem)to process hidden and/or system files.
Default is to ignore hidden and system files."""
                        )
    parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
    args = parser.parse_args()

    process_hidden = False
    process_system = False
    for a in args.attrib:
        a = a.lower()
        a = a[0]
        if a == "h":
            process_hidden = True
        elif a == 's':
            process_system = True

    pmt = propmtime(args.path, process_hidden, process_system, args.verbose)

    if not os.path.isdir(util.get_long_abs_path(args.path)):
        print(("error:", args.path, "is not a folder/directory"))
        print ("exiting...")
        exit()
    if args.verbose:
        print(("path:", args.path))

    pmt.run()
    if args.verbose:
        pmt.print_stats()

