
import os
import shutil
import time
import sys

from PySide import *

import latus.gui_wizard
import latus.util
import latus.logger
import latus.preferences
import latus.sync
import latus.key_management
import latus.folders

import test_latus.create_files
import test_latus.paths


def get_gui_wizard_root():
    return os.path.join(test_latus.paths.get_data_root(), "gui_wizard")


def get_folders(node):
    node_folder = os.path.join(get_gui_wizard_root(), node)
    return {'app_data': os.path.join(node_folder, 'app_data'), 'cloud': os.path.join(get_gui_wizard_root(), 'cloud')}


def run_one(node_id):

    folders = get_folders(node_id)
    latus.logger.log.info('test_gui_wizard : start')

    app = QtGui.QApplication([])
    # ignore the cloud folder from the GUI - force the cloud folder to this test area
    app_gui_wizard = latus.gui_wizard.GUIWizard(folders['app_data'], folders['cloud'])
    app_gui_wizard.exec_()

if __name__ == '__main__':
    if os.path.exists(get_gui_wizard_root()):
        shutil.rmtree(get_gui_wizard_root())

    latus.logger.init(os.path.join(os.path.join(get_gui_wizard_root(), 'log')))

    test_nodes = ['a', 'b']  # test folder names (not the actual node IDs)
    syncs = {}
    pref = {}
    for test_node in test_nodes:
        this_node_folders = get_folders(test_node)
        run_one(test_node)
        pref[test_node] = latus.preferences.Preferences(this_node_folders['app_data'])
        pref[test_node].set_cloud_root(this_node_folders['cloud'])  # for testing
        syncs[test_node] = latus.sync.Sync(this_node_folders['app_data'], False, True)  # creates the node DBs
        syncs[test_node].start()
        time.sleep(5)  # sleep long enough to make the node DBs

    b_folders = get_folders('b')
    b_cloud_folders = latus.folders.CloudFolders(b_folders['cloud'])
    latus_key = latus.key_management.get_latus_key(pref['b'].get_node_id(), b_cloud_folders.keys,
                                                   pref['b'].get_private_key())
    pref['b'].set_crypto_key(latus_key)

    for test_node in test_nodes:
        latus.logger.log.info('%s : latus key : %s' % (test_node, pref[test_node].get_crypto_key()))

    is_ok = (pref['a'].get_crypto_key() == pref['b'].get_crypto_key())
    assert is_ok

    for test_node in test_nodes:
        syncs[test_node].request_exit()

    # unfortunately this doesn't really work, since automa doesn't look at the return code :(
    # todo: write a file with the pass/fail that the caller from py.test can read and assert on
    if is_ok:
        sys.exit(0)
    else:
        sys.exit(1)