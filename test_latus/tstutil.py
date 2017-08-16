
import os
import time
import logging
import shutil
import sys
import subprocess
import filecmp
import json

import latus.logger
import latus.util
import latus.crypto
import latus.preferences
import latus.const

def get_data_root():
    return os.path.abspath(os.path.join('test_latus', 'data'))

AWS_LOCAL_CONFIG_FILE_PATH = os.path.join('temp', 'aws_local_config.json')


def set_cloud_config(cloud_mode, aws_local=True):
    os.makedirs(os.path.dirname(AWS_LOCAL_CONFIG_FILE_PATH), exist_ok=True)
    with open(AWS_LOCAL_CONFIG_FILE_PATH, 'w') as f:
        json.dump({'cloud_mode': cloud_mode, 'aws_local': bool(aws_local)}, f, indent=4)


def get_cloud_config():
    info = {'cloud_mode': 'aws', 'aws_local': False}  # defaults
    if os.path.exists(AWS_LOCAL_CONFIG_FILE_PATH):
        with open(AWS_LOCAL_CONFIG_FILE_PATH) as f:
            try:
                info = json.load(f)
            except json.decoder.JSONDecodeError:
                pass
    return info


def logger_init(log_folder):
    if latus.logger.log:
        latus.logger.log.info('logger already set up at %s (will NOT change to %s)' %
                              (latus.logger.get_base_log_file_path(), log_folder))
        return
    latus.logger.init(log_folder)
    latus.logger.set_console_log_level(logging.INFO)
    latus.logger.set_file_log_level(logging.DEBUG)
    latus.logger.log.info('logger_init')


def get_python_exe():
    if latus.util.is_windows():
        bin_folder = 'Scripts'
    else:
        bin_folder = 'bin'
    return os.path.join('venv', bin_folder, 'python')


# waits for a file to exist
# set "to_exist" parameter to False if you want to wait until the file does NOT exist
def wait_for_file(file_path, to_exist=True, message_prefix=''):
    time_out_sec = 30
    sleep_time_sec = 3
    time_out_count_down = int(round(time_out_sec / sleep_time_sec))

    if to_exist:
        exist_polarity = ''
    else:
        exist_polarity = ' not'

    while (to_exist ^ os.path.exists(file_path)) and time_out_count_down > 0:
        latus.logger.log.info('%s waiting for %s to%s exist' % (message_prefix, file_path, exist_polarity))
        time.sleep(sleep_time_sec)
        time_out_count_down -= 1
    if time_out_count_down <= 0:
        latus.logger.log.warn('%s timeout waiting for %s to%s exist' % (message_prefix, file_path, exist_polarity))
        return False
    return True


def write_preferences(node_id, data_root, latus_key):
    """
    :param node_id: name of this node
    :param data_root: folder this test is using for all its data
    :param latus_key: the (shared) latus crypto key
    :return: folder where the preferences file resides
    """
    app_data_folder = get_app_data_folder(data_root, node_id)
    pref = latus.preferences.Preferences(app_data_folder, True)
    pref.set_node_id(node_id)
    # this folder is shared across all the nodes to emulate cloud sync
    pref.set_cloud_root(os.path.join(data_root, 'cloud'))
    pref.set_latus_folder(get_latus_folder(data_root, node_id))
    pref.set_crypto_key(latus_key)
    cloud_config = get_cloud_config()
    pref.set_cloud_mode(cloud_config['cloud_mode'])
    pref.set_aws_local(cloud_config['aws_local'])
    pref.set_aws_location('us-west-1')
    return app_data_folder


def get_latus_folder(root, node_id):
    return os.path.join(root, node_id, 'latus')  # give us our own folder


def get_app_data_folder(root, node_id):
    return os.path.join(root, node_id, 'appdata')  # give us our own folder


def get_file_name(node_id):
    return node_id + '.txt'


class SyncProc:
    """
    Run the sync in a separate process.  This is necessary since the watchdog module and/or the
    underlying OS doesn't work well if there are multiple watchers watching the same path in the same process
    (i.e. we can't merely start multiple syncs in the test process - we have to create multiple separate processes).
    """
    def __init__(self, app_data_folder, log_folder):
        self.app_data_folder = app_data_folder
        self.sync_process = None

        if latus.util.is_mac():
            exec_path = os.path.join('venv', 'bin', 'coverage') + ' run -a'
        else:
            exec_path = sys.executable

        sync_py_path = os.path.join('latus', 'sync.py')
        # may want to put in -v
        self.cmd = '%s %s -a %s -t -l %s' % (exec_path, sync_py_path, self.app_data_folder, log_folder)
        cc = get_cloud_config()
        if cc['aws_local']:
            self.cmd += ' --localstack'

    def start(self):
        latus.logger.log.info(self.cmd)
        self.sync_process = subprocess.Popen(self.cmd, shell=True, stdin=subprocess.PIPE)

    def request_exit(self, time_out=latus.const.TIME_OUT):
        self.sync_process.communicate(b'\n\r')  # emulate 'enter' key to shutdown (one of these should do it)
        self.sync_process.wait(time_out)  # if there are no issues shutdown should take just a few seconds
        rc = self.sync_process.poll()
        if rc != 0:
            latus.logger.log.error('%s returned %s' % (self.cmd, str(rc)))
        return rc


def clean(path=get_data_root(), delete_coverage=True):
    """
    clean up the test data
    :return:
    """
    try_count = 100
    while os.path.exists(path) and try_count:
        try:
            shutil.rmtree(path)
        except PermissionError as e:
            # log isn't set up yet, so just print
            print('can not rmtree %s - retrying' % path)
            print(str(e))
            time.sleep(0.2)
            try_count -= 1
    assert(try_count > 0)
    if try_count == 0:
        exit('clean failed')
    if delete_coverage:
        try:
            print('deleting .coverage')
            os.remove('.coverage')
        except FileNotFoundError:
            pass


def write_to_file(dir_path, file_name, contents, subdir=None, mode='w'):
    if subdir:
        p = os.path.join(dir_path, subdir, file_name)
    else:
        p = os.path.join(dir_path, file_name)
    try:
        os.makedirs(os.path.dirname(p), mode=latus.const.MAKE_DIRS_MODE, exist_ok=True)
    except PermissionError as e:
        latus.logger.log.error('%s : %s (%s)' % (str(e), dir_path, os.path.abspath(dir_path)))

    latus.logger.log.info('writing %s' % p)
    with open(p, mode) as f:
        f.write(contents)
        f.close()
    return p


def compare_folders(folder_paths):
    """
    compare a list of folder paths
    print errors if they exist
    :param folder_paths: list of folder paths
    :return: True if all compare, False if there are differences or there are errors
    """
    all_compare_ok = False
    attempt_count_down = 10
    latus.logger.log.debug('comparing %s' % str(folder_paths))
    mismatch = None
    errors = None
    while not all_compare_ok and attempt_count_down > 0:
        error_a, error_b = None, None
        for folder_a in folder_paths:
            for folder_b in folder_paths:
                if folder_a != folder_b:
                    # both dirs should have the same files
                    common_files = set(os.listdir(folder_a)).union(set(os.listdir(folder_b)))
                    latus.logger.log.debug('comparing %s to %s' % (folder_a, folder_b))
                    match, mismatch, errors = filecmp.cmpfiles(folder_a, folder_b, common_files)
                    if len(mismatch) > 0 or len(errors) > 0:
                        all_compare_ok = False
                        error_a, error_b = folder_a, folder_b
                    else:
                        all_compare_ok = True
        if not all_compare_ok:
            time.sleep(1)
            latus.logger.log.warn('compare_folders issue - retrying : countdown=%d : folders=%s,%s : mismatch=%s : errors=%s' %
                                  (attempt_count_down, error_a, error_b, str(mismatch), str(errors)))
        attempt_count_down -= 1
    if attempt_count_down < 1:
        latus.logger.log.error('comparing %s' % str(folder_paths))
        s = 'compare folders error : mismatch=%s : errors=%s' % (str(mismatch), str(errors))
        print(s)
        latus.logger.log.fatal(s)
    if all_compare_ok:
        latus.logger.log.info('%d files compare OK : %s' % (len(os.listdir(folder_paths[0])), str(folder_paths)))
    return all_compare_ok


def root_test_gui_wizard():
    return os.path.join('test_latus', 'test_gui_wizard')

