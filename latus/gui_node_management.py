
import collections
import datetime
import logging
import os
import shutil
import sys

import dateutil.parser

from PyQt5.QtWidgets import QPushButton, QMessageBox, QDialog, QGridLayout, QLabel, QLineEdit, QApplication
from PyQt5.QtGui import QFontMetrics, QFont

import latus.key_management
import latus.logger
import latus.preferences
import latus.folders
import latus.nodedb
import latus.util


class ForgetButton(QPushButton):
    def __init__(self, node, node_db, row_widgets):
        super().__init__('Forget')
        self.node = node
        self.node_db = node_db
        self.row_widgets = row_widgets
        self.clicked.connect(self.do_forget)

    def do_forget(self):
        reply = QMessageBox.question(self, 'Verify Forget',
                                           'Are you sure you want to forget the Latus node from user "%s" on computer "%s"?' %
                                           (self.row_widgets[0].text(), self.row_widgets[1].text()),
                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            latus.logger.log.info('forgetting : %s' % self.node)
            self.node_db.delete()  # the database (file)
            self.hide()  # this button
            for row_widget in self.row_widgets[2:4]:
                row_widget.setText('< Forgotten >')  # the rest of the row


class ManagementDialog(QDialog):
    def __init__(self, latus_app_data_folder):
        latus.logger.log.info('starting ManagementDialog')
        super().__init__()

        pref = latus.preferences.Preferences(latus_app_data_folder)
        cloud_folders = latus.folders.CloudFolders(pref.get_cloud_root())

        grid_layout = QGridLayout()
        cells = [[QLabel('User Name'), QLabel('Computer Name'), QLabel('Latus Node ID'),
                  QLabel('How Long Since Last Seen'), QLabel(''), datetime.timedelta.max]]

        for node in latus.nodedb.get_existing_nodes(cloud_folders.nodes):
            node_db = latus.nodedb.NodeDB(cloud_folders.nodes, node)
            row_widgets = [QLineEdit(node_db.get_user()), QLineEdit(node_db.get_computer()),
                           QLineEdit(node)]
            button = ForgetButton(node, node_db, row_widgets)
            row_widgets += [button]
            cells.append(row_widgets)

        cells = sorted(cells, key=lambda cell : cell[-1], reverse=True)

        widths = collections.defaultdict(int)
        for row in range(0, len(cells)):
            for column in range(0, len(cells[row]) - 1):
                text = cells[row][column].text()
                width = QFontMetrics(QFont()).width(text) * 1.05
                widths[column] = max(widths[column], width)
                if row > 0 and column < len(cells[row]) - 2:
                    cells[row][column].setReadOnly(True)
                grid_layout.addWidget(cells[row][column], row, column)
        for width in widths:
            grid_layout.setColumnMinimumWidth(width, widths[width])
        for row in range(0, len(cells)):
            for column in range(0, len(cells[row]) - 2):
                cells[row][column].setMinimumWidth(widths[column])
        self.setLayout(grid_layout)
        self.setWindowTitle("Latus Node Management")


def main():
    root = os.path.join('temp', 'gui_management')
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

    preferences = {}
    node_dbs = {}
    app_data_folders = {}
    for node in ['a', 'b', 'c']:
        app_data_folders[node] = os.path.join(root, node, 'appdata')
        preferences[node] = latus.preferences.Preferences(app_data_folders[node], True)
        node_id = latus.util.new_node_id()
        preferences[node].set_node_id(node_id)
        preferences[node].set_cloud_root(cloud_folder)
        latus.util.make_dirs(cloud_folders.nodes)
        node_dbs[node] = latus.nodedb.NodeDB(cloud_folders.nodes, node_id, True)
        node_dbs[node].set_user('user_' + node)  # essentially override defaults
        node_dbs[node].set_computer('computer_' + node)  # essentially override defaults
    preferences['a'].set_crypto_key(latus_key)  # a has the latus key, b and c want it

    app = QApplication(sys.argv)
    dialog = ManagementDialog(app_data_folders['a'])
    dialog.show()
    dialog.exec_()
    print(app.applicationName())


if __name__ == '__main__':
    main()