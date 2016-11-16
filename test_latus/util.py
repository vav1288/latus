
import os
import time
import logging
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
    latus.logger.log.info('logger_init')


# get an mtime back in time
def get_mtime_time():
    return time.mktime(time.strptime("12", "%y"))


def make_dirs(p):
    if not os.path.exists(p):
        os.makedirs(p)


def get_python_exe():
    if latus.util.is_windows():
        bin_folder = 'Scripts'
    else:
        bin_folder = 'bin'
    return os.path.join('venv', bin_folder, 'python')


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
    cmd += ['--config', appdata_folder]
    cmd += ['-k', 'dQf6js1s-CcVRQMnt6t4w7fOdVJAzqhvcQNsHnvuQNQ=']
    cmd += ['-n', node_id]
    cmd += ['-cli']
    cmd += ['-log', log_folder]
    cmd += ['-v']
    print('cmd', cmd)
    latus_process = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    return latus_process, latus_folder, log_folder


# waits for a file to exist
# set "to_exist" parameter to False if you want to wait until the file does NOT exist
def wait_for_file(file_path, to_exist=True):
    time_out_sec = 20
    sleep_time_sec = 0.1
    time_out_count_down = time_out_sec / sleep_time_sec

    if to_exist:
        message = ''
    else:
        message = ' not'

    while (to_exist ^ os.path.exists(file_path)) and time_out_count_down > 0:
        time.sleep(sleep_time_sec)
        time_out_count_down -= 1
    if time_out_count_down <= 0:
        print('timeout waiting for %s to%s exist' % (file_path, message))
        return False
    return True


def get_app_data_folder(root):
    return os.path.join(root, 'appdata')


def sync_node(setup_id, key, root, cloud, sub_folder, exit_event, write_flag=True, data_sub_folder=None):
    logger_init(os.path.join(root, 'log'))
    _sync_node = SetupSyncNode(setup_id, key, root, cloud, sub_folder)
    if write_flag:
        write_to_file(_sync_node.get_file_dir(), _sync_node.get_file_name(), setup_id, data_sub_folder)
    _sync_node.get_sync().start()
    while not exit_event.is_set():
        time.sleep(2)
        _sync_node.get_sync().poll()  # the real app would have to periodically poll
    _sync_node.get_sync().request_exit()


def get_latus_folder(root, node_id):
    node_folder = os.path.join(root, node_id)  # give us our own folder
    latus_folder = os.path.join(node_folder, 'latus')
    return latus_folder


def get_file_name(node_id):
    return node_id + '.txt'


class SetupSyncNode:
    def __init__(self, node_id, key, root, cloud, sub_folder):
        self.root = root
        self.sub_folder = sub_folder
        self.node_id = node_id
        node_folder = os.path.join(root, self.node_id)  # give us our own folder
        self.app_data_folder = get_app_data_folder(node_folder)
        self.cloud_root = cloud
        pref = latus.preferences.Preferences(self.app_data_folder, True)
        pref.set_cloud_root(self.cloud_root)
        pref.set_latus_folder(get_latus_folder(root, node_id))
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

    def get_file_path(self):
        latus_folder = get_latus_folder(self.root, self.node_id)
        if self.sub_folder:
            p = os.path.join(latus_folder, self.sub_folder, get_file_name(self.node_id))
        else:
            p = os.path.join(latus_folder, get_file_name(self.node_id))
        return p

    def get_file_dir(self):
        return os.path.dirname(self.get_file_path())

    def get_file_name(self):
        return get_file_name(self.node_id)

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


def write_to_file(dir_path, file_name, contents, subdir=None):
    if subdir:
        p = os.path.join(dir_path, subdir, file_name)
    else:
        p = os.path.join(dir_path, file_name)
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