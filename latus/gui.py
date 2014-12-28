import sys
import os
import logging
from PyQt5 import QtWidgets, QtCore, QtGui

import latus.logger
import latus.sync
import latus.config
import latus.util
import latus.const


class SystemTrayIcon(QtWidgets.QSystemTrayIcon):

    def __init__(self, app, latus_appdata_folder, parent=None):
        self.app = app
        icon_path = os.path.abspath(os.path.join('icons', 'active.ico'))
        icon = QtGui.QIcon(icon_path)
        super(SystemTrayIcon, self).__init__(icon, parent)
        self.latus_appdata_folder = latus_appdata_folder

        menu = QtWidgets.QMenu(parent)
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
        qw = QtWidgets.QMessageBox()
        QtWidgets.QMessageBox.about(qw, 'latus', 'www.lat.us')

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