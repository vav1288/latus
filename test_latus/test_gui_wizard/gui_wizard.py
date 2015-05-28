
import os
import shutil
import time

from PyQt5 import QtWidgets, QtCore

import latus.gui_wizard
import latus.util
import latus.logger
import latus.preferences
import latus.sync

import test_latus.create_files
import test_latus.paths

def get_gui_wizard_root():
    return os.path.join(test_latus.paths.get_data_root(), "gui_wizard")


def get_folders(node_id):
    node_folder = os.path.join(get_gui_wizard_root(), node_id)
    return {'app_data': os.path.join(node_folder, 'app_data'), 'log': os.path.join(node_folder, 'log'),
            'cloud': os.path.join(get_gui_wizard_root(), 'cloud')}


def run_one(node_id):

    folders = get_folders(node_id)
    latus.util.make_dirs(folders['log'])
    latus.logger.init(folders['log'])

    latus.logger.log.info('test_gui_wizard : start')

    app = QtWidgets.QApplication([])
    # ignore the cloud folder from the GUI - force the cloud folder to this test area
    app_gui_wizard = latus.gui_wizard.GUIWizard(folders['app_data'], folders['cloud'])
    app_gui_wizard.exec_()

if __name__ == '__main__':
    if os.path.exists(get_gui_wizard_root()):
        shutil.rmtree(get_gui_wizard_root())

    for this_node_id in ['a', 'b']:
        this_node_folders = get_folders(this_node_id)
        run_one(this_node_id)
        pref = latus.preferences.Preferences(this_node_folders['app_data'])
        pref.set_cloud_root(this_node_folders['cloud'])  # for testing
        key_management = latus.sync.Sync(this_node_folders['app_data'], False, True)
        key_management.start()
        time.sleep(5)  # make node DBs
        key_management.request_exit()


