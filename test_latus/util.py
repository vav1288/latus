
import os
import time
import logging
import json
import subprocess
import shutil

import latus.logger
import latus.util
import latus.crypto
import latus.preferences
import latus.sync
import latus.nodedb
import latus.folders

SRC = "src"
DEST = "dest"
DEST_EMPTY = "dest_empty"
DEST_EXISTS_EXACT = "dest_exists_exact"
DEST_EXISTS_DIFFERENT = "dest_exists_different"
DEST_EXISTS_UNDER_DIFFERENT_NAME = "dest_exists_under_different_name"
DEST_BEST = "dest_best"
DEST_CONFLICT = "dest_conflict"

A_STRING = "a"
B_STRING = "b"
C_STRING = "c"
A_FILE_NAME = "a.txt"
B_FILE_NAME = "b.txt"
C_FILE_NAME = "c.txt"

# something to give good unicode coverage ...
UNICODE_FILE_NAME_LENGTH = 63
SMALL_MAX_CODE = 512
BIG_MAX_CODE = 8192

y_folder_files = None


def logger_init(log_folder):
    if latus.logger.log:
        print('WARNING: logger already set up')
    else:
        latus.logger.init(log_folder)
    latus.logger.set_console_log_level(logging.INFO)
    latus.logger.set_file_log_level(logging.DEBUG)


# get an mtime back in time
def get_mtime_time():
    return time.mktime(time.strptime("12", "%y"))


def make_dirs(p):
    if not os.path.exists(p):
        os.makedirs(p)


def wait_on_nodes(log_folders_param):
    for log_folder in log_folders_param:
        wait_for_node(log_folder)


def wait_for_node(log_folder):
    # wait for this node to settle down and cease all activity
    # returns True if stability found, False if we merely timed out and gave up

    sleep_time = 0.5  # sec
    time_out = 600/sleep_time  # sec to timeout
    stable_time = 5/sleep_time  # number of seconds we need to see stable files to declare it stable
    time_out_count = time_out
    stable_count = stable_time
    unstable_file = None

    status = []
    log_files = ['cloud.log', 'local.log']
    prior_status = {}
    for log_file in log_files:
        prior_status[log_file] = None
    while stable_count > 0 and time_out_count > 0:
        stable_flag = True
        for log_file in log_files:
            file_path = os.path.join(log_folder, log_file)
            if os.path.exists(file_path):
                with open(file_path) as json_file:
                    try:
                        status = json.load(json_file)
                    except ValueError:
                        stable_flag = False
                    if prior_status[log_file]:
                        #print('status', status)
                        if status['count'] != prior_status[log_file]['count']:
                            latus.logger.log.debug('%s not yet stable %s : %s' % (file_path, status, prior_status[log_file]))
                            stable_flag = False
                            unstable_file = file_path
                    else:
                        stable_flag = False
                    prior_status[log_file] = status
            else:
                stable_flag = False
        #print('stable_flag', stable_flag)
        if stable_flag:
            stable_count -= 1
        else:
            stable_count = stable_time
        time_out_count -= 1
        time.sleep(0.1)
    if time_out_count <= 0:
        latus.logger.log.warn('timeout : %s' % unstable_file)
    return time_out_count > 0


def get_python_exe():
    return os.path.join('venv', 'Scripts', 'python.exe')

def start_cmd_line(node_id, test_name):
    test_folder = os.path.join(get_data_root(), test_name)
    node_folder = os.path.join(test_folder, node_id)
    latus.util.make_dirs(node_folder)
    latus_folder = os.path.join(node_folder, 'latus')
    cloud_folder = os.path.join(test_folder, 'cloud')  # all nodes use the same cloud folder to emulate cloud sync
    appdata_folder = os.path.join(node_folder, 'appdata')
    log_folder = os.path.join(node_folder, 'log')
    python_exe = get_python_exe()
    #print('python_exe', python_exe)
    cmd = [python_exe, 'main.py']
    cmd += ['-l', latus_folder]
    # all nodes use same folder to emulate cloud sync
    cmd += ['-c', cloud_folder]
    cmd += ['-a', appdata_folder]
    cmd += ['-k', 'dQf6js1s-CcVRQMnt6t4w7fOdVJAzqhvcQNsHnvuQNQ=']
    cmd += ['-n', node_id]
    cmd += ['-cli']
    cmd += ['-log', log_folder]
    cmd += ['-v']
    print('cmd', cmd)
    latus_process = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    return latus_process, latus_folder, log_folder


def wait_for_file(file_path):
    time_out_sec = 60
    sleep_time_sec = 0.1
    time_out_count_down = time_out_sec / sleep_time_sec

    while not os.path.exists(file_path) and time_out_count_down:
        time.sleep(sleep_time_sec)
        time_out_count_down -= 1
    return time_out_count_down > 0


def get_app_data_folder(root):
    return os.path.join(root, 'appdata')


class SetupSyncNode:
    def __init__(self, setup_id, key, root, cloud, sub_folder=None):
        self.sub_folder = sub_folder
        self.node_id = setup_id
        node_folder = os.path.join(root, self.node_id)  # give us our own folder
        self.app_data_folder = get_app_data_folder(node_folder)
        self.latus_folder = os.path.join(node_folder, 'latus')
        self.cloud_root = cloud
        pref = latus.preferences.Preferences(self.app_data_folder, True)
        pref.set_cloud_root(self.cloud_root)
        pref.set_latus_folder(self.latus_folder)
        pref.set_node_id(self.node_id)
        pref.set_crypto_key(key)
        pref.set_verbose(True)
        self.sync = latus.sync.Sync(self.app_data_folder)

    def get_sync(self):
        return self.sync

    def get_app_data_folder(self):
        return self.app_data_folder

    def get_preferences(self):
        return latus.preferences.Preferences(self.app_data_folder)

    def get_file_name(self):
        return self.node_id + '.txt'

    def get_file_path(self):
        if self.sub_folder:
            p = os.path.join(self.latus_folder, self.sub_folder, self.get_file_name())
        else:
            p = os.path.join(self.latus_folder, self.get_file_name())
        return p

    def get_latus_folder(self):
        return self.latus_folder

    def get_cloud_root(self):
        return self.cloud_root

    def set_folder_preferences(self, encrypt, shared, cloud):
        if self.sub_folder:
            pref = latus.preferences.Preferences(self.app_data_folder)
            folders = latus.folders.CloudFolders(pref.get_cloud_root())
            node_db = latus.nodedb.NodeDB(folders.nodes, pref.get_node_id(), True)
            node_db.set_folder_preferences(self.sub_folder, encrypt, shared, cloud)


def clean():
    """
    clean up the test data
    :return:
    """
    path = get_data_root()
    try_count = 10
    while os.path.exists(path) and try_count:
        try:
            shutil.rmtree(path)
        except PermissionError as e:
            # log isn't set up yet, so just print
            print('can not rmtree %s - retrying' % path)
            print(str(e))
            time.sleep(1)
            try_count -= 1
    assert(try_count > 0)
    if try_count == 0:
        exit('clean failed')


def write_to_file(p, contents):
    make_dirs(os.path.dirname(p))
    with open(p, "w") as f:
        f.write(contents)
        f.close()


sha512 = {
    'a' : "1f40fc92da241694750979ee6cf582f2d5d7d28e18335de05abc54d0560e0f5302860c652bf08d560252aa5e74210546f369fbbbce8c12cfc7957b2652fe9a75"
}


def get_data_root():
    return os.path.abspath(os.path.join('test_latus', 'data'))


def root_test_gui_wizard():
    return os.path.join('test_latus', 'test_gui_wizard')