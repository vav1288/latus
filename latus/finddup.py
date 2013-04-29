
import platform
import collections
from . import hash, logger, walker, util

class finddup:
    def __init__(self, path, metadata_override, verbose = False):
        self.verbose = verbose
        self.path = path

        self.hash = hash.hash(metadata_override, verbose)
        self.walker = walker.walker(path)
        #if self.verbose:
        #    print(("metadata_db_path :", self.folder.get_metadata_db_path()))

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
            hash_val, hash_cache_flag = self.hash.get_hash(full_path)
            hash_counts[hash_val] += 1
            file_count += 1
        #pprint.pprint(hash_counts)
        dups = []
        for h in collections.Counter(hash_counts):
            file_list = []
            # todo: CLEAN THIS UP!!! UGLY!!!
            paths = self.hash.get_paths_from_hash(h, self.path)
            if paths is not None:
                # todo : figure out how paths can be None
                if len(paths) > 1:
                    for p in paths:
                        file_list.append(p)
            dups.append(file_list)
        print("-------------------")
        for file_list in dups:
            print (len(file_list))
            for file in file_list:
                print (file)
        print("-------------------")
        if self.verbose:
            print(("total files analyzed :", file_count))
        if not len(hash_counts):
            print ("All files unique")
        return dups

