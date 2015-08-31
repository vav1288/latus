import sys
import os
from PyQt5 import QtWidgets, QtCore, QtGui

import latus.logger
import latus.sync
import latus.preferences
import latus.util
import latus.const
import latus.crypto
import latus.gui_wizard
import latus.gui_preferences
import latus.gui_management
import latus.key_management
import latus.patch_crypto_be_discovery


class LatusSystemTrayIcon(QtWidgets.QSystemTrayIcon):

    def __init__(self, app, latus_appdata_folder, parent=None):
        latus.logger.log.info('starting LatusSystemTrayIcon')
        self.app = app

        import icons.icons  # actually used for QPixmap
        icon = QtGui.QIcon(QtGui.QPixmap(':active.png'))
        super().__init__(icon, parent)
        self.latus_appdata_folder = latus_appdata_folder

        menu = QtWidgets.QMenu(parent)
        about_action = menu.addAction("Import Latus Key")
        about_action.triggered.connect(self.import_latus_key)
        about_action = menu.addAction("Export Latus Key")
        about_action.triggered.connect(self.export_latus_key)
        about_action = menu.addAction("Nodes")
        about_action.triggered.connect(self.nodes)
        about_action = menu.addAction("Preferences")
        about_action.triggered.connect(self.preferences)
        about_action = menu.addAction("About")
        about_action.triggered.connect(self.about)
        exit_action = menu.addAction("Exit")
        exit_action.triggered.connect(self.exit)
        self.setContextMenu(menu)

        self.sync = None

    def start_latus(self):
        self.sync = latus.sync.Sync(self.latus_appdata_folder)
        self.sync.start()

    def show(self):
        QtWidgets.QSystemTrayIcon.show(self)

    def import_latus_key(self):
        key = latus.key_management.read_latus_key_gui()
        if key:
            pref = latus.preferences.Preferences(self.latus_appdata_folder)
            pref.set_crypto_key(key)

    def export_latus_key(self):
        pref = latus.preferences.Preferences(self.latus_appdata_folder)
        latus.key_management.write_latus_key_gui(pref.get_crypto_key())

    def about(self):
        QtWidgets.QMessageBox.about(QtWidgets.QMessageBox(), latus.const.NAME, latus.const.URL)

    def preferences(self):
        preferences_dialog = latus.gui_preferences.PreferencesDialog(self.latus_appdata_folder)
        preferences_dialog.exec_()

    def nodes(self):
        management_dialog = latus.gui_management.ManagementDialog(self.latus_appdata_folder)
        management_dialog.exec_()

    def exit(self):
        latus.logger.log.info('exit')
        self.hide()
        if self.sync:
            self.sync.request_exit()
        QtWidgets.QApplication.exit()


def main(latus_appdata_folder):
    latus.logger.log.info('gui')

    latus.patch_crypto_be_discovery.patch_crypto_be_discovery()  # remove this when cryptography discovery gets fixed

    # check if we should run the setup wizard first
    pref = latus.preferences.Preferences(latus_appdata_folder)
    latus.logger.log.info("latus_app_data: %s" % latus_appdata_folder)

    app = QtWidgets.QApplication(sys.argv)  # need this even for the GUIWizard

    if not pref.folders_are_set():
        latus.logger.log.info('not all preferences are set - starting WizardGUI')
        app_gui_wizard = latus.gui_wizard.GUIWizard(latus_appdata_folder)
        app_gui_wizard.exec_()

    if pref.folders_are_set():
        app.setQuitOnLastWindowClosed(False)  # so popup dialogs don't close the system tray icon
        system_tray = LatusSystemTrayIcon(app, latus_appdata_folder)
        system_tray.start_latus()
        system_tray.show()
        app.exec_()
    else:
        msg = 'Incomplete configuration.\n\nPlease re-run Latus and complete the Latus Setup Wizard.\n\nExiting ...'

        w = QtWidgets.QMessageBox()
        w.setWindowTitle(latus.const.NAME)
        w.setText(msg)
        w.exec()

        latus.logger.log.warn(msg.replace('\n', ' '))  # don't put newlines in the log
        sys.exit(1)

# for interactive testing
if __name__ == "__main__":
    latus_appdata_folder = sys.argv[1]
    latus.logger.init(latus_appdata_folder)
    main(latus_appdata_folder)