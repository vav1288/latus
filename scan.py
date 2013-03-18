
import os
import win32con
import win32api
import pywintypes
import hash
import os_util
import walker
import logger

class scan():
    def __init__(self, root, metadata_root):
        self.root = root
        self.metadata_root = metadata_root

    # Scan a single file.  This will update the metadata for this file.
    # Path is the partial path from the 'root' of the source (or dest).  i.e. that part to the 'right' of the root.
    def scan_file(self, file_path, attrib_mask = win32con.FILE_ATTRIBUTE_HIDDEN | win32con.FILE_ATTRIBUTE_SYSTEM):
        hash_result = None
        cache_result = None
        #dir_abs_path_no_drive = os.path.abspath(self.root)[2:]
        attrib = 0
        abs_source_path = os_util.get_long_abs_path(file_path)
        try:
            # Trick to get around 260 char limit
            # http://msdn.microsoft.com/en-us/library/aa365247.aspx#maxpath
            attrib = win32api.GetFileAttributes(abs_source_path)
        except pywintypes.error, details:
            logger.get_log().error(str(details) + "," + abs_source_path)
        except UnicodeDecodeError, details:
            logger.get_log().error(str(details) + "," + abs_source_path)
        if not (attrib & attrib_mask):
            hash_obj = hash.hash(self.metadata_root)
            hash_result, cache_result = hash_obj.get_hash(file_path)
        #print file_path, hash_result, cache_result
        return hash_result, cache_result

    def run(self):
        analysis_walker = walker.walker(self.root)
        for partial_path in analysis_walker:
            file_path = analysis_walker.get_path(partial_path)
            self.scan_file(file_path)

if __name__ == "__main__":
    logger.setup()
    a = scan(os.path.join(u"test")) # note that this parameter MUST be unicode text
    a.run()