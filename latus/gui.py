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

    def __init__(self, icon, parent=None):
        super(SystemTrayIcon, self).__init__(icon, parent)
        menu = QtWidgets.QMenu(parent)
        exit_action = menu.addAction("Exit")
        exit_action.triggered.connect(parent.close)
        self.setContextMenu(menu)


class MainWindow(QtWidgets.QWidget):
    def __init__(self, latus_appdata_folder):
        super(MainWindow, self).__init__()
        self.tray_icon = SystemTrayIcon(QtGui.QIcon(os.path.join('icons', 'active.ico')), self)
        self.tray_icon.show()

        config = latus.config.Config(latus.util.get_latus_appdata_folder())
        latus.logger.log.info("latus_app_data: %s" % latus_appdata_folder)

        latus_folder = config.latus_folder_get()
        cloud_root = config.cloud_root_get()

        if not config.cloud_root_get() or not config.latus_folder_get():
            exit('error - folders not specified')  # todo: run a setup wizard
        self.sync = latus.sync.Sync(config.crypto_get(), latus_folder, cloud_root, config.verbose_get())
        self.sync.start()

    def close(self):
        self.tray_icon.hide()
        self.sync.request_exit()
        super(MainWindow, self).close()


def main(latus_appdata_folder):
    latus.logger.log.info('gui mode')
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow(latus_appdata_folder)
    sys.exit(app.exec_())