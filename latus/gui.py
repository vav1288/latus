import sys
import os
from PyQt5 import QtWidgets, QtCore, QtGui 


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
        print('stopped here ... start a thread that runs the sync!')

    def close(self):
        self.tray_icon.hide()
        super(MainWindow, self).close()

def main(args):
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    sys.exit(app.exec_())