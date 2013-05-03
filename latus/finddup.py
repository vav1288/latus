
import platform
import collections
import os
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

        # get a dict of hashes
        # todo:  should this just be a list instead of a dict?
        for file_path in self.walker:
            full_path = self.walker.get_path(file_path)
            #if self.verbose:
            #    print ("finddup", full_path)
            hash_val, hash_cache_flag, entry_count = self.hash.get_hash(full_path)
            hash_counts[hash_val] += 1
            file_count += 1
        #pprint.pprint(hash_counts)

        # get a dict that contains lists of the duplicate files
        # todo: we can have the same 'savings' for two sets of files - how to handle that?????
        dups = {}
        total_savings = 0
        for h in collections.Counter(hash_counts):
            file_list = []
            # todo: get this to work if you are executing from one drive and looking for dups on another
            paths = self.hash.get_paths_from_hash(h)
            if len(paths) > 1:
                size = os.path.getsize(paths[0])
                for p in paths:
                    file_list.append(p)
                savings = (len(paths) - 1) * size
                total_savings += savings
                dups[savings] = file_list

        # print the result
        found_at_least_one = False
        for savings in sorted(dups):
            if savings > 0:
                print("-------------------")
                print (len(dups[savings]), "files")
                print (savings, "bytes of savings")
                for file in dups[savings]:
                    print (file)
                found_at_least_one = True
        print("-------------------")

        print(total_savings, "total bytes of savings")
        if self.verbose:
            print(("total files analyzed :", file_count))
        if not found_at_least_one:
            print ("All files unique")
        return dups

