
# merge - merge two directories (aka folders)

import os
import sys
import platform
import logger
import util
import logging
import walker
import folder
import argparse

MODE_UNDEFINED, MODE_ANALYZE, MODE_COPY, MODE_MOVE = tuple(range(4))
EXISTS_EXACT, EXISTS_ELSEWHERE, EXISTS_CONFLICT, DOES_NOT_EXIST = tuple(range(4))

def str_to_mode(str):
    mode = MODE_UNDEFINED
    c = str[0].lower()
    if c == 'c':
        mode = MODE_COPY
    elif c == 'm':
        mode = MODE_MOVE
    elif c == 'a':
        mode = MODE_ANALYZE
    return mode

def mode_to_str(mode):
    str = None
    if mode == MODE_MOVE:
        str = "move"
    elif mode == MODE_COPY:
        str = "copy"
    elif mode == MODE_ANALYZE:
        str = "analyze"
    return str

def search_result_to_str(search_result):
    str = None
    if search_result == DOES_NOT_EXIST:
        str = "does_not_exist"
    elif search_result == EXISTS_CONFLICT:
        str = "conflict"
    elif search_result == EXISTS_ELSEWHERE:
        str = "exists_elsewhere"
    elif search_result == EXISTS_EXACT:
        str = "exists_exact"
    elif search_result is None:
        str = "not_accessible"
    return str

class merge:
    def __init__(self, source_root, out_file_path = None, dest_root = None, verbose = False, metadata_root_override = None, mode = MODE_MOVE):
        self.log = logger.get_log()

        self.mode = mode
        self.verbose = verbose

        self.source = folder.folder(source_root, metadata_root_override)
        if self.verbose:
            print "source : metadata_db_path :", self.source.get_metadata_db_path()
        if dest_root is None:
            self.dest = None
        else:
            self.dest = folder.folder(dest_root, metadata_root_override)
            if self.verbose:
                print "dest : metadata_db_path :", self.source.get_metadata_db_path()

        self.out_file = None
        self.out_file_path = out_file_path

        if self.out_file_path is not None:
            try:
                self.out_file = open(out_file_path, "w")
            except:
                sys.exit("error : could not open : " + self.out_file_path)

        self.log.info('"computer","%s"',platform.node())
        self.log.info('"source_root","%s"',self.source.root)
        if self.dest is not None:
            self.log.info('"dest_root","%s"', self.dest.root)

        if self.dest is not None:
            scan_dest = folder.folder(self.dest.root, self.dest.metadata_root)
            scan_dest.scan()

    def __del__(self):
        if self.out_file is not None:
            self.log.warning("did not close out_file : " + self.out_file_path)
            self.out_file.close()
            self.out_file = None

    def compare(self, partial_path):
        found_paths = None
        dest_hash = None
        source_path = os.path.join(self.source.root, partial_path)
        dest_path = os.path.join(self.dest.root, partial_path)
        source_hash, src_cache = self.source.target_hash.get_hash(source_path)
        if os.path.exists(dest_path):
            dest_hash, dest_cache = self.dest.target_hash.get_hash(dest_path)
        if source_hash == dest_hash:
            result = EXISTS_EXACT
            found_paths = dest_path
        else:
            if os.path.exists(dest_path):
                # not the same contents, but already exists
                result = EXISTS_CONFLICT
            else:
                # Doesn't exist at dest, but first see if it exists anywhere
                dest_hash_root = util.get_abs_path_wo_drive(self.dest.root)
                found_paths = self.dest.target_hash.get_paths_from_hash(source_hash, dest_hash_root)
                if found_paths is None:
                    result = DOES_NOT_EXIST
                else:
                    result = EXISTS_ELSEWHERE
        return result, found_paths

    # Merge a file.
    # file_path is the path inside the src or dest (the 'right side' of the path, i.e. without the root)
    def merge_file(self, file_path):
        search_result, search_paths = self.compare(file_path)
        # if there is no dest_path, then we are merely indexing
        # todo: does it make sense to separate out the indexing capability from the merging?  It seems confusing for them to be 'one thing'.
        if search_result == DOES_NOT_EXIST:
            self.out_file.write(mode_to_str(self.mode) + " " + os.path.join(self.source.root, file_path) + " " + os.path.join(self.dest.root, file_path) + "\n")
        else:
            self.out_file.write("REM " + search_result_to_str(search_result) + " " + os.path.join(self.source.root, file_path) + " " + os.path.join(self.dest.root, file_path) + "\n")
        return search_result, search_paths

    def run(self):
        if self.verbose:
            if self.out_file is not None:
                self.out_file.write("REM " + str(sys.argv) + "\n")
                self.out_file.write("REM source " + self.source.root + "\n")
                if self.dest.root is not None:
                    self.out_file.write("REM dest " + self.dest.root + "\n")
        if not os.path.exists(self.source.root):
            print "Source does not exist :", self.source.root
            print "Exiting"
            return False
        if self.dest is not None:
            if not os.path.exists(self.source.root):
                print "Source does not exist :", self.source.root
                print "Exiting"
                return False

        if self.mode is MODE_ANALYZE:
            self.analyze()
        else:
            # move or copy
            source_walker = walker.walker(self.source.root)
            for file_path in source_walker:
                self.merge_file(file_path)

    def close(self):
        if self.out_file is not None:
            self.out_file.close()
            self.out_file = None

    def clean(self):
        self.source.target_hash.clean()
        if self.dest is not None:
            self.dest.target_hash.clean()

if __name__ == "__main__":
    log = logger.get_log()

    epilog = """
Execute with no arguments to run the GUI version.

Command line example:
""" + os.path.split(sys.argv[0])[-1] + " -s my_source -d my_dest"

    parser = argparse.ArgumentParser(epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-s", "--source", help="path to source directory/folder")
    parser.add_argument("-d", "--dest", default = None, help="path to destination directory/folder")
    parser.add_argument("-m", "--mode", nargs=1, default = 'm', choices='acm', help="analyze, copy or move")
    parser.add_argument("-o", "--outfile", help="output file path")
    parser.add_argument("-t", "--test", nargs=1, help="special test parameters (metadata path)", default = None)
    parser.add_argument("-v", "--verbose", help="print informational messages", action="store_true")

    args = parser.parse_args()
    if args.source is None:
        # stub for GUI version
        sys.exit("-h for help")
    if args.test is None:
        metadata_root_override = None
    else:
        metadata_root_override = args.test[0]
    verbose = args.verbose
    mode = str_to_mode(args.mode)
    source = util.decode_text(args.source)
    dest = util.decode_text(args.dest)
    out_file_path = args.outfile

    logger.setup()
    if verbose:
        log.setLevel(logging.INFO)
    m = merge(source, out_file_path , dest, verbose = verbose,
                     metadata_root_override = metadata_root_override,
                     mode = mode)
    m.run()
    m.close()