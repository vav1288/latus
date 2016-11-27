
import os
import logging
import time
import threading
import random
import shutil
import argparse
import appdirs

from PyQt5.QtWidgets import QApplication, QPushButton, QWidget

import latus.logger
import latus.sync
import latus.preferences
import latus.crypto
import latus.gui
import latus.const
from test_latus.tstutil import SyncProc

import test_latus.tstutil
import test_latus.read_logs

# todo: Don't pollute the normal log file with these logs (but you'll have to change both this code and the
#       processes of the latus sync nodes).

class FilesTest(threading.Thread):
    """
    thread that does all the testing
    """
    def __init__(self, app_data_folders, latus_folders, syncs):
        super().__init__()
        self.app_data_folders = app_data_folders
        self.latus_folders = latus_folders
        self.syncs = syncs
        [os.makedirs(d, exist_ok=True) for d in self.latus_folders]
        self.run_latus_test = True
        self.exit_event = threading.Event()
        self.file_count = 0
        # the test latus processes use the default log path
        self.log_file_path = os.path.join(appdirs.user_log_dir(latus.const.NAME, latus.const.COMPANY), latus.const.LOG_FILE)
        os.remove(self.log_file_path)

    def run(self):
        # create appears twice so we give more weight to file creation (else we'd not have a lot of files)
        actions = [self.file_create, self.file_create, self.file_modify, self.file_delete, self.file_move]
        while not self.exit_event.is_set():
            # keep trying until one of the actions actually does something
            while not random.choice(actions)():
                pass

            latus.logger.log.info('waiting for nodes to become inactive')
            time.sleep(2)

            timeout = 0
            # read the log file the nodes are using
            while test_latus.read_logs.is_active(self.log_file_path) and timeout < 10*60:
                latus.logger.log.info(test_latus.read_logs.get_activity_states(self.log_file_path))
                time.sleep(2)
                timeout += 1
            latus.logger.log.info(test_latus.read_logs.get_activity_states(self.log_file_path))
            test_latus.tstutil.compare_folders(self.latus_folders)

        latus.logger.log.info('exiting test')

    def file_create(self):
        file_path = self.next_file_path()
        latus.logger.log.info('file_create : %s' % file_path)
        with open(file_path, 'w') as f:
            f.write('%s\n' % file_path)  # merely write the file path in the file itself
        return True

    def file_modify(self):
        file_path, dir = self.get_existing_file_path()
        if file_path:
            latus.logger.log.info('file_modify : %s' % file_path)
            with open(file_path, 'a') as f:
                f.write('%s\n' % str(time.time()))
            return True
        else:
            latus.logger.log.info('can not do file_modify yet at %s - no files exist' % dir)
            return False

    def file_delete(self):
        file_path, d = self.get_existing_file_path()
        if file_path:
            latus.logger.log.info('file_delete : %s' % file_path)
            os.remove(file_path)
            return True
        else:
            latus.logger.log.info('can not do file_delete yet at %s - no files exist' % d)
            return False

    def file_move(self):
        file_path, dir = self.get_existing_file_path()
        new_path = self.next_file_path(dir)  # moves are within a node's folder (not cross-node)
        if file_path:
            # if there is no existing file, then don't do anything
            latus.logger.log.info('file_move : %s to %s' % (file_path, new_path))
            shutil.move(file_path, new_path)
            return True
        else:
            latus.logger.log.info('can not do file_move yet at %s - no files exist' % dir)
            return False

    def next_file_path(self, d=None):
        # for move, allow the caller to provide the folder
        if not d:
            d = random.choice(self.latus_folders)
        path = os.path.join(d, 't' + hex(self.file_count) + '.txt')
        self.file_count += 1
        # latus.logger.log.info('next_file_path : %s' % path)
        return path

    def get_existing_file_path(self):
        # todo: do subdirs
        d = random.choice(self.latus_folders)
        files = os.listdir(d)
        if len(files) == 0:
            return None, d
        path = os.path.join(d, random.choice(files))
        while os.path.isdir(path):
            path = os.path.join(d, random.choice(files))
        # latus.logger.log.info('existing file : %s' % path)
        return path, d

    def request_exit(self):
        latus.logger.log.info('exit requested')
        self.exit_event.set()


def setup_preferences(data_root, number_of_nodes):
    """
    set up all the preferences (the preferences DBs) for the test nodes
    :param data_root: folder to use for the test folders
    :param number_of_nodes: number of nodes to use in this test
    :return:
    """
    first_node_name = 'a'
    latus_key = latus.crypto.new_key()
    node_names = [chr(c) for c in range(ord(first_node_name), ord(first_node_name) + number_of_nodes)]
    app_data_folders = [test_latus.tstutil.write_preferences(node_name, data_root, latus_key) for node_name in node_names]
    return app_data_folders


class UIWindow(QWidget):
    """
    The user interface window
    """
    def __init__(self):
        super().__init__()
        w = 300
        h = 100
        qbtn = QPushButton('Stop', self)
        qbtn.clicked.connect(QApplication.instance().quit)
        qbtn.move(w/2, h/2)
        self.setMinimumSize(w, h)
        self.setWindowTitle('Latus System Test is Running')
        self.show()


def user_interface():
    """
    THe user interace 'app'
    :return:
    """
    app = QApplication([])
    ui = UIWindow()
    app.exec()


def main():
    """
    main test function
    """

    number_of_nodes = 3

    parser = argparse.ArgumentParser(description='latus system test')
    parser.add_argument('-n', '--no_sync', action='store_true', default=False, help="don't do sync (for testing)")
    args = parser.parse_args()

    # set up test folder and logging
    test_root = os.path.join('temp', 'systst')
    shutil.rmtree(test_root)
    latus.logger.init(delete_existing_log_files=True)
    latus.logger.set_console_log_level(logging.INFO)

    # set up the preferences for the nodes we'll run
    app_data_folders = setup_preferences(test_root, number_of_nodes)
    latus_folders = []
    for app_data_folder in app_data_folders:
        pref = latus.preferences.Preferences(app_data_folder)
        latus_folders.append(pref.get_latus_folder())

    # create the nodes and start them
    syncs = []
    if not args.no_sync:
        # start the sync
        syncs = [SyncProc(app_data_folder) for app_data_folder in app_data_folders]
        [sync.start() for sync in syncs]

    # do the tests (and provide the user with a "Stop" button)
    files_test = FilesTest(app_data_folders, latus_folders, syncs)
    files_test.start()
    user_interface()
    files_test.request_exit()
    files_test.join()
    if not args.no_sync:
        [sync.request_exit() for sync in syncs]

if __name__ == '__main__':
    main()
