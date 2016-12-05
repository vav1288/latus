import sys
import os
import subprocess

from PyQt5.QtGui import QFontMetrics, QFont, QIcon, QPixmap
from PyQt5.QtWidgets import QGridLayout, QLabel, QLineEdit, QSystemTrayIcon, QMenu, QDialog, QApplication, QMessageBox

import latus.const
import latus.crypto
import latus.gui_node_management
import latus.gui_preferences
import latus.gui_wizard
import latus.key_management
import latus.logger
import latus.preferences
import latus.sync
import latus.util


def message_box(msg):
    w = QMessageBox()
    w.setWindowTitle(latus.const.NAME)
    w.setText(msg)
    w.show()
    return w


class About(QDialog):

    def __init__(self, node_id):
        super().__init__()  # todo: fill in parameter?
        self.setWindowTitle(latus.const.NAME)
        layout = QGridLayout(self)
        self.setLayout(layout)
        layout.addWidget(QLabel(latus.const.URL), 0, 0)

        self.add_line('Latus Node ID:', node_id, 2, layout)
        self.add_line('Log folder:', latus.logger.get_base_log_file_path(), 5, layout)

        self.show()

    def add_line(self, label, value, row_number, layout):
        layout.addWidget(QLabel(label), row_number, 0)
        log_dir_widget = QLineEdit(value)
        log_dir_widget.setReadOnly(True)
        width = QFontMetrics(QFont()).width(value) * 1.05
        log_dir_widget.setMinimumWidth(width)
        layout.addWidget(log_dir_widget, row_number+1, 0)


class LatusSystemTrayIcon(QSystemTrayIcon):

    def __init__(self, app, latus_appdata_folder, parent=None):
        latus.logger.log.info('starting LatusSystemTrayIcon')
        self.app = app

        from latus import icons
        icon = QIcon(QPixmap(':active.png'))
        super().__init__(icon, parent)
        self.latus_appdata_folder = latus_appdata_folder

        menu = QMenu(parent)
        menu.addAction("Open Latus Folder").triggered.connect(self.open_latus_folder)
        menu.addSeparator()
        menu.addAction("Import Latus Key").triggered.connect(self.import_latus_key)
        menu.addAction("Export Latus Key").triggered.connect(self.export_latus_key)
        menu.addAction("Nodes").triggered.connect(self.nodes)
        menu.addAction("Preferences").triggered.connect(self.preferences)
        menu.addAction("About").triggered.connect(self.about)
        menu.addAction("Exit").triggered.connect(self.exit)
        self.setContextMenu(menu)

        self.sync = None

    def activated(self, reason):
        super().activated(reason)
        if reason == self.DoubleClick:
            self.open_latus_folder()

    def start_latus(self):
        self.sync = latus.sync.Sync(self.latus_appdata_folder)
        self.sync.start()

    def show(self):
        QSystemTrayIcon.show(self)

    def open_latus_folder(self):
        pref = latus.preferences.Preferences(self.latus_appdata_folder)
        if latus.util.is_windows():
            # todo: startfile() seems to be deprecated ... ?
            os.startfile(pref.get_latus_folder())  # keep the app running - call('explorer') would kil it
        elif latus.util.is_mac():
            subprocess.check_call(['open', pref.get_latus_folder()])
        else:
            # todo: what about Linux?
            raise NotImplementedError

    def import_latus_key(self):
        key = latus.key_management.read_latus_key_gui()
        if key:
            pref = latus.preferences.Preferences(self.latus_appdata_folder)
            pref.set_crypto_key(key)

    def export_latus_key(self):
        pref = latus.preferences.Preferences(self.latus_appdata_folder)
        latus.key_management.write_latus_key_gui(pref.get_crypto_key())

    def about(self):
        pref = latus.preferences.Preferences(self.latus_appdata_folder)
        about_box = About(pref.get_node_id())
        about_box.exec()

    def preferences(self):
        preferences_dialog = latus.gui_preferences.PreferencesDialog(self.latus_appdata_folder)
        preferences_dialog.exec_()

    def nodes(self):
        management_dialog = latus.gui_node_management.ManagementDialog(self.latus_appdata_folder)
        management_dialog.exec_()

    def exit(self):
        latus.logger.log.info('exit')
        self.hide()
        if self.sync:
            self.sync.request_exit()
        QApplication.exit()  # todo: what should this parameter be?


def main(latus_appdata_folder):

    latus.logger.log.info("latus_app_data: %s" % latus_appdata_folder)

    # check if we should run the setup wizard first
    if latus.preferences.preferences_db_exists(latus_appdata_folder):
        pref = latus.preferences.Preferences(latus_appdata_folder)
    else:
        pref = None

    app = QApplication(sys.argv)  # need this even for the GUIWizard

    if not pref or (pref and not pref.folders_are_set()):
        latus.logger.log.info('not all preferences are set - starting WizardGUI')
        app_gui_wizard = latus.gui_wizard.GUIWizard(latus_appdata_folder)
        app_gui_wizard.exec_()
        pref = latus.preferences.Preferences(latus_appdata_folder)

    if pref and pref.folders_are_set():
        app.setQuitOnLastWindowClosed(False)  # so popup dialogs don't close the system tray icon
        system_tray = LatusSystemTrayIcon(app, latus_appdata_folder)
        system_tray.start_latus()
        system_tray.show()
        app.exec_()
    else:
        msg = 'Incomplete configuration.\n\nPlease re-run Latus and complete the Latus Setup Wizard.\n\nExiting ...'
        mb = message_box(msg)
        mb.exec()
        latus.logger.log.warn(msg.replace('\n', ' '))  # don't put newlines in the log
        sys.exit(1)

# for interactive testing
if __name__ == "__main__":
    args = latus.util.arg_parse()
    latus.logger.init_from_args(args)
    main(args.latus_appdata_folder)
