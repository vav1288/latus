
from PyQt5 import QtWidgets, QtCore

import latus.key_management
import latus.logger


class AllowButton(QtWidgets.QPushButton):
    def __init__(self, latus_app_data_folder, requester):
        self.requester = requester
        self.latus_app_data_folder = latus_app_data_folder
        super().__init__('Allow')
        self.clicked.connect(self.allow)

    def allow(self):
        latus.logger.log.info('allowing %s' % self.requester)
        km = latus.key_management.KeyManagement(self.latus_app_data_folder)
        km.respond_to_request(self.requester)


class ManagementDialog(QtWidgets.QDialog):
    def __init__(self, latus_app_data_folder):
        latus.logger.log.info('starting ManagementDialog')
        super().__init__()
        km = latus.key_management.KeyManagement(latus_app_data_folder)
        grid_layout = QtWidgets.QGridLayout()
        lines = {}
        buttons = {}
        row = 0
        for requester in km.get_requesters():
            lines[requester] = QtWidgets.QLineEdit(requester)
            lines[requester].setReadOnly(True)
            buttons[requester] = AllowButton(latus_app_data_folder, requester)
            grid_layout.addWidget(lines[requester], row, 0)
            grid_layout.addWidget(buttons[requester], row, 1)
            row += 1
        self.setLayout(grid_layout)
        self.setWindowTitle("Management")


if __name__ == '__main__':
    import sys
    import os
    import shutil
    import logging
    import latus.logger
    import latus.folders
    import latus.util
    import latus.preferences
    import latus.nodedb

    root = os.path.join('temp', 'gui_management')
    app_data_folders = os.path.join(root, 'appdata')
    if os.path.exists(root):
        shutil.rmtree(root)

    latus.logger.init(root)
    latus.logger.set_console_log_level(logging.INFO)
    latus_key = 'my_secret_latus_key'

    log_folder = os.path.join(root, 'log')
    latus.util.make_dirs(log_folder)
    latus.logger.init(log_folder)
    cloud_folder = os.path.join(root, 'cloud')
    cloud_folders = latus.folders.CloudFolders(cloud_folder)

    user_prefix = 'user_'
    computer_prefix = 'computer_'
    preferences = {}
    node_dbs = {}
    kms = {}
    app_data_folders = {}
    for node in ['a', 'b', 'c']:
        app_data_folders[node] = os.path.join(root, node, 'appdata')
        preferences[node] = latus.preferences.Preferences(app_data_folders[node], True)
        preferences[node].set_node_id(node)
        preferences[node].set_new_private_key()
        preferences[node].set_cloud_root(cloud_folder)
        node_dbs[node] = latus.nodedb.NodeDB(cloud_folders.nodedb, node, preferences[node].get_public_key(), True)
        node_dbs[node].set_user(user_prefix + node)  # essentially override defaults
        node_dbs[node].set_computer(computer_prefix + node)  # essentially override defaults
        kms[node] = latus.key_management.KeyManagement(app_data_folders[node])
    preferences['a'].set_crypto_key_string(latus_key)  # a has the latus key, b and c want it

    kms['b'].request_key()
    kms['c'].request_key()

    app = QtWidgets.QApplication(sys.argv)
    dialog = ManagementDialog(app_data_folders['a'])
    dialog.show()
    dialog.exec_()
