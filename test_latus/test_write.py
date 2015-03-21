
import os
import time

import test_latus.create_files
import test_latus.util
import latus.util
import latus.logger


def get_write_root():
    return os.path.join(test_latus.create_files.get_data_root(), "write")


def test_write(setup):

    test_latus.util.logger_init(os.path.join(get_write_root(), 'log'))

    test_name = 'write'
    proc_a, folder_a, log_a = test_latus.util.start_cmd_line('a', test_name)
    file_a = 'a.txt'
    proc_b, folder_b, log_b = test_latus.util.start_cmd_line('b', test_name)
    file_b = 'b.txt'

    log_folders = [log_a, log_b]

    test_latus.util.wait_on_nodes(log_folders)

    latus.logger.log.info("*************** STARTING WRITE *************")

    test_latus.create_files.write_to_file(os.path.join(folder_a, file_a), 'a')
    test_latus.util.wait_on_nodes(log_folders)
    test_latus.create_files.write_to_file(os.path.join(folder_b, file_b), 'b')
    test_latus.util.wait_on_nodes(log_folders)

    latus.logger.log.info("*************** ENDING WRITE *************")

    assert(test_latus.util.wait_for_file(os.path.join(folder_a, file_b)))
    assert(test_latus.util.wait_for_file(os.path.join(folder_b, file_a)))

    test_latus.util.wait_on_nodes(log_folders)

    # doesn't seem to work:
    #proc_a.communicate('q\n')
    #proc_b.communicate('q\n')

    # use this instead:
    proc_a.terminate()
    proc_b.terminate()

