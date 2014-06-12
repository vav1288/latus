
import os
import core.const
import core.db
import core.metadatapath
import test.const
import test.util
import test.results
import test.create_files
from test.conftest import setup

def test_scan_simple(setup):
    db = core.db.DB(core.metadatapath.MetadataPath(test.create_files.get_metadata_root()), force_drop=True)
    db.scan(test.create_files.get_simple_root())
    a_path = os.path.join(test.create_files.SRC, test.create_files.A_FILE_NAME)
    assert(a_path != None)
    if a_path is not None:
        sha512_val = db.get_file_info(a_path).sha512
        assert(sha512_val == test.results.sha512[test.create_files.A_STRING])

def test_scan_unicode(setup):
    db = core.db.DB(core.metadatapath.MetadataPath(test.create_files.get_metadata_root()), force_drop=True)
    db.scan(test.create_files.get_unicode_root())

def test_new_root(setup):
    db = core.db.DB(core.metadatapath.MetadataPath(test.create_files.get_metadata_root()), force_drop=True)
    db.scan(test.create_files.get_simple_root())
    db = core.db.DB(core.metadatapath.MetadataPath(test.create_files.get_metadata_root()))
    db.scan(test.create_files.get_unicode_root())

def test_hash_time(setup):
    db = core.db.DB(core.metadatapath.MetadataPath(os.path.join(test.create_files.get_metadata_root(), 'hashtime')))
    db.scan(test.create_files.get_hash_root())
    hash_perfs = db.get_hash_perf()
    assert(len(hash_perfs) == core.const.MAX_HASH_PERF_VALUES) # make sure the table is full
    files_in_hash_perf = [os.path.abspath(os.path.join(test.create_files.get_hash_root(), 'big' + str(i) + '.txt'))
                          for i in range(core.const.MAX_HASH_PERF_VALUES,test.const.HASH_TEST_FILE_MAX+1)]
    # make sure the entries in the table are for the largest files
    for hash_perf in hash_perfs:
        assert(hash_perf.abspath in files_in_hash_perf)


