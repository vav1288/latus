
import sys
import logging
import shutil
import os

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QMessageBox, QLabel
from PyQt5.Qt import QApplication

import latus.logger
import latus.preferences
import latus.csp.cloud_folders


class AdvancedDialog(QDialog):
    def __init__(self, app_data_folder, stop_handler=None):

        # Called right before any actions that require the app to be stopped before the action is done,
        # and will also require that a running app exit when this dialog is closed.  For example,
        # when a node DB is cleared.
        self.stop_handler = stop_handler

        super().__init__()
        self.setWindowTitle('Advanced')
        layout = QVBoxLayout(self)

        buttons = [('', None), ('Clear Cache', self.clear_cache), ('Clear This Node DB', self.clear_this_node_db),
                   ('Clear All Node DBs', self.clear_all_node_dbs),
                   ('Reinitialize Preferences DB', self.reinit_preferences_db), ('Delete All', self.delete_all),
                   ('Quit', self.done_handler)]

        layout.addWidget(QLabel('WARNING - ONLY FOR ADVANCED USERS'))
        for label, handler in buttons:
            b = QPushButton(label, self)
            if handler:
                b.clicked.connect(handler)
            else:
                b.hide()  # trick since first button will be highlighted but we don't want that
            layout.addWidget(b)

        self.preferences = None
        self.cloud_folders = None
        if app_data_folder:
            self.preferences = latus.preferences.Preferences(app_data_folder)
            if False:
                # deprecated ...
                cloud_root = self.preferences.get_cloud_root()
                if cloud_root:
                    self.cloud_folders = latus.folders.CloudFolders(cloud_root)

    def clear_cache(self):
        self._do_stop()
        if self._do_clear_cache():
            self.done_dialog('Cache cleared')
        else:
            self.done_dialog('No cloud folders yet specified')

    def clear_this_node_db(self):
        self._do_stop()
        self.done_dialog('Not yet implemented')  # todo: implement clearing this node's DB

    def clear_all_node_dbs(self):
        self._do_stop()
        if self.cloud_folders:
            shutil.rmtree(self.cloud_folders.nodes, ignore_errors=True)
            self.done_dialog('Deleted all Node DBs')
        else:
            self.done_dialog('No cloud folders yet specified')

    def reinit_preferences_db(self):
        self.done_dialog('Not yet implemented')  # todo: read the existing preferences DB and write out as latest version

    def delete_all(self):
        self._do_stop()
        shutil.rmtree(self.preferences.get_app_data_folder(), ignore_errors=True)
        self._do_clear_cache()
        self.done_dialog('Deleted all')

    def _do_clear_cache(self):
        if self.cloud_folders:
            shutil.rmtree(self.cloud_folders.cache, ignore_errors=True)
            return True
        return False

    def _do_stop(self):
        if self.stop_handler:
            latus.logger.log.info('calling stop_handler')
            self.stop_handler()

    def done_handler(self):
        self.done(QDialog.Accepted)

    def done_dialog(self, message):
        d = QMessageBox()
        d.setWindowTitle('Finished')
        d.setText(message)
        d.exec_()

g_exit_flag = False


def main():

    def my_stop_handler():
        global g_exit_flag
        latus.logger.log.info('stopping')
        g_exit_flag = True

    latus.logger.init(None)
    latus.logger.set_console_log_level(logging.INFO)

    app = QApplication(sys.argv)

    app_data_folder = os.path.join('test_latus', 'data', 'test_simple', 'a', 'appdata')
    if not os.path.exists(app_data_folder):
        s = '%s does not exist - please run the py.test to make it' % app_data_folder
        print(s)
        sys.exit(s)

    advanced_dialog = AdvancedDialog(app_data_folder, my_stop_handler)
    advanced_dialog.show()
    advanced_dialog.exec_()
    if g_exit_flag:
        latus.logger.log.info('exiting')

if __name__ == '__main__':
    main()
