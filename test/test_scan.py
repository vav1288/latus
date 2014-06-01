
import os
import core.db
import core.metadatapath
import test.util
import test.results
import test.create_files
from test.conftest import setup

class Scan():
    def __init__(self):
        self.test_files = test.create_files.TestFiles()

    def scan(self, path):
        db = core.db.DB(path, core.metadatapath.MetadataPath(test.create_files.get_metadata_root()))
        db.scan()

    def get_info(self, path):
        db = core.db.DB(path, core.metadatapath.MetadataPath(test.create_files.get_metadata_root()))
        return(db.get_info(path))

def test_scan_simple(setup):
    t = Scan()
    root = test.create_files.get_simple_root()
    t.scan(root)
    a_path = os.path.join(test.create_files.SRC, test.create_files.A_FILE_NAME)
    assert(a_path != None)
    if a_path is not None:
        sha512_val = t.get_info(a_path).sha512
        assert(sha512_val == test.results.sha512[test.create_files.A_STRING])

def test_scan_unicode(setup):
    t = Scan()
    t.scan(test.create_files.get_unicode_root())

