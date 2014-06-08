
import os
import core.const
import core.db
import core.metadatapath
import test.const
import test.util
import test.results
import test.create_files
from test.conftest import setup

def test_scan_compare(setup):
    metadata_path = os.path.join(test.create_files.get_metadata_root(), 'compare')
    x_folder = os.path.join(test.create_files.get_compare_root(), test.const.X_FOLDER)
    y_folder = os.path.join(test.create_files.get_compare_root(), test.const.Y_FOLDER)
    dbx = core.db.DB(core.metadatapath.MetadataPath(metadata_path), force_drop=True)
    dbx.scan(x_folder)
    dby = core.db.DB(core.metadatapath.MetadataPath(metadata_path))
    dby.scan(y_folder)
    a_minus_b, intersection = dbx.compare(x_folder, y_folder)
    assert(a_minus_b == [test.create_files.A_FILE_NAME])
    assert(intersection == [test.create_files.B_FILE_NAME])
    # call it with the ignore_* True just to test those code paths
    dbx.compare(x_folder, y_folder, hidden=True, system=True)
    # for some reason we need to close the db so the next test can run
    dbx.close()
    dby.close()