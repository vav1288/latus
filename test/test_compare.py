
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
    assert(x_minus_y[0][1] == test.create_files.A_FILE_NAME)
    # call difference with the ignore_* True just to test those code paths
    dbx.difference(x_folder, y_folder, hidden=True, system=True)

    # test intersection
    intersection = dbx.intersection(x_folder, y_folder)
    assert(intersection[0][1] == test.create_files.B_FILE_NAME)

    # this is like a merge, where x is merged into y and the result is all the files
    assert(len(x_minus_y + test.create_files.y_folder_files) == 3)

    simple_root = test.create_files.get_simple_root()
    dbx.scan(simple_root)
    non_uniques = dbx.non_uniques(simple_root) # only one item is returned
    _, paths = non_uniques.popitem() # now pop that one item
    assert(len(non_uniques) == 0) # check that only one content ('a') appeared more than once
    assert(len(paths) == 3) # there are 3 different files in "simple" that have just 'a' in them

    random_root_a, random_root_b = test.create_files.get_random_roots()
    dbx.scan(random_root_a)
    dbx.scan(random_root_b)
    # we happen to know there are 5 files in the intersection
    #for f in dbx.intersection(random_root_a, random_root_b):
    #    print(f)
    assert(len(dbx.intersection(random_root_a, random_root_b)) == 5)
    a_minus_b = dbx.difference(random_root_a, random_root_b)
    b_minus_a = dbx.difference(random_root_b, random_root_a)
    print('a_minus_b', a_minus_b)
    print('b_minus_a', b_minus_a)
    # todo: do an assert on the above paths

    # for some reason we need to close the db so the next test can run
    dbx.close()
    dby.close()