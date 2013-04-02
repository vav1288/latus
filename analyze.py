
import argparse
import logging
import os
import sys
import platform
import collections
import logger
import util
import folder

class analyze:
    def __init__(self, path, metadata_root_override, verbose = False):
        self.log = logger.get_log()
        self.verbose = verbose
        self.path = path

        self.folder = folder.folder(path, metadata_root_override, verbose)
        if self.verbose:
            print "metadata_db_path :", self.folder.get_metadata_db_path()

        self.log.info('"computer","%s"',platform.node())
        self.log.info('"path","%s"',self.path)

    def run(self):
        if self.verbose:
            print "analyze :", self.path
        file_count = 0
        self.folder.scan() # ensure metadata is up to date
        hash_counts = collections.defaultdict(int)
        for file_path in self.folder.get_walker():
            full_path = self.folder.get_walker().get_path(file_path) # ugly ...
            #if self.verbose:
            #    print "analyze", util.encode_text(full_path)
            hash_val = self.folder.get_hash(full_path)
            hash_counts[hash_val] += 1
            file_count += 1
        for h in collections.Counter(hash_counts):

            # todo: CLEAN THIS UP!!! UGLY!!!
            p = util.get_abs_path_wo_drive(self.path)
            paths = self.folder.target_hash.get_paths_from_hash(h, p)

            # todo: bug fix : this yields all the files with this hash ... need to only give the ones
            # that are in the tree below self.source_root .
            if paths is not None:
                # todo : figure out how paths can be None
                if len(paths) > 1:
                    print len(paths)
                    for p in paths:
                        print util.encode_text(p)
        if self.verbose:
            print "total files analyzed :", file_count
        return hash_counts

if __name__ == "__main__":
    logger.setup()
    log = logger.get_log()

    epilog = """
Execute with no arguments to run the GUI version.

Command line example:
""" + os.path.split(sys.argv[0])[-1] + " -s my_source -d my_dest"

    parser = argparse.ArgumentParser(epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-p", "--path", help="path to directory/folder to analyze")
    parser.add_argument("-o", "--outfile", help="output file path")
    parser.add_argument("-t", "--test", nargs=1, help="special test parameters (metadata path)", default = None)
    parser.add_argument("-v", "--verbose", help="print informational messages", action="store_true")

    args = parser.parse_args()
    if args.path is None:
        print "no arguments - stub for GUI version"
        exit()
    if args.test is None:
        metadata_root_override = None
    else:
        metadata_root_override = args.test[0]
    verbose = args.verbose
    path = util.decode_text(args.path)

    if verbose:
        log.setLevel(logging.INFO)
    a = analyze(path, metadata_root_override, verbose)
    a.run()