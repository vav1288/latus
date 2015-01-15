
import os
import time
import subprocess

import latus.util
import test_latus


def start_one(node_id, test_name):
    write_folder = os.path.join(test_latus.create_files.get_sync_root(), test_name)
    node_folder = os.path.join(write_folder, node_id)
    latus.util.make_dirs(node_folder)
    latus_folder = os.path.join(node_folder, 'latus')
    python_exe = os.path.join('c:', '/', 'python34', 'python.exe')
    print('python_exe', python_exe)
    cmd = [python_exe, 'latus.py']
    cmd += ['-l', latus_folder]
    # all nodes use same folder to emulate cloud sync
    cmd += ['-c', os.path.join(write_folder, 'dropbox')]
    cmd += ['-a', os.path.join(node_folder, 'appdata')]
    cmd += ['-k', 'dQf6js1s-CcVRQMnt6t4w7fOdVJAzqhvcQNsHnvuQNQ=']
    cmd += ['-i', node_id]
    cmd += ['-cli']
    cmd += ['-log', os.path.join(node_folder, 'log')]
    cmd += ['-v']
    print('cmd', cmd)
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    return p, latus_folder


def write_one(folder, file_name, s):
    if not os.path.exists(folder):
        os.mkdir(folder)
    with open(os.path.join(folder, file_name), 'w') as f:
        f.write(s)


def wait_for_file(file_path):
    time_out_sec = 10
    sleep_time_sec = 0.1
    time_out_count_down = time_out_sec / sleep_time_sec

    while not os.path.exists(file_path) and time_out_count_down:
        time.sleep(sleep_time_sec)
        time_out_count_down -= 1
    return time_out_count_down > 0
