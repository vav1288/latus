
import os
import time
import subprocess
import test_latus.create_files
import latus.util
from test_latus.conftest import setup


def test_multi(setup):

    def write_one(folder, file_name, s):
        if not os.path.exists(folder):
            os.mkdir(folder)
        with open(os.path.join(folder, file_name), 'w') as f:
            f.write(s)

    def start_one(node_id):
        multi_folder = os.path.join(test_latus.create_files.get_sync_root(), 'multi')
        node_folder = os.path.join(multi_folder, node_id)
        latus.util.make_dirs(node_folder)
        latus_folder = os.path.join(node_folder, 'latus')
        python_exe = os.path.join('c:', '/', 'python34', 'python.exe')
        print('python_exe', python_exe)
        cmd = [python_exe, 'latus.py']
        cmd += ['-l', latus_folder]
        # all nodes use same folder to emulate cloud sync
        cmd += ['-c', os.path.join(multi_folder, 'dropbox')]
        cmd += ['-a', os.path.join(node_folder, 'appdata')]
        cmd += ['-k', 'dQf6js1s-CcVRQMnt6t4w7fOdVJAzqhvcQNsHnvuQNQ=']
        cmd += ['-i', node_id]
        cmd += ['-cli']
        cmd += ['-log', os.path.join(node_folder, 'log')]
        cmd += ['-v']
        print('cmd', cmd)
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        return p, latus_folder

    proc_a, folder_a = start_one('a')
    file_a = 'a.txt'
    time.sleep(5)  # ensure an order
    proc_b, folder_b = start_one('b')
    file_b = 'b.txt'

    write_one(folder_a, file_a, 'a')
    write_one(folder_b, file_b, 'b')

    sleep_time = 0.1
    time_out = 10 / sleep_time

    time_out_count_down = time_out
    while not os.path.exists(os.path.join(folder_a, file_b)) and time_out_count_down:
        time.sleep(sleep_time)
        time_out_count_down -= 1
    assert(time_out_count_down > 0)

    time_out_count_down = time_out
    while not os.path.exists(os.path.join(folder_b, file_a)) and time_out_count_down:
        time.sleep(sleep_time)
        time_out_count_down -= 1
    assert(time_out_count_down > 0)

    # doesn't seem to work:
    #proc_a.communicate('q\n')
    #proc_b.communicate('q\n')

    # use this instead:
    proc_a.terminate()
    proc_b.terminate()

    print('multi exiting')

