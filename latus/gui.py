import sys
import os
from PyQt5 import QtWidgets, QtCore, QtGui

import latus.sync
import latus.config
import latus.util
import latus.const


class SystemTrayIcon(QtWidgets.QSystemTrayIcon):

    def __init__(self, icon, parent=None):
        super(SystemTrayIcon, self).__init__(icon, parent)
        menu = QtWidgets.QMenu(parent)
        exitAction = menu.addAction("Exit")
        exitAction.triggered.connect(parent.close)
        self.setContextMenu(menu)


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.tray_icon = SystemTrayIcon(QtGui.QIcon(os.path.join('icons', 'active.ico')), self)
        self.tray_icon.show()

        #self.sync_exit_control = threading.Event()
        #self.sync_thread = SyncThread(self.sync_exit_control)
        #self.sync_thread.start()
        # todo: create a routine in util to get the latus app data folder (not just the overall OS appdata folder)
        config = latus.config.Config(os.path.join(latus.util.get_appdata_folder(), latus.const.NAME))
        self.sync = latus.sync.Sync(config.crypto_get(), config.cloud_root_get(), config.latus_folder_get(),
                                    verbose=config.verbose_get())
        self.sync.start()

    def close(self):
        self.tray_icon.hide()
        self.sync.request_exit()
        super(MainWindow, self).close()


def main(args):
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    sys.exit(app.exec_())