
import os
import logging

from PyQt5 import QtWidgets, QtCore

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
        self.label = QtWidgets.QLabel(name + ':')
        self.line = QtWidgets.QLineEdit(value)
        self.line.setMinimumWidth(600)  # swag
        self.select_button = QtWidgets.QDialogButtonBox()
        self.line.setReadOnly(True)  # guide user via dialog boxes - don't allow them to just type anything in
        if method:
            self.select_button.addButton(button_text, QtWidgets.QDialogButtonBox.AcceptRole)
            self.select_button.accepted.connect(method)

    def layout(self, grid, column):
        grid.addWidget(self.label, column, 0)
        grid.addWidget(self.line, column, 1)
        grid.addWidget(self.select_button, column, 2)

    def get(self):
        return self.line.text()


class CheckBoxUI:
    """
    Set up a check box widgets
    """
    def __init__(self, name, value, method=None):
        self.check_box = QtWidgets.QCheckBox(name)
        if method:
            self.check_box.stateChanged.connect(method)


class PreferencesDialog(QtWidgets.QDialog):
    def __init__(self, latus_appdata_folder):
        latus.logger.log.info('starting PreferencesDialog')
        super().__init__()
        grid_layout = QtWidgets.QGridLayout()

        self.pref = latus.preferences.Preferences(latus_appdata_folder)
        self.latus_folder = LineUI('Latus folder', self.pref.get_latus_folder(), self.new_folder)
        self.cloud_folder = LineUI('Cloud Folder', self.pref.get_cloud_root(), self.new_folder)
        self.key_ui = CryptoKeyUI(self.pref.get_crypto_key_string(), latus_appdata_folder)
        self.node_id = LineUI('Node ID', self.pref.get_node_id())
        self.blank = QtWidgets.QLabel('')

        ok_buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)
        ok_buttonBox.accepted.connect(self.ok)
        cancel_buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Cancel)
        cancel_buttonBox.rejected.connect(self.cancel)

        self.latus_folder.layout(grid_layout, 0)
        self.cloud_folder.layout(grid_layout, 1)
        self.key_ui.layout(grid_layout, 2)
        self.node_id.layout(grid_layout, 3)
        grid_layout.addWidget(self.blank, 4, 0)
        grid_layout.addWidget(ok_buttonBox, 5, 0)
        grid_layout.addWidget(cancel_buttonBox, 5, 1, alignment=QtCore.Qt.AlignLeft)  # kind of cheating on the layout
        grid_layout.setColumnStretch(1, 1)  # path column
        self.setLayout(grid_layout)

        self.setWindowTitle("Preferences")

    def ok(self):
        self.pref.set_latus_folder(self.latus_folder.get())
        self.pref.set_cloud_root(self.cloud_folder.get())
        self.pref.set_new_private_key()
        self.pref.set_crypto_key_string(self.key_ui.get())
        self.close()

    def cancel(self):
        self.close()

    def new_folder(self):
        f = QtWidgets.QFileDialog.getExistingDirectory()
        return f


# todo: does this really need to be a separate class?  Perhaps put it back into PreferencesDialog
class CryptoKeyUI:
    """
    Set up the crypto key widgets
    """
    def __init__(self, key, latus_appdata_folder):
        self.latus_appdata_folder = latus_appdata_folder
        self.label = QtWidgets.QLabel("Key:")
        self.line = QtWidgets.QLineEdit(key)
        self.line.setMinimumWidth(400)  # swag
        self.line.setReadOnly(True)  # guide user via dialog boxes - don't allow them to just type anything in

        self.manage_button = QtWidgets.QDialogButtonBox()
        self.manage_button.addButton('Manage ...', QtWidgets.QDialogButtonBox.AcceptRole)
        self.manage_button.accepted.connect(self.manage_key)

    def layout(self, grid, column):
        grid.addWidget(self.label, column, 0)
        grid.addWidget(self.line, column, 1)
        grid.addWidget(self.manage_button, column, 2)

    def get(self):
        return self.line.text()

    def set(self, s):
        self.line.setText(s)

    def manage_key(self):
        crypto_key_dialog = CryptoKeyDialog(self.latus_appdata_folder)
        crypto_key_dialog.exec_()


class CryptoKeyDialog(QtWidgets.QDialog):
    """
    Dialog box for managing the crypto key.
    """
    def __init__(self, latus_appdata_folder):
        super().__init__()

        self.caption = 'Key file'

        self.pref = latus.preferences.Preferences(latus_appdata_folder)
        ok_buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)
        ok_buttonBox.accepted.connect(self.ok)
        cancel_buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Cancel)
        cancel_buttonBox.rejected.connect(self.cancel)

        generate_buttonBox = QtWidgets.QDialogButtonBox()
        generate_buttonBox.addButton('Generate New Key', QtWidgets.QDialogButtonBox.AcceptRole)
        generate_buttonBox.clicked.connect(self.generate_key)

        load_button_box = QtWidgets.QDialogButtonBox()
        load_button_box.addButton('Load Key', QtWidgets.QDialogButtonBox.AcceptRole)
        load_button_box.clicked.connect(self.load_key)

        save_button_box = QtWidgets.QDialogButtonBox()
        save_button_box.addButton('Save Key', QtWidgets.QDialogButtonBox.AcceptRole)
        save_button_box.clicked.connect(self.save_key)

        self.key_ui = CryptoKeyUI(self.pref.get_crypto_key_string(), latus_appdata_folder)

        grid_layout = QtWidgets.QGridLayout()
        self.key_ui.layout(grid_layout, 0)
        grid_layout.addWidget(generate_buttonBox, 0, 2)
        grid_layout.addWidget(load_button_box, 1, 0)
        grid_layout.addWidget(save_button_box, 1, 1, alignment=QtCore.Qt.AlignLeft)  # kind of cheating on the layout
        grid_layout.addWidget(ok_buttonBox, 2, 0)
        grid_layout.addWidget(cancel_buttonBox, 2, 1, alignment=QtCore.Qt.AlignLeft)  # kind of cheating on the layout
        grid_layout.setColumnStretch(1, 1)  # key column
        self.setLayout(grid_layout)

        self.setWindowTitle("Key Management")

    def load_key(self):
        print(self.pref.get_key_folder())
        path, _ = QtWidgets.QFileDialog.getOpenFileName(None, self.caption, self.pref.get_key_folder(),
                                                        '*' + latus.const.LATUS_KEY_FILE_EXTENSION)
        if path:
            self.pref.set_key_folder(os.path.dirname(path))
            key_file = latus.crypto.CryptoFile(path)
            key_info = key_file.load_key()
            key = key_info['cryptokey']
            self.key_ui.set(key)

    def save_key(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(None, self.caption, self.pref.get_key_folder(),
                                                        '*' + latus.const.LATUS_KEY_FILE_EXTENSION)
        if path:
            self.pref.set_key_folder(os.path.dirname(path))
            key_file = latus.crypto.CryptoFile(path)
            key_file.save(self.key_ui.get())

    def generate_key(self):
        new_key = latus.crypto.new_key()
        self.key_ui.set(new_key.decode())

    def ok(self):
        self.pref.set_crypto_key_string(self.key_ui.get())
        self.close()

    def cancel(self):
        self.close()


if __name__ == '__main__':
    import sys
    temp_dir = 'temp'
    latus.logger.init(os.path.join(temp_dir, 'log'))
    latus.logger.set_console_log_level(logging.INFO)

    app = QtWidgets.QApplication(sys.argv)

    preferences_dialog = PreferencesDialog('temp')
    preferences_dialog.show()
    preferences_dialog.exec_()