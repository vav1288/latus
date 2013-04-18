
import platform
import collections
from . import folder, logger, util

class analyze:
    def __init__(self, path, metadata_root_override, verbose = False):
        self.verbose = verbose
        self.path = path

        self.folder = folder.folder(path, metadata_root_override, verbose)
        if self.verbose:
            print(("metadata_db_path :", self.folder.get_metadata_db_path()))

        logger.get_log().info('"computer","%s"',platform.node())
        logger.get_log().info('"path","%s"',self.path)

    def run(self):
        if self.verbose:
            print(("analyze :", self.path))
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
                    print((len(paths)))
                    for p in paths:
                        print((util.encode_text(p)))
        if self.verbose:
            print(("total files analyzed :", file_count))
        if not len(hash_counts):
            print ("All files unique")
        return hash_counts

