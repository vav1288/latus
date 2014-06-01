
import os
import core.db
import core.metadatapath
import test.util
import test.results
import test.test_files
from test.test_session import test_set_up

class Scan():
    def __init__(self):
        self.test_files = test.test_files.TestFiles()

    def scan(self, path):
        db = core.db.DB(path, core.metadatapath.MetadataPath(test.test_files.get_root()))
        db.scan()

    def get_info(self, path):
        db = core.db.DB(path, core.metadatapath.MetadataPath(test.test_files.get_root()))
        return(db.get_info(path))

def test_scan_simple(test_set_up):
    t = Scan()
    root = test.test_files.get_simple_root()
    t.scan(root)
    a_path = os.path.join(test.test_files.SRC, test.test_files.A_FILE_NAME)
    assert(a_path != None)
    if a_path is not None:
        sha512_val = t.get_info(a_path).sha512
        assert(sha512_val == test.results.sha512[test.test_files.A_STRING])

def test_scan_unicode(test_set_up):
    t = Scan()
    t.scan(test.test_files.get_unicode_root())

