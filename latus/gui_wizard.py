
import time
import os

from PyQt5 import QtWidgets, QtCore

import latus.wizard
import latus.preferences
import latus.gui
import latus.sync
import latus.folders
import latus.logger
import latus.crypto
import latus.util
import latus.nodedb
import latus.key_management

CLOUD_FOLDER_FIELD_STRING = 'cloud_folder'
LATUS_FOLDER_FIELD_STRING = 'latus_folder'
NODE_ID_FIELD_STRING = 'node_id'
LATUS_KEY_FIELD_STRING = 'latus_key'


class GUIWizard(QtWidgets.QWizard):

    # cloud_folder parameter generally only used for testing
    def __init__(self, app_data_folder, cloud_root_override=None):
        super().__init__()
        self.app_data_folder = app_data_folder
        latus.logger.log.info('starting GUIWizard : app_data_folder : %s' % app_data_folder)

        self.folder_wizard = latus.wizard.FolderWizard()

        self.addPage(IntroPage())
        self.addPage(CloudRootPage(self.folder_wizard, cloud_root_override))
        self.addPage(LatusFolderPage())
        self.addPage(LatusKeyPage())
        self.addPage(ConclusionPage())
        self.setWindowTitle("Latus Setup")
        self.show()

    def accept(self):
        pref = latus.preferences.Preferences(self.app_data_folder)
        pref.set_cloud_root(self.field(CLOUD_FOLDER_FIELD_STRING))
        pref.set_latus_folder(self.field(LATUS_FOLDER_FIELD_STRING))
        pref.set_node_id(self.field(NODE_ID_FIELD_STRING))
        pref.set_crypto_key_string(self.field(LATUS_KEY_FIELD_STRING))
        super().accept()

    def done(self, result):
        self.folder_wizard.request_exit()
        super().done(result)


class IntroPage(QtWidgets.QWizardPage):

    def __init__(self):
        super().__init__()
        self.setTitle("Latus Setup Wizard")

        self.node_id_line = QtWidgets.QLineEdit()  # non-visible
        self.registerField(NODE_ID_FIELD_STRING, self.node_id_line)
        self.node_id_line.setText(latus.util.new_node_id())

        label = QtWidgets.QLabel("This will guide you through the Latus setup process.")
        label.setWordWrap(True)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(label)
        self.setLayout(layout)


class WizardFolderListWidget(QtWidgets.QListWidget):
    def __init__(self, change_method):
        self.change_method = change_method
        super().__init__()

    def selectionChanged(self, a, b):
        self.change_method()
        super().selectionChanged(a, b)


class CloudRootPage(QtWidgets.QWizardPage):

    complete_trigger = QtCore.pyqtSignal()
    selection_trigger = QtCore.pyqtSignal()

    def __init__(self, folder_wizard, cloud_root_override=None):
        super().__init__()
        self.prior_time = 0
        self.prior_is_complete = None

        self.cloud_folder_list = WizardFolderListWidget(self.isComplete)
        self.cloud_folder_list.SelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

        self.folder_wizard = folder_wizard
        self.cloud_root_override = cloud_root_override

        self.folder_wizard.set_found_alert(self.wizard_alert)
        self.folder_wizard.set_progress(self.progress_method)
        self.folder_wizard.start()

        self.setTitle("Cloud storage folder")
        self.setSubTitle("We will now attempt to automatically find your cloud storage folder.  This is the folder you "
                         "use for Dropbox, Microsoft's OneDrive, Google Drive, etc.\n\nOnce your cloud storage folder"
                         " is shown, please select it and hit 'Next'.")

        self.progress_line = QtWidgets.QLineEdit()
        self.progress_line.setReadOnly(True)
        self.progress_line.setText('...')

        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.progress_line, 0, 0)
        layout.addWidget(self.cloud_folder_list, 1, 0)
        self.setLayout(layout)

        # use this for the value that's been selected
        self.cloud_folder_line = QtWidgets.QLineEdit()
        self.registerField(CLOUD_FOLDER_FIELD_STRING, self.cloud_folder_line)

        self.cloud_folder_list.show()

    # controls the if the 'next' button is enabled or not
    def isComplete(self):
        if self.cloud_folder_list.currentItem():
            is_complete = True
        else:
            is_complete = False
        if is_complete != self.prior_is_complete:
            self.prior_is_complete = is_complete
            self.complete_trigger.connect(self.completeChanged)
            self.complete_trigger.emit()  # inform the window to update the 'next' button state (call this method)
        return is_complete

    def progress_method(self, folder):
        t = time.time()
        if folder:
            # todo: figure out why this can cause a crash if 'rate' is too small
            rate = 1.0  # if this rate is too low (too frequent), Python (or PyQT) will crash ... I don't know why
            if t - self.prior_time > rate:
                self.progress_line.setText('Searching: ' + folder)
                self.progress_line.setCursorPosition(0)  # left justify
                self.prior_time = t
        else:
            self.progress_line.setText('Search complete.  Please select a path below.')

    def wizard_alert(self, folders):
        item_count = 0
        for folder in folders:
            item_string = self.cloud_folder_list.item(item_count)
            if not item_string:
                self.cloud_folder_list.insertItem(item_count, folder)
            item_count += 1

    def validatePage(self):
        if self.cloud_folder_list.currentItem():
            self.cloud_folder_line.setText(self.cloud_folder_list.currentItem().text())
        if self.cloud_root_override:
            self.cloud_folder_line.setText(self.cloud_root_override)
        return super().validatePage()


