
import os
import shutil
import win32event
import subprocess
import time
import core.const
import core.sync
import core.metadatapath
import test.create_files
from test.conftest import setup

def emulate_cloud_sync(a, b):
    # one direction ...
    for r, _, fs in os.walk(a):
        for f in fs:
            src = os.path.join(r, f)
            # a kludge, but works for this particular case
            dest = src.replace('\\a\\', '\\b\\')
            if not os.path.exists(dest):
                d = os.path.split(dest)[0]
                if not os.path.exists(d):
                    os.makedirs(d)
                shutil.copyfile(src, dest)
    # now the other direction ...
    for r, _, fs in os.walk(b):
        for f in fs:
            src = os.path.join(r, f)
            dest = src.replace('\\b\\', '\\a\\')
            if not os.path.exists(dest):
                d = os.path.split(dest)[0]
                if not os.path.exists(d):
                    os.makedirs(d)
                shutil.copyfile(src, dest)

def test_sync_simple(setup):
    """
    test a simple sync of 2 files across 2 nodes
    """
    sync_nodes_test_info = test.create_files.SyncNodesTestInfo()
    sync = {}

    # get the cloud folders
    nodes = sync_nodes_test_info.nodes
    cloud_folder_0 = sync_nodes_test_info.get_cloud_folder(nodes[0])
    cloud_folder_1 = sync_nodes_test_info.get_cloud_folder(nodes[1])

    exit_event = win32event.CreateEvent(None, 0, 0, None)

    for node in sync_nodes_test_info.nodes:
        sync[node] = core.sync.Sync('xyzzy', sync_nodes_test_info.get_local_folder(node),
                                    sync_nodes_test_info.get_cloud_folder(node), verbose=True)
        sync[node].sync()

        # do what the cloud service sync would normally do
        emulate_cloud_sync(cloud_folder_0, cloud_folder_1)

    for node in sync_nodes_test_info.nodes:
        sync[node].sync()

    for node in sync_nodes_test_info.nodes:
        # shutil.rmtree(os.path.join(sync_nodes.get_cloud_folder(node))) # remove what sync creates
        pass

    local_folders = []
    file_names = []
    for node in sync_nodes_test_info.nodes:
        local_folders.append(sync_nodes_test_info.get_local_folder(node))
        file_names.append(sync_nodes_test_info.get_file_name(node))
    b_to_a = os.path.join(local_folders[0], file_names[1])
    print('b_to_a', b_to_a)
    assert(os.path.exists(b_to_a))
    a_to_b = os.path.join(local_folders[1], file_names[0])
    print('a_to_b', a_to_b)
    assert(os.path.exists(a_to_b))
    return

def test_sync_cli_invocation(setup):
    """
    Just test that the CLI version can be run at all.
    """
    sync_folder = os.path.join('test', 'data', 'files', 'sync', 'a')
    python_exe = os.path.join('c:', '/', 'python33', 'python.exe')
    print('python_exe', python_exe)
    cmd = [python_exe, 'sync.py']
    cmd += ['-p',  'xyzzy']
    cmd += ['-l', os.path.join(sync_folder, 'latus')]
    cmd += ['-c', os.path.join(sync_folder, 'dropbox')]
    cmd += ['-v']
    print('cmd', cmd)
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    # this is a kludge - I really want to test that the program ran and then send a CR to it to stop
    time.sleep(10) # long enough for the program to run
    p.terminate()
    # p.communicate('OK\n') # didn't work ...
