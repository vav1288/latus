import os
import time
import subprocess
import test_latus.create_files


def get_cli_root():
    return os.path.join(test_latus.create_files.get_data_root(), "cli")


def test_sync_cli_invocation(setup):
    """
    Just test that the CLI version can be run at all.
    """
    sync_folder = os.path.join(get_cli_root(), 'a')
    python_exe = os.path.join('c:', '/', 'python34', 'python.exe')
    print('python_exe', python_exe)
    cmd = [python_exe, 'latus.py']
    cmd += ['-l', os.path.join(sync_folder, 'latus')]
    cmd += ['-c', os.path.join(sync_folder, 'dropbox')]
    cmd += ['-a', os.path.join(sync_folder, 'appdata')]
    cmd += ['-k', 'dQf6js1s-CcVRQMnt6t4w7fOdVJAzqhvcQNsHnvuQNQ=']
    cmd += ['-n', 'x']
    cmd += ['-cli']
    cmd += ['-v']
    print('cmd', cmd)
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    # this is a kludge - I really want to test that the program ran and then send a CR to it to stop
    time.sleep(10) # long enough for the program to run
    p.terminate()
    # p.communicate('q\n') # didn't work ...
    time.sleep(5)  # give it time to fully terminate