class LatusFolderPage(QtWidgets.QWizardPage):

    def __init__(self):
        super().__init__()
        self.latus_folder_box = QtWidgets.QLineEdit()
        self.latus_folder_box.setReadOnly(True)

        self.setTitle("Latus folder")
        self.setSubTitle("This is the Latus folder on your computer.  You may edit this path if you wish.")

        self.latus_folder_box.show()

        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.latus_folder_box, 0, 1)
        self.setLayout(layout)

        self.registerField(LATUS_FOLDER_FIELD_STRING, self.latus_folder_box)

    def initializePage(self):
        latus_folder = latus.wizard.latus_folder_from_cloud_folder(self.field(CLOUD_FOLDER_FIELD_STRING))
        self.latus_folder_box.setText(latus_folder)


class LatusKeyPage(QtWidgets.QWizardPage):

    complete_trigger = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()

        self.setTitle("Latus key")

        self.prior_is_complete = False

        self.latus_key_line = QtWidgets.QLineEdit()  # non-visible
        self.registerField(LATUS_KEY_FIELD_STRING, self.latus_key_line)
        self.setField(LATUS_KEY_FIELD_STRING, None)

    def initializePage(self):

        self.setTitle('Latus Key Setup')

        cloud_folder_field = self.field(CLOUD_FOLDER_FIELD_STRING)
        cloud_folders = latus.folders.CloudFolders(cloud_folder_field)
        existing_nodes = latus.nodedb.get_existing_nodes(cloud_folders.nodes)
        latus.logger.log.info('existing nodes: %s' % str(existing_nodes))
        if len(existing_nodes) < 1:
            latus_key = latus.crypto.new_key().decode()
            latus.logger.log.info('new latus key')
            self.setField(LATUS_KEY_FIELD_STRING, latus_key)
            self.setSubTitle('This is the first computer you are adding to Latus.  The Latus key has been created.')
        else:
            key_folder = latus.folders.CloudFolders(self.field(CLOUD_FOLDER_FIELD_STRING))
            latus.key_management.request_key(self.field(NODE_ID_FIELD_STRING), key_folder.keys)
            self.setSubTitle('Please go to one of your other computers running Latus and accept the key request.')

    # controls the if the 'next' button is enabled or not
    def isComplete(self):
        return self.field(LATUS_KEY_FIELD_STRING) is not None


class ConclusionPage(QtWidgets.QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Congratulations - Latus setup is now complete!")


if __name__ == '__main__':

    import sys
    import logging

    if len(sys.argv) < 2:
        data_folder = os.path.join('temp', 'wizardgui')
    else:
        data_folder = sys.argv[1]

    latus.logger.init(data_folder)
    latus.logger.set_console_log_level(logging.INFO)
    latus.logger.set_file_log_level(logging.DEBUG)

    latus.logger.log.info('data_folder : %s' % data_folder)

    app = QtWidgets.QApplication(sys.argv)
    app_gui_wizard = GUIWizard(data_folder)
    app_gui_wizard.exec_()
    my_pref = latus.preferences.Preferences(data_folder)
    print(my_pref.get_db_path())
    print(my_pref.get_node_id())
    print(my_pref.get_cloud_root())
    print(my_pref.get_latus_folder())
    print(my_pref.get_crypto_key_string())
    sys.exit()
