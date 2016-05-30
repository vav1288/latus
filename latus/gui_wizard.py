
import time
import os

from PySide import *
from PySide.QtCore import Signal as pyqtSignal

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
LATUS_KEY_FIELD_STRING = 'latus_key'


class GUIWizard(QtGui.QWizard):

    # cloud_folder parameter generally only used for testing
    def __init__(self, app_data_folder, cloud_root_override=None):
        super().__init__()
        self.app_data_folder = app_data_folder
        latus.logger.log.info('starting GUIWizard : app_data_folder : %s' % app_data_folder)

        self.folder_wizard = latus.wizard.FolderWizard()

        self.addPage(IntroPage())
        self.addPage(CloudRootPage(self.folder_wizard, cloud_root_override))
        self.addPage(LatusFolderPage())
        self.addPage(LatusKeyPage(app_data_folder))
        self.addPage(ConclusionPage())
        self.setWindowTitle("Latus Setup")
        self.show()

    def done(self, result):
        self.folder_wizard.request_exit()
        super().done(result)

    def accept(self):
        latus.logger.log.info('accept')
        pref = latus.preferences.Preferences(self.app_data_folder)
        pref.set_cloud_root(self.field(CLOUD_FOLDER_FIELD_STRING))
        pref.set_latus_folder(self.field(LATUS_FOLDER_FIELD_STRING))
        pref.set_crypto_key(self.field(LATUS_KEY_FIELD_STRING))
        if not pref.get_node_id():
            pref.set_node_id(latus.util.new_node_id())
        folders = latus.folders.CloudFolders(pref.get_cloud_root())
        node = latus.nodedb.NodeDB(folders.nodes, pref.get_node_id(), write_flag=True)
        node.set_all(pref.get_node_id())

        # todo: write node info out to 'state' that this node is on Latus, even if it hasn't sync'd yet

        super().accept()


class IntroPage(QtGui.QWizardPage):

    def __init__(self):
        super().__init__()
        self.setTitle("Latus Setup Wizard")

        label = QtGui.QLabel("This will guide you through the Latus setup process.  Please make sure you are "
                                 "connected to the internet and your cloud storage application (such as Dropbox, "
                                 "Microsoft's OneDrive, Google Drive, etc.) is running.")
        label.setWordWrap(True)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(label)
        self.setLayout(layout)


class WizardFolderListWidget(QtGui.QListWidget):
    def __init__(self, change_method):
        self.change_method = change_method
        super().__init__()

    def selectionChanged(self, a, b):
        self.change_method()
        super().selectionChanged(a, b)


class CloudRootPage(QtGui.QWizardPage):

    complete_trigger = pyqtSignal()
    selection_trigger = pyqtSignal()

    def __init__(self, folder_wizard, cloud_root_override=None):
        super().__init__()



        self.prior_time = 0
        self.prior_is_complete = None

        self.cloud_folder_list = WizardFolderListWidget(self.isComplete)
        self.cloud_folder_list.SelectionMode(QtGui.QAbstractItemView.SingleSelection)

        self.folder_wizard = folder_wizard
        self.cloud_root_override = cloud_root_override

        self.progress_line = QtGui.QLineEdit()
        self.progress_line.setReadOnly(True)

        self.progress_line.setText('...')

        self.folder_wizard.set_found_alert(self.wizard_alert)
        self.folder_wizard.set_progress(self.progress_method)
        self.folder_wizard.start()

        self.setTitle("Cloud storage folder")
        self.setSubTitle("Please specify the folder you use for Dropbox, Microsoft's OneDrive, Google Drive, "
                         "etc.\n\n"
                         "Your computer is automatically being scanned for this folder.  Once your cloud storage folder"
                         " is shown, please select it and hit 'Next'.  Alternatively, you can click the button below"
                         " to manually provide the cloud storage path.")

        self.manual_button = QtGui.QPushButton()
        self.manual_button.setText('Click here to manually provide the cloud storage path')
        self.manual_button.pressed.connect(self.manual_cloud_folder_entry)

        layout = QtGui.QGridLayout()
        layout.addWidget(self.cloud_folder_list, 0, 0)
        layout.addWidget(self.progress_line, 1, 0)
        layout.addWidget(self.manual_button, 2, 0)

        self.setLayout(layout)

        # use this for the value that's been selected
        self.cloud_folder_line = QtGui.QLineEdit()
        self.registerField(CLOUD_FOLDER_FIELD_STRING, self.cloud_folder_line)

        self.cloud_folder_list.show()

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
            rate = 1.0
            if t - self.prior_time > rate:
                self.progress_line.setText('Searching: ' + folder)
                self.progress_line.setCursorPosition(0)  # left justify
                self.prior_time = t
        else:
            self.progress_line.setText('Search complete.')

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

    def manual_cloud_folder_entry(self):
        cloud_folder = QtGui.QFileDialog.getExistingDirectory(None, 'Select a folder:', None, QtWidgets.QFileDialog.ShowDirsOnly)
        self.cloud_folder_line.setText(cloud_folder)
        self.cloud_folder_list.insertItem(0, cloud_folder)
        self.cloud_folder_list.setCurrentItem(self.cloud_folder_list.item(0))
        # todo: figure out how to just skip to the next page w/o having the user have to click on 'next'


class LatusFolderPage(QtGui.QWizardPage):
    def __init__(self):
        super().__init__()
        self.latus_folder_box = QtGui.QLineEdit()
        self.latus_folder_box.setReadOnly(True)

        self.setTitle("Latus folder")
        self.setSubTitle("This is the Latus folder on your computer.  You may edit this path if you wish.")

        self.latus_folder_box.show()

        layout = QtGui.QGridLayout()
        layout.addWidget(self.latus_folder_box, 0, 1)
        self.setLayout(layout)

        self.registerField(LATUS_FOLDER_FIELD_STRING, self.latus_folder_box)

    def initializePage(self):
        latus_folder = latus.wizard.latus_folder_from_cloud_folder(self.field(CLOUD_FOLDER_FIELD_STRING))
        self.latus_folder_box.setText(latus_folder)


class LatusKeyPage(QtGui.QWizardPage):

    def __init__(self, app_data_folder):
        super().__init__()
        self.app_data_folder = app_data_folder
        self.key_widget = QtGui.QLabel(LATUS_KEY_FIELD_STRING)
        self.registerField(LATUS_KEY_FIELD_STRING, self.key_widget)
        self.setTitle("Latus key")

    def initializePage(self):

        self.setTitle('Latus Key Setup')

        first_time = True

        cloud_folder_field = self.field(CLOUD_FOLDER_FIELD_STRING)
        cloud_folders = latus.folders.CloudFolders(cloud_folder_field)
        existing_nodes = latus.nodedb.get_existing_nodes(cloud_folders.nodes)
        latus.logger.log.info('existing nodes: %s' % str(existing_nodes))
        if len(existing_nodes) > 0:
            first_time = False
        latus.logger.log.info('first_time: %s' % first_time)

        first_time_intro = QtGui.QLabel()
        first_time_intro.setWordWrap(True)
        first_time_intro_text = \
            "This seems to be your first time setting up Latus.  We will now create a new Latus key " \
            "for you.  You will use this key to 'connect' all of your computers to Latus.  You will also be " \
            "prompted to write this key to a USB stick or some other secure medium you can later take " \
            "to your other computers in order to set them up."
        first_time_intro.setText(first_time_intro_text)

        not_first_time_intro = QtGui.QLabel()
        not_first_time_intro.setWordWrap(True)
        not_first_time_intro_text = \
            "You seem to already be a Latus user on your other computers.  When you set up Latus " \
            "previously you created a Latus key and wrote it to a USB stick or some" \
            "other secure medium. Please use that now to load into this computer.  Alternately, " \
            "go to one of your other computers running Latus and write the Latus " \
            "key to a new USB stick."
        not_first_time_intro.setText(not_first_time_intro_text)

        restart_latus_key_setup = QtGui.QLabel()
        restart_latus_key_setup.setWordWrap(True)
        restart_latus_key_setup_text = \
            "If you can't get to your previous key or any of your computers that already have Latus " \
            "installed, alternatively you can restart the setup process.  While this is not " \
            "recommended since you'll have to re-load they key on you all of our computers, you " \
            "may restart the Latus key setup now."
        restart_latus_key_setup.setText(restart_latus_key_setup_text)

        new_key_button = QtGui.QPushButton()
        new_key_button.setText('Create new Latus key')
        new_key_button.pressed.connect(self.new_latus_key)

        existing_key_button = QtGui.QPushButton()
        existing_key_button.setText('Load existing Latus key')
        existing_key_button.pressed.connect(self.existing_latus_key)

        restart_setup_button = QtGui.QPushButton()
        restart_setup_button.setText('Restart Latus key setup')
        restart_setup_button.pressed.connect(self.restart_latus_key_setup)

        layout = QtGui.QGridLayout()
        if first_time:
            layout.addWidget(first_time_intro, 0, 0)
            layout.addWidget(new_key_button, 1, 0)
        else:
            layout.addWidget(not_first_time_intro, 0, 0)
            layout.addWidget(existing_key_button, 1, 0)
            layout.addWidget(QtGui.QLabel(), 2, 0)  # spacer
            layout.addWidget(restart_latus_key_setup, 3, 0)
            layout.addWidget(restart_setup_button, 5, 0)
        self.setLayout(layout)

    def isComplete(self):
        return bool(self.field(LATUS_KEY_FIELD_STRING) and len(self.field(LATUS_KEY_FIELD_STRING)) > 0)

    def new_latus_key(self):
        new_key = latus.crypto.new_key()
        self.setField(LATUS_KEY_FIELD_STRING, new_key)
        latus.key_management.write_latus_key_gui(new_key)
        self.completeChanged.emit()

    def existing_latus_key(self):
        key = latus.key_management.read_latus_key_gui()
        if key:
            # todo: this seems to cause the message below to be logged, even though things seem work - figure out why
            # QWizard::setField: Couldn't write to property ''
            self.setField(LATUS_KEY_FIELD_STRING, key)
        self.completeChanged.emit()

    def restart_latus_key_setup(self):
        latus.logger.log.error('Not yet implemented.')
        print('Not yet implemented.')


class ConclusionPage(QtGui.QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Congratulations - Latus setup is now complete!")


if __name__ == '__main__':

    # a manual test of the Wizard

    import sys
    import shutil
    import logging

    def print_pref(pref):
        print('db_path : %s' % pref.get_db_path())
        print('node_id : %s' % pref.get_node_id())
        print('cloud_root : %s' % pref.get_cloud_root())
        print('latus_folder : %s' % pref.get_latus_folder())
        print('crypto_key : %s' % pref.get_crypto_key())

    if len(sys.argv) < 2:
        data_folder_root = os.path.join('temp', 'wizardgui')
        if os.path.exists(data_folder_root):
            shutil.rmtree(data_folder_root)
    else:
        data_folder_root = sys.argv[1]

    if os.path.exists(data_folder_root):
        error_string = 'error: %s must be empty - exiting' % data_folder_root
        print(error_string)
        sys.exit(error_string)

    data_folder_a = os.path.join(data_folder_root, 'a')
    cloud_folder = os.path.join(data_folder_root, 'cloud')
    os.makedirs(cloud_folder)  # both nodes should use this
    print('NOTE: make sure you select "%s" as the cloud folder in the GUI!!!' % os.path.abspath(cloud_folder))

    latus.logger.init(data_folder_a)
    latus.logger.set_console_log_level(logging.INFO)
    latus.logger.set_file_log_level(logging.DEBUG)

    latus.logger.log.info('data_folder : %s' % data_folder_a)

    my_pref_a = latus.preferences.Preferences(data_folder_a, True)

    # run once after init (no data)
    app = QtGui.QApplication(sys.argv)
    app_gui_wizard = GUIWizard(data_folder_a)
    app_gui_wizard.exec_()

    print_pref(my_pref_a)

    data_folder_b = os.path.join(data_folder_root, 'b')

    my_pref_b = latus.preferences.Preferences(data_folder_b, True)
    # run again to emulate a 2nd node
    app_gui_wizard = GUIWizard(data_folder_b)
    app_gui_wizard.exec_()

    print_pref(my_pref_b)

    sys.exit()
