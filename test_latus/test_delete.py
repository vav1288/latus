
import os
import time

import test_latus.test_write
import test_latus.create_files
import test_latus.conftest
import latus.logger

def test_delete():

    def do_delete():
        file_name = 'a.txt'
        test_name = 'delete'
        proc_a, latus_folder_a = test_latus.run_nodes.start_one('a', test_name)
        time.sleep(2)
        proc_b, latus_folder_b = test_latus.run_nodes.start_one('b', test_name)

        file_path_a = os.path.join(latus_folder_a, file_name)
        file_path_b = os.path.join(latus_folder_b, file_name)

        latus.logger.log.info("*************** STARTING WRITE *************")
        test_latus.run_nodes.write_one(latus_folder_a, file_name, 'a')
        time.sleep(5)
        latus.logger.log.info("*************** ENDING WRITE *************")

        assert(test_latus.run_nodes.wait_for_file(file_path_b))  # make sure it's on b

        latus.logger.log.info("*************** STARTING DELETE *************")
        time.sleep(10)
        os.remove(file_path_a)  # remove it on a

        time.sleep(10)  # wait for it to happen
        latus.logger.log.info("*************** ENDING DELETE *************")

        # assert(not os.path.exists(file_path_b))  # make sure it's gone on b

        # todo: make this some sort of control flow based
        proc_a.terminate()
        proc_b.terminate()

    def run():
        test_latus.conftest.init()
        test_latus.create_files.clean()
        do_delete()

    # finally, run the test!
    run()