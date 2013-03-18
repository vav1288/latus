
# merge - merge two directories (aka folders)

import os
import sys
import platform
import collections
import logger
import hash
import walker
import scan
import target
import metadata_location

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

        self.source = target.target(source_root, metadata_root_override)
        if self.verbose:
            print "source : metadata_db_path :", self.source.get_metadata_db_path()
        if dest_root is None:
            self.dest = None
        else:
            self.dest = target.target(dest_root, metadata_root_override)
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
            scan_dest = scan.scan(self.dest.root, self.dest.metadata_root)
            scan_dest.run()

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
                # in order to avoid making redundant copies.
                found_paths = None
                dest_hash_root = os.path.splitdrive(os.path.abspath(self.dest.root))[1]
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

    def analyze(self):
        if self.verbose:
            print "analyze :", self.source.root
        # refresh the metadata
        scan_source = scan.scan(self.source.root, self.source.metadata_root)
        scan_source.run()
        hash_counts = collections.defaultdict(int)
        # the iterator uses self.source_root (not sure if I like this or not, but not sure what else to do)
        source_walker = walker.walker(self.source.root)
        for file_path in source_walker:
            src_hash_val, src_cache_flag = self.source.target_hash.get_hash(source_walker.get_path(file_path))
            if src_hash_val is None:
                self.log.error("%s %s", file_path, src_hash_val)
            hash_counts[src_hash_val] += 1
        for h in collections.Counter(hash_counts):
            paths = self.source.target_hash.get_paths_from_hash(h)
            # todo: bug fix : this yields all the files with this hash ... need to only give the ones
            # that are in the tree below self.source_root .
            if paths is not None:
                # todo : figure out how paths can be None
                if len(paths) > 1:
                    print len(paths)
                    for p in paths:
                        print p

    def run(self):
        if self.verbose:
            if self.out_file is not None:
                self.out_file.write("REM " + __name__ + "\n")
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
    #m = merge(os.path.join("test", "simple"), verbose=True, mode=MODE_MOVE)
    #m.run()
    print "Do not use this program directly."
    print "Use merge_cli."