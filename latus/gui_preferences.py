
import os
import logging

from PyQt5.QtWidgets import QLabel, QDialogButtonBox, QVBoxLayout, QLineEdit, QGridLayout, QFileDialog, QDialog, \
    QGroupBox, QCheckBox
from PyQt5.QtCore import Qt

import latus.logger
import latus.sync
import latus.preferences
import latus.util
import latus.const
import latus.crypto
import latus.gui_wizard
import latus.nodedb
import latus.folders


class LineUI:
    """
    Set up the folder widgets
    """
    def __init__(self, name, value, method=None, button_text='Select...'):
        self.label = QLabel(name + ':')
        self.line = QLineEdit(value)
        self.line.setMinimumWidth(600)  # swag
        self.select_button = QDialogButtonBox()
        self.line.setReadOnly(True)  # guide user via dialog boxes - don't allow them to just type anything in
        if method:
            self.select_button.addButton(button_text, QDialogButtonBox.AcceptRole)
            self.select_button.accepted.connect(method)

    def layout(self, grid, column):
        grid.addWidget(self.label, column, 0)
        grid.addWidget(self.line, column, 1)
        grid.addWidget(self.select_button, column, 2)

    def get(self):
        return self.line.text()


class PreferencesDialog(QDialog):
    def __init__(self, latus_appdata_folder):
        latus.logger.log.info('starting PreferencesDialog')

        self.pref = latus.preferences.Preferences(latus_appdata_folder)
        cloud_folders = latus.folders.CloudFolders(self.pref.get_cloud_root())
        self.node_db = latus.nodedb.NodeDB(cloud_folders.nodes, self.pref.get_node_id())

        super().__init__()
        overall_layout = QVBoxLayout()

        folder_preferences_group_box = QGroupBox("Folder Preferences")
        folder_preferences_layout = QGridLayout()
        headers = ['Folder', 'Encrypted', 'Shared', 'Cloud']
        col = 0
        for header in headers:
            folder_preferences_layout.addWidget(QLabel(header), 0, col)
            col += 1
        row = 1

        self.folders = sorted(os.listdir(self.pref.get_latus_folder()))
        self.check_boxes = {}
        for folder in self.folders:
            folder_preferences_layout.addWidget(QLabel(folder))
            col = 1
            self.check_boxes[folder] = []
            for attribute in self.node_db.get_folder_preferences_from_folder(folder):
                s = Qt.Unchecked
                if attribute:
                    s = Qt.Checked
                cb = QCheckBox()
                cb.setCheckState(s)
                folder_preferences_layout.addWidget(cb, row, col)
                self.check_boxes[folder].append(cb)
                col += 1
            row += 1
        folder_preferences_group_box.setLayout(folder_preferences_layout)
        overall_layout.addWidget(folder_preferences_group_box)

        folder_locations_group_box = QGroupBox("Folder Locations")
        folder_locations_layout = QGridLayout()
        self.latus_folder = LineUI('Latus Folder', self.pref.get_latus_folder(), self.new_folder)
        self.cloud_folder = LineUI('Cloud Folder', self.pref.get_cloud_root(), self.new_folder)
        self.blank = QLabel('')

        ok_buttonBox = QDialogButtonBox(QDialogButtonBox.Ok)
        ok_buttonBox.accepted.connect(self.ok)
        cancel_buttonBox = QDialogButtonBox(QDialogButtonBox.Cancel)
        cancel_buttonBox.rejected.connect(self.cancel)

        self.latus_folder.layout(folder_locations_layout, row)
        self.cloud_folder.layout(folder_locations_layout, row + 1)
        folder_locations_group_box.setLayout(folder_locations_layout)
        overall_layout.addWidget(folder_locations_group_box)

        # todo: alignment
        overall_layout.addWidget(ok_buttonBox)     # , alignment=QtCore.Qt.AlignLeft)
        overall_layout.addWidget(cancel_buttonBox) # , alignment=QtCore.Qt.AlignLeft)

        self.setLayout(overall_layout)

        self.setWindowTitle("Preferences")

    def ok(self):
        if self.pref.get_latus_folder() != self.latus_folder.get():
            latus.logger.log.info('new latus folder location %s' % self.latus_folder.get())
            self.pref.set_latus_folder(self.latus_folder.get())
        if self.pref.get_cloud_root() != self.cloud_folder.get():
            latus.logger.log.info('new cloud folder location %s' % self.cloud_folder.get())
            self.pref.set_cloud_root(self.cloud_folder.get())
        for folder in self.folders:
            cb_states = tuple([cb.isChecked() for cb in self.check_boxes[folder]])
            current_preferences = self.node_db.get_folder_preferences_from_folder(folder)
            print(cb_states)
            if current_preferences != cb_states:
                print('new prefernces for %s : %s --> %s' % (folder, str(current_preferences), str(cb_states)))
                self.node_db.set_folder_preferences(folder, cb_states[0], cb_states[1], cb_states[2])
        self.close()

    def cancel(self):
        self.close()

    def new_folder(self):
        f = QFileDialog.getExistingDirectory()
        return f


if __name__ == '__main__':
    import sys

    latus.logger.init()
    latus.logger.set_console_log_level(logging.INFO)

    app = QtGui.QApplication(sys.argv)

    app_data_folder = latus.util.get_latus_appdata_roaming_folder()
    preferences = latus.preferences.Preferences(app_data_folder)
    if not preferences.get_node_id():
        preferences.set_node_id(latus.util.new_node_id())
    preferences_dialog = PreferencesDialog(app_data_folder)
    preferences_dialog.show()
    preferences_dialog.exec_()