
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
    metadata_path = os.path.join(test.create_files.get_metadata_root(), 'diff')
    x_folder = os.path.join(test.create_files.get_compare_root(), test.const.X_FOLDER)
    y_folder = os.path.join(test.create_files.get_compare_root(), test.const.Y_FOLDER)
    dbx = core.db.DB(x_folder, core.metadatapath.MetadataPath(metadata_path), force_drop=True)
    dbx.scan()
    dby = core.db.DB(y_folder, core.metadatapath.MetadataPath(metadata_path))
    dby.scan()
    a_minus_b, b_minus_a, intersection = dbx.compare(x_folder, y_folder)
    assert(a_minus_b == {test.create_files.A_FILE_NAME})
    assert(b_minus_a == {test.create_files.C_FILE_NAME})
    assert(intersection == {test.create_files.B_FILE_NAME})
    # call it with the ignore_* True to test those code paths
    a_minus_b, b_minus_a, intersection = dbx.compare(x_folder, y_folder, hidden=True, system=True)
    dbx.close()
    dby.close()