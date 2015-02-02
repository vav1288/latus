
import os
import time

import test_latus.test_write
import test_latus.create_files
import test_latus.util
import test_latus.run_nodes
import latus.logger


def get_delete_root():
    return os.path.join(test_latus.create_files.get_data_root(), "delete")


def test_delete(setup):

    folders = test_latus.create_files.Folders(get_delete_root())
    test_latus.util.logger_init(folders.get_log_folder())
    test_name = 'delete'
    proc_a, folder_a, log_a = test_latus.run_nodes.start_one('a', test_name)
    file_a = 'a.txt'
    proc_b, folder_b, log_b = test_latus.run_nodes.start_one('b', test_name)

    log_folders = [log_a, log_b]

    test_latus.util.wait_on_nodes(log_folders)

    file_path_a = os.path.join(folder_a, file_a)
    file_path_b = os.path.join(folder_b, file_a)

    latus.logger.log.info("*************** STARTING WRITE *************")
    test_latus.create_files.write_to_file(os.path.join(folder_a, file_a), 'a')
    test_latus.util.wait_on_nodes(log_folders)
    latus.logger.log.info("*************** ENDING WRITE *************")

    assert(test_latus.run_nodes.wait_for_file(file_path_b))  # make sure it's on b

    latus.logger.log.info("*************** STARTING DELETE *************")
    test_latus.util.wait_on_nodes(log_folders)
    os.remove(file_path_a)  # remove it on a

    test_latus.util.wait_on_nodes(log_folders)  # wait for it to happen
    latus.logger.log.info("*************** ENDING DELETE *************")

    test_latus.util.wait_on_nodes(log_folders)

    assert(not os.path.exists(file_path_b))  # make sure it's gone on b

    # todo: make this some sort of control flow based
    proc_a.terminate()
    proc_b.terminate()
