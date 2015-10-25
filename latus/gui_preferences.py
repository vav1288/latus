
import os
import logging

from PySide import *

import latus.logger
import latus.sync
import latus.preferences
import latus.util
import latus.const
import latus.crypto
import latus.gui_wizard


class LineUI:
    """
    Set up the folder widgets
    """
    def __init__(self, name, value, method=None, button_text='Select...'):
        self.label = QtGui.QLabel(name + ':')
        self.line = QtGui.QLineEdit(value)
        self.line.setMinimumWidth(600)  # swag
        self.select_button = QtGui.QDialogButtonBox()
        self.line.setReadOnly(True)  # guide user via dialog boxes - don't allow them to just type anything in
        if method:
            self.select_button.addButton(button_text, QtGui.QDialogButtonBox.AcceptRole)
            self.select_button.accepted.connect(method)

    def layout(self, grid, column):
        grid.addWidget(self.label, column, 0)
        grid.addWidget(self.line, column, 1)
        grid.addWidget(self.select_button, column, 2)

    def get(self):
        return self.line.text()


class PreferencesDialog(QtGui.QDialog):
    def __init__(self, latus_appdata_folder):
        latus.logger.log.info('starting PreferencesDialog')
        super().__init__()
        overall_layout = QtGui.QVBoxLayout()

        folder_preferences_group_box = QtGui.QGroupBox("Folder Preferences")
        folder_preferences_layout = QtGui.QGridLayout()
        headers = ['Folder', 'Encrypted', 'Shared', 'Cloud']
        col = 0
        for header in headers:
            folder_preferences_layout.addWidget(QtGui.QLabel(header), 0, col)
            col += 1
        row = 1
        folders = {}  # DEBUG DEBUG DEBUG
        for folder in folders:
            folder_preferences_layout.addWidget(QtGui.QLabel(folder))
            col = 1
            for attribute in folders[folder]:
                s = QtCore.Qt.CheckState.Unchecked
                if attribute:
                    s = QtCore.Qt.CheckState.Checked
                cb = QtGui.QCheckBox()
                cb.setCheckState(s)
                folder_preferences_layout.addWidget(cb, row, col)
                col += 1
            row += 1
        folder_preferences_group_box.setLayout(folder_preferences_layout)
        overall_layout.addWidget(folder_preferences_group_box)

        folder_locations_group_box = QtGui.QGroupBox("Folder Locations")
        folder_locations_layout = QtGui.QGridLayout()
        self.pref = latus.preferences.Preferences(latus_appdata_folder)
        self.latus_folder = LineUI('Latus folder', self.pref.get_latus_folder(), self.new_folder)
        self.cloud_folder = LineUI('Cloud Folder', self.pref.get_cloud_root(), self.new_folder)
        self.blank = QtGui.QLabel('')

        ok_buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok)
        ok_buttonBox.accepted.connect(self.ok)
        cancel_buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Cancel)
        cancel_buttonBox.rejected.connect(self.cancel)

        self.latus_folder.layout(folder_locations_layout, row)
        self.cloud_folder.layout(folder_locations_layout, row + 1)
        folder_locations_group_box.setLayout(folder_locations_layout)
        overall_layout.addWidget(folder_locations_group_box)

        overall_layout.addWidget(ok_buttonBox, alignment=QtCore.Qt.AlignLeft)
        overall_layout.addWidget(cancel_buttonBox, alignment=QtCore.Qt.AlignLeft)

        self.setLayout(overall_layout)

        self.setWindowTitle("Preferences")

    def ok(self):
        self.pref.set_latus_folder(self.latus_folder.get())
        self.pref.set_cloud_root(self.cloud_folder.get())
        self.close()

    def cancel(self):
        self.close()

    def new_folder(self):
        f = QtGui.QFileDialog.getExistingDirectory()
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