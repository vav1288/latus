
import os
import time
import subprocess

import latus.util
import test_latus.create_files


def start_one(node_id, test_name):
    test_folder = os.path.join(test_latus.create_files.get_data_root(), test_name)
    node_folder = os.path.join(test_folder, node_id)
    latus.util.make_dirs(node_folder)
    latus_folder = os.path.join(node_folder, 'latus')
    cloud_folder = os.path.join(test_folder, 'dropbox')  # all nodes use the same cloud folder to emulate cloud sync
    appdata_folder = os.path.join(node_folder, 'appdata')
    log_folder = os.path.join(node_folder, 'log')
    python_exe = os.path.join('c:', '/', 'python34', 'python.exe')
    #print('python_exe', python_exe)
    cmd = [python_exe, 'latus.py']
    cmd += ['-l', latus_folder]
    # all nodes use same folder to emulate cloud sync
    cmd += ['-c', cloud_folder]
    cmd += ['-a', appdata_folder]
    cmd += ['-k', 'dQf6js1s-CcVRQMnt6t4w7fOdVJAzqhvcQNsHnvuQNQ=']
    cmd += ['-i', node_id]
    cmd += ['-cli']
    cmd += ['-log', log_folder]
    cmd += ['-v']
    print('cmd', cmd)
    latus_process = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    return latus_process, latus_folder, log_folder


def wait_for_file(file_path):
    time_out_sec = 10
    sleep_time_sec = 0.1
    time_out_count_down = time_out_sec / sleep_time_sec

    while not os.path.exists(file_path) and time_out_count_down:
        time.sleep(sleep_time_sec)
        time_out_count_down -= 1
    return time_out_count_down > 0
