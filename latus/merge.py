
# merge - merge two directories (aka folders)

import os
import sys
import platform
import collections
from . import hash, logger, util, walker, metadata_location


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
        str = "finddup"
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
    def __init__(self, source_root, out_file_path = None, dest_root = None, verbose = False, metadata_override = None, mode = MODE_MOVE):
        self.log = logger.get_log()

        self.source_root = source_root
        self.dest_root = dest_root
        self.mode = mode
        self.verbose = verbose

        self.source = hash.hash(source_root, metadata_override)
        #if self.verbose:
        #    print(("source : metadata_db_path :", self.source.get_metadata_db_path()))
        if dest_root is None:
            self.dest_hash = None
        else:
            self.dest_hash = hash.hash(dest_root, metadata_override)
            #if self.verbose:
            #    print(("dest : metadata_db_path :", self.source.get_metadata_db_path()))

        self.out_file = None
        self.out_file_path = out_file_path

        if self.out_file_path is not None:
            try:
                self.out_file = open(out_file_path, "w")
            except:
                sys.exit("error : could not open : " + self.out_file_path)

        self.log.info('"computer","%s"',platform.node())
        self.log.info('"source_root","%s"', source_root)
        if self.dest_hash is not None:
            self.log.info('"dest_root","%s"', dest_root)

        if self.dest_hash is not None:
            scan_dest = hash.hash(dest_root, self.dest_hash.metadata_root)
            scan_dest.scan(dest_root)

    def __del__(self):
        if self.out_file is not None:
            self.log.warning("did not close out_file : " + self.out_file_path)
            self.out_file.close()
            self.out_file = None

    def compare(self, partial_path):
        found_paths = None
        dest_hash = None
        source_path = os.path.join(self.source_root, partial_path)
        dest_path = os.path.join(self.dest_root, partial_path)
        source_hash, src_cache, src_count = self.source.get_hash(source_path)
        if os.path.exists(dest_path):
            dest_hash, dest_cache, dest_count = self.dest_hash.get_hash(dest_path)
        if source_hash == dest_hash:
            result = EXISTS_EXACT
            found_paths = dest_path
        else:
            if os.path.exists(dest_path):
                # not the same contents, but already exists
                result = EXISTS_CONFLICT
            else:
                # Doesn't exist at dest, but first see if it exists anywhere
                dest_hash_root = util.get_abs_path_wo_drive(self.dest_root)
                found_paths = self.dest_hash.get_paths_from_hash(source_hash)
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
            self.out_file.write(mode_to_str(self.mode) + " " + os.path.join(self.source_root, file_path) + " " + os.path.join(self.dest_root, file_path) + "\n")
        else:
            self.out_file.write("REM " + search_result_to_str(search_result) + " " + os.path.join(self.source_root, file_path) + " " + os.path.join(self.dest_root, file_path) + "\n")
        return search_result, search_paths

    def run(self):
        if self.verbose:
            if self.out_file is not None:
                self.out_file.write("REM " + str(sys.argv) + "\n")
                self.out_file.write("REM source " + self.source_root + "\n")
                if self.dest_root is not None:
                    self.out_file.write("REM dest " + self.dest_root + "\n")
        if not os.path.exists(self.source_root):
            print(("Source does not exist :", self.source_root))
            print ("Exiting")
            return False
        if self.dest_hash is not None:
            if not os.path.exists(self.source_root):
                print(("Source does not exist :", self.source_root))
                print ("Exiting")
                return False

        if self.mode is MODE_ANALYZE:
            self.analyze()
        else:
            # move or copy
            source_walker = walker.walker(self.source_root)
            for file_path in source_walker:
                self.merge_file(file_path)

    def find_best_merge_location(self):
        #source_metadata_root = metadata_location.get_metadata_root(self.source_root, None)
        #source_walker = walker.walker(self.source_root)
        #source_hash = hash.hash(self.source_root, util.Metadata(source_metadata_root, self.__module__))

        dest_metadata_root = metadata_location.get_metadata_root(self.dest_root, None)
        trial_dest_walker = walker.walker(self.dest_root)
        #dest_hash = hash.hash(self.dest_root, util.Metadata(dest_metadata_root, self.__module__))

        BestMatch = collections.namedtuple('BestMatch', ['paths', 'count'])
        best_match = BestMatch(None,0)

        for trial_dest_partial_path in trial_dest_walker:
            trial_dest_full_path = trial_dest_walker.get_path(trial_dest_partial_path)
            if os.path.isdir(trial_dest_full_path):
                # print("trial_dest_full_path", trial_dest_full_path)
                match_value = self.compare_folders(trial_dest_full_path, self.source_root)
                if match_value > best_match.count:
                    best_match = BestMatch([trial_dest_full_path], match_value)
        print (best_match)
        return best_match

    def compare_folders(self, a, b):
        # print(a, b)
        count = 0
        aw = walker.walker(a)
        for af in aw:
            ap = aw.get_path(af)
            if os.path.isfile(ap):
                bp = os.path.join(b, af)
                if os.path.isfile(bp):
                    # todo: compare contents
                    count += 1
        return count

    def close(self):
        if self.out_file is not None:
            self.out_file.close()
            self.out_file = None

    def clean(self):
        self.source.clean()
        if self.dest_hash is not None:
            self.dest_hash.clean()

