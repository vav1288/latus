
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

    # setups and scans
    metadata_path = os.path.join(test.create_files.get_metadata_root(), 'compare')
    x_folder = os.path.join(test.create_files.get_compare_root(), test.const.X_FOLDER)
    y_folder = os.path.join(test.create_files.get_compare_root(), test.const.Y_FOLDER)
    dbx = core.db.DB(core.metadatapath.MetadataPath(metadata_path), force_drop=True)
    dbx.scan(x_folder)
    dby = core.db.DB(core.metadatapath.MetadataPath(metadata_path))
    dby.scan(y_folder)

    # test difference
    x_minus_y = dbx.difference(x_folder, y_folder)
    assert(x_minus_y == [test.create_files.A_FILE_NAME])
    # call difference with the ignore_* True just to test those code paths
    dbx.difference(x_folder, y_folder, hidden=True, system=True)

    # test intersection
    intersection = dbx.intersection(x_folder, y_folder)
    assert(intersection == [test.create_files.B_FILE_NAME])

    # this is like a merge, where x is merged into y and the result is all the files
    assert(len(x_minus_y + test.create_files.y_folder_files) == 3)

    simple_root = test.create_files.get_simple_root()
    dbx.scan(simple_root)
    non_uniques_dict = dbx.non_uniques(simple_root)
    non_uniques = [non_uniques_dict[h] for h in non_uniques_dict.keys()]
    assert(len(non_uniques) == 1) # only one content appears more than once
    assert(len(non_uniques[0]) == 3) # there are 3 different files in "simple" that have just 'a' in them

    # for some reason we need to close the db so the next test can run
    dbx.close()
    dby.close()