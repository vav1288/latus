
import platform
import collections
from . import hash, logger, walker, util

class finddup:
    def __init__(self, path, metadata_override, verbose = False):
        self.verbose = verbose
        self.path = path

        self.hash = hash.hash(path, metadata_override, verbose)
        self.walker = walker.walker(path)

        logger.get_log().info('"computer","%s"',platform.node())
        logger.get_log().info('"path","%s"',self.path)

    def run(self):
        if self.verbose:
            print(("finddup :", self.path))
        file_count = 0
        self.hash.scan(self.path) # ensure metadata is up to date
        hash_counts = collections.defaultdict(int)
        for file_path in self.walker:
            full_path = self.walker.get_path(file_path) # ugly ...
            #if self.verbose:
            #    print ("finddup", full_path)
            hash_val, hash_cache_flag, entry_count = self.hash.get_hash(full_path)
            hash_counts[hash_val] += 1
            file_count += 1
        #pprint.pprint(hash_counts)
        dups = []
        for h in collections.Counter(hash_counts):
            file_list = []
            paths = self.hash.get_paths_from_hash(h)
            if len(paths) > 1:
                for p in paths:
                    file_list.append(p)
            dups.append(file_list)
        print("-------------------")
        for file_list in dups:
            length = len(file_list)
            if length > 0:
                print (length)
                for file in file_list:
                    print (file)
        print("-------------------")
        if self.verbose:
            print(("total files analyzed :", file_count))
        if not len(hash_counts):
            print ("All files unique")
        return dups

