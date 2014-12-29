import sys
import os
import logging
from PyQt5 import QtWidgets, QtCore, QtGui

import latus.logger
import latus.sync
import latus.config
import latus.util
import latus.const

LINE_BOX_PADDING = 50

class Folder():
    def __init__(self, name, path, file_dialog_method, font_metrics):
        self.name = name
        self.label = QtWidgets.QLabel(self.name + " Folder:")
        self.line = QtWidgets.QLineEdit(path)
        self.line.setMinimumWidth(font_metrics.width(path) + LINE_BOX_PADDING)  # actual width plus padding
        self.edit_button = QtWidgets.QDialogButtonBox()
        self.edit_button.addButton('Edit ...', QtWidgets.QDialogButtonBox.AcceptRole)
        self.edit_button.accepted.connect(file_dialog_method)

    def layout(self, grid, column):
        grid.addWidget(self.label, column, 0)
        grid.addWidget(self.line, column, 1)
        grid.addWidget(self.edit_button, column, 2)

    def get(self):
        return self.line.text()


class CryptoKey():
    def __init__(self, key, font_metrics):
        self.label = QtWidgets.QLabel("Key:")
        self.line = QtWidgets.QLineEdit(key)
        self.line.setMinimumWidth(font_metrics.width(key) + LINE_BOX_PADDING)  # actual width plus padding

    def layout(self, grid, column):
        grid.addWidget(self.label, column, 0)
        grid.addWidget(self.line, column, 1)

    def get(self):
        return self.line.text()


class OptionsDialog(QtWidgets.QDialog):
    def __init__(self, latus_appdata_folder):
        super(OptionsDialog, self).__init__()

        self.config = latus.config.Config(latus_appdata_folder)
        self.latus_folder = Folder('Latus', self.config.latus_folder_get(), self.new_folder, self.fontMetrics())
        self.cloud_folder = Folder('Cloud', self.config.cloud_root_get(), self.new_folder, self.fontMetrics())

        self.key = CryptoKey(self.config.crypto_get_string(), self.fontMetrics())

        ok_buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)
        ok_buttonBox.accepted.connect(self.ok)
        cancel_buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Cancel)
        cancel_buttonBox.rejected.connect(self.cancel)

        #self.latus_folder.clicked.connect(self.set_latus_folder)
        #self.cloud_root_folder.clicked.connect(self.set_cloud_root_folder)

        grid_layout = QtWidgets.QGridLayout()
        self.latus_folder.layout(grid_layout, 0)
        self.cloud_folder.layout(grid_layout, 1)
        self.key.layout(grid_layout, 2)
        grid_layout.addWidget(ok_buttonBox, 3, 0)
        grid_layout.addWidget(cancel_buttonBox, 3, 1, alignment=QtCore.Qt.AlignLeft)  # kind of cheating on the layout
        grid_layout.setColumnStretch(1, 1)  # path column
        self.setLayout(grid_layout)

        self.setWindowTitle("Options")

    def ok(self):
        self.config.latus_folder_set(self.latus_folder.get())
        self.config.cloud_root_set(self.cloud_folder.get())
        self.config.crypto_set_string(self.key.get())
        self.close()

    def cancel(self):
        self.close()

    def new_folder(self):
        f = QtWidgets.QFileDialog.getExistingDirectory()
        return f

class SystemTrayIcon(QtWidgets.QSystemTrayIcon):

    def __init__(self, app, latus_appdata_folder, parent=None):
        self.app = app
        icon_path = os.path.abspath(os.path.join('icons', 'active.ico'))
        icon = QtGui.QIcon(icon_path)
        super(SystemTrayIcon, self).__init__(icon, parent)
        self.latus_appdata_folder = latus_appdata_folder

        menu = QtWidgets.QMenu(parent)
        about_action = menu.addAction("Options")
        about_action.triggered.connect(self.options)
        about_action = menu.addAction("About")
        about_action.triggered.connect(self.about)
        exit_action = menu.addAction("Exit")
        exit_action.triggered.connect(self.exit)
        self.setContextMenu(menu)

        self.start_latus()

    def start_latus(self):
        config = latus.config.Config(self.latus_appdata_folder)
        latus.logger.log.info("latus_app_data: %s" % self.latus_appdata_folder)

        latus_folder = config.latus_folder_get()
        cloud_root = config.cloud_root_get()

        if not config.cloud_root_get() or not config.latus_folder_get():
            exit('error - folders not specified')  # todo: run a setup wizard
        self.sync = latus.sync.Sync(config.crypto_get(), latus_folder, cloud_root, config.verbose_get())
        self.sync.start()

    def show(self):
        QtWidgets.QSystemTrayIcon.show(self)

    def about(self):
        QtWidgets.QMessageBox.about(QtWidgets.QMessageBox(), 'latus', 'www.lat.us')

    def options(self):
        options_dialog = OptionsDialog(self.latus_appdata_folder)
        options_dialog.exec_()

    def exit(self):
        self.hide()
        self.sync.request_exit()
        QtWidgets.QApplication.exit()


def main(latus_appdata_folder):
    latus.logger.log.info('gui mode')
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # so popup dialogs don't close the system tray icon
    system_tray = SystemTrayIcon(app, latus_appdata_folder)
    system_tray.show()
    sys.exit(app.exec_())