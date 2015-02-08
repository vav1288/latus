import sys
import os
from PyQt5 import QtWidgets, QtCore, QtGui

import latus.logger
import latus.sync
import latus.config
import latus.util
import latus.const
import latus.crypto


# todo: put this in PreferencesDialog as a method?  Create grid_layout early and just put all of this in one method.
class LineUI():
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


# todo: does this really need to be a separate class?  Perhaps put it back into PreferencesDialog
class CryptoKeyUI():
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


class PreferencesDialog(QtWidgets.QDialog):
    def __init__(self, latus_appdata_folder):
        super(PreferencesDialog, self).__init__()

        self.config = latus.config.Config(latus_appdata_folder)
        self.latus_folder = LineUI('Latus folder', self.config.latus_folder_get(), self.new_folder)
        self.cloud_folder = LineUI('Cloud Folder', self.config.cloud_root_get(), self.new_folder)
        self.key_ui = CryptoKeyUI(self.config.crypto_get_string(), latus_appdata_folder)
        self.node_id = LineUI('Node ID', self.config.node_id_get())

        ok_buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)
        ok_buttonBox.accepted.connect(self.ok)
        cancel_buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Cancel)
        cancel_buttonBox.rejected.connect(self.cancel)

        grid_layout = QtWidgets.QGridLayout()
        self.latus_folder.layout(grid_layout, 0)
        self.cloud_folder.layout(grid_layout, 1)
        self.key_ui.layout(grid_layout, 2)
        self.node_id.layout(grid_layout, 3)
        grid_layout.addWidget(ok_buttonBox, 4, 0)
        grid_layout.addWidget(cancel_buttonBox, 4, 1, alignment=QtCore.Qt.AlignLeft)  # kind of cheating on the layout
        grid_layout.setColumnStretch(1, 1)  # path column
        self.setLayout(grid_layout)

        self.setWindowTitle("Preferences")

    def ok(self):
        self.config.latus_folder_set(self.latus_folder.get())
        self.config.cloud_root_set(self.cloud_folder.get())
        self.config.crypto_set_string(self.key_ui.get())
        self.close()

    def cancel(self):
        self.close()

    def new_folder(self):
        f = QtWidgets.QFileDialog.getExistingDirectory()
        return f


class CryptoKeyDialog(QtWidgets.QDialog):
    """
    Dialog box for managing the crypto key.
    """
    def __init__(self, latus_appdata_folder):
        super(CryptoKeyDialog, self).__init__()

        self.caption = 'Key file'

        self.config = latus.config.Config(latus_appdata_folder)
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

        self.key_ui = CryptoKeyUI(self.config.crypto_get_string(), latus_appdata_folder)

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
        print(self.config.key_folder_get())
        path, _ = QtWidgets.QFileDialog.getOpenFileName(None, self.caption, self.config.key_folder_get(),
                                                        '*' + latus.const.LATUS_KEY_FILE_EXTENSION)
        if path:
            self.config.key_folder_set(os.path.dirname(path))
            key_file = latus.crypto.CryptoFile(path)
            key_info = key_file.load_key()
            key = key_info['cryptokey']
            self.key_ui.set(key)

    def save_key(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(None, self.caption, self.config.key_folder_get(),
                                                        '*' + latus.const.LATUS_KEY_FILE_EXTENSION)
        if path:
            self.config.key_folder_set(os.path.dirname(path))
            key_file = latus.crypto.CryptoFile(path)
            key_file.save(self.key_ui.get())

    def generate_key(self):
        new_key = latus.crypto.new_key()
        self.key_ui.set(new_key.decode())

    def ok(self):
        self.config.crypto_set_string(self.key_ui.get())
        self.close()

    def cancel(self):
        self.close()

class SystemTrayIcon(QtWidgets.QSystemTrayIcon):

    def __init__(self, app, latus_appdata_folder, parent=None):
        self.app = app

        import icons.icons  # actually used for QPixmap
        icon = QtGui.QIcon(QtGui.QPixmap(':active.png'))
        super(SystemTrayIcon, self).__init__(icon, parent)
        self.latus_appdata_folder = latus_appdata_folder

        menu = QtWidgets.QMenu(parent)
        about_action = menu.addAction("Preferences")
        about_action.triggered.connect(self.preferences)
        about_action = menu.addAction("About")
        about_action.triggered.connect(self.about)
        exit_action = menu.addAction("Exit")
        exit_action.triggered.connect(self.exit)
        self.setContextMenu(menu)

        self.start_latus()

    def start_latus(self):
        config = latus.config.Config(self.latus_appdata_folder)
        latus.logger.log.info("latus_app_data: %s" % self.latus_appdata_folder)

        if not config.crypto_get():
            crypto_key_dialog = CryptoKeyDialog(self.latus_appdata_folder)
            crypto_key_dialog.exec_()
        if not config.cloud_root_get():
            QtWidgets.QMessageBox.information(QtWidgets.QMessageBox(), latus.const.NAME,
                                              'Please select the cloud folder (e.g. Dropbox, Google Drive, Microsoft One Drive, etc.)')
            config.cloud_root_set(str(QtWidgets.QFileDialog.getExistingDirectory(QtWidgets.QFileDialog(), "Select Cloud Folder",
                                                                                 options=QtWidgets.QFileDialog.ShowDirsOnly)))
        if not config.latus_folder_get():
            QtWidgets.QMessageBox.information(QtWidgets.QMessageBox(), latus.const.NAME, 'Please select a latus folder')
            config.latus_folder_set(str(QtWidgets.QFileDialog.getExistingDirectory(QtWidgets.QFileDialog(), "Select Latus Folder",
                                                                                   options=QtWidgets.QFileDialog.ShowDirsOnly)))
        if not config.node_id_get():
            config.node_id_set(latus.util.new_node_id())
            QtWidgets.QMessageBox.information(QtWidgets.QMessageBox(), latus.const.NAME, 'Note: A new Node ID has been created: %s' % str(config.node_id_get()))

        self.sync = latus.sync.Sync(config.crypto_get(), config.latus_folder_get(), config.cloud_root_get(),
                                    config.node_id_get(), config.verbose_get())
        self.sync.start()

    def show(self):
        QtWidgets.QSystemTrayIcon.show(self)

    def about(self):
        QtWidgets.QMessageBox.about(QtWidgets.QMessageBox(), latus.const.NAME, latus.const.URL)

    def preferences(self):
        preferences_dialog = PreferencesDialog(self.latus_appdata_folder)
        preferences_dialog.exec_()

    def exit(self):
        latus.logger.log.info('exit')
        self.hide()
        self.sync.request_exit()
        QtWidgets.QApplication.exit()


def main(latus_appdata_folder):
    latus.logger.log.info('gui')
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # so popup dialogs don't close the system tray icon
    system_tray = SystemTrayIcon(app, latus_appdata_folder)
    system_tray.show()
    sys.exit(app.exec_())

# for interactive testing
if __name__ == "__main__":
    latus.logger.init(sys.argv[1])
    main(sys.argv[1])