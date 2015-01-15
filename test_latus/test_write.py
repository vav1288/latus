
import os
import time
import subprocess
import test_latus.create_files
import test_latus.conftest
import test_latus.run_nodes
import latus.util


def test_write():

    def write_all():
        test_name = 'write'
        proc_a, folder_a = test_latus.run_nodes.start_one('a', test_name)
        file_a = 'a.txt'
        time.sleep(2)
        proc_b, folder_b = test_latus.run_nodes.start_one('b', test_name)
        file_b = 'b.txt'

        time.sleep(10)

        latus.logger.log.info("*************** STARTING WRITE *************")
        test_latus.run_nodes.write_one(folder_a, file_a, 'a')
        time.sleep(5)
        test_latus.run_nodes.write_one(folder_b, file_b, 'b')
        time.sleep(5)
        latus.logger.log.info("*************** ENDING WRITE *************")

        assert(test_latus.run_nodes.wait_for_file(os.path.join(folder_a, file_b)))
        assert(test_latus.run_nodes.wait_for_file(os.path.join(folder_b, file_a)))

        time.sleep(5)  # wait for all DBs to be written (is there a better way? - need to have a file based way to terminate instead of proc.terminate() )

        # doesn't seem to work:
        #proc_a.communicate('q\n')
        #proc_b.communicate('q\n')

        # use this instead:
        proc_a.terminate()
        proc_b.terminate()

    def run():
        test_latus.conftest.init()
        test_latus.create_files.clean()
        test_latus.create_files.write_files()
        write_all()

    # finally, run the test!
    run()