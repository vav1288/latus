
import time
import os

from PyQt5 import QtGui, QtWidgets, QtCore

import latus.wizard
import latus.config
import latus.gui
import latus.sync
import latus.folders

CLOUD_FOLDER_FIELD_STRING = 'cloud_folder'
LATUS_FOLDER_FIELD_STRING = 'latus_folder'
KEY_FIELD_STRING = 'key'

class GUIWizard(QtWidgets.QWizard):

    NUM_PAGES = 6
    (IntroPageNumber, CloudFolderPageNumber, LatusFolderPageNumber, NewKeyPageNumber, ExistingKeyPageNumber,
     ConclusionPageNumber) = range(NUM_PAGES)

    def __init__(self):
        super().__init__()

        self.cloud_folder = None
        self.latus_folder = None
        self.folder_wizard = latus.wizard.FolderWizard()

        self.setPage(self.IntroPageNumber, IntroPage())
        self.setPage(self.CloudFolderPageNumber, CloudFolderPage(self.folder_wizard))
        self.setPage(self.LatusFolderPageNumber, LatusFolderPage())
        self.setPage(self.ExistingKeyPageNumber, ExistingKeyPage())
        self.setPage(self.NewKeyPageNumber, NewKeyPage())
        self.setPage(self.ConclusionPageNumber, ConclusionPage())
        self.setWindowTitle("Latus Setup")
        self.show()

    def accept(self):
        self.cloud_folder = self.field(CLOUD_FOLDER_FIELD_STRING)
        self.latus_folder = self.field(LATUS_FOLDER_FIELD_STRING)
        super().accept()

    def get_cloud_folder(self):
        return self.cloud_folder

    def get_latus_folder(self):
        return self.latus_folder

    def done(self, result):
        self.folder_wizard.request_exit()
        super().done(result)


class IntroPage(QtWidgets.QWizardPage):

    def __init__(self):
        super().__init__()
        self.setTitle("Latus Setup Wizard")

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


class CloudFolderPage(QtWidgets.QWizardPage):

    complete_trigger = QtCore.pyqtSignal()
    selection_trigger = QtCore.pyqtSignal()

    def __init__(self, folder_wizard):
        super().__init__()
        self.prior_time = 0
        self.prior_is_complete = None

        self.cloud_folder_list = WizardFolderListWidget(self.isComplete)
        self.cloud_folder_list.SelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

        self.folder_wizard = folder_wizard
        self.cloud_folders = []

        self.folder_wizard.set_found_alert(self.wizard_alert)
        self.folder_wizard.set_progress(self.progress_method)
        self.folder_wizard.start()

        self.setTitle("Cloud storage folder")
        self.setSubTitle("We will now attempt to automatically find your cloud storage folder.  This is the folder you "
                         "use for Dropbox, Microsoft's OneDrive, Google Drive, etc.\n\nOnce your cloud storage folder"
                         " is shown, please select it and hit 'Next'.")

        self.cloud_folder_list.show()

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
        return super().validatePage()


class LatusFolderPage(QtWidgets.QWizardPage):

    def __init__(self):
        super().__init__()
        self.latus_folder_box = QtWidgets.QLineEdit()
        self.latus_folder_box.setReadOnly(True)

        self.setTitle("Latus folder")
        self.setSubTitle("This is the default Latus folder on your computer:")

        self.latus_folder_box.show()

        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.latus_folder_box, 0, 1)
        self.setLayout(layout)

        self.registerField(LATUS_FOLDER_FIELD_STRING, self.latus_folder_box)

    def initializePage(self):
        latus_folder = latus.wizard.latus_folder_from_cloud_folder(self.field('cloud_folder'))
        self.latus_folder_box.setText(latus_folder)

    def nextId(self):
        cf = latus.folders.CloudFolders(self.field(CLOUD_FOLDER_FIELD_STRING))
        if os.path.exists(cf.latus):
            return GUIWizard.ExistingKeyPageNumber
        else:
            return GUIWizard.NewKeyPageNumber

class NewKeyPage(QtWidgets.QWizardPage):

    complete_trigger = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.prior_is_complete = None
        self.key_box = QtWidgets.QLineEdit()
        self.key_box.show()  # only show when we get a value

        self.setTitle("Latus key")
        self.setSubTitle("This will set up the Latus secret key.  Please make sure you keep this key secure.")

        self.generate_label = QtWidgets.QTextEdit()
        self.generate_label.setText('This is the first time using Latus.  Generate a my secret key.')
        self.generate_label.show()
        self.generate_button = QtWidgets.QDialogButtonBox()
        self.generate_button.addButton('Generate', QtWidgets.QDialogButtonBox.AcceptRole)
        self.generate_button.show()

        self.load_label = QtWidgets.QTextEdit()
        self.load_label.setText('I am already using Latus.  Load my secret key that was generated on another computer.')
        self.load_label.show()
        self.load_button = QtWidgets.QDialogButtonBox()
        self.load_button.addButton('Load', QtWidgets.QDialogButtonBox.AcceptRole)
        self.load_button.clicked.connect(self.load_key)
        self.load_button.show()

        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.generate_label, 0, 0)
        layout.addWidget(self.generate_button, 0, 1)
        layout.addWidget(self.load_label, 1, 0)
        layout.addWidget(self.load_button, 1, 1)
        layout.addWidget(self.key_box, 2, 0)
        self.setLayout(layout)

        self.registerField(KEY_FIELD_STRING, self.key_box)

    def initializePage(self):
        pass

    # controls the if the 'next' button is enabled or not
    def isComplete(self):
        if len(self.key_box.text()) > 0:
            is_complete = True
        else:
            is_complete = False
        if is_complete != self.prior_is_complete:
            self.prior_is_complete = is_complete
            self.complete_trigger.connect(self.completeChanged)
            self.complete_trigger.emit()  # inform the window to update the 'next' button state (call this method)
        return is_complete

    def load_key(self):
        self.isComplete()


class ExistingKeyPage(QtWidgets.QWizardPage):

    complete_trigger = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.prior_is_complete = None
        self.key_box = QtWidgets.QLineEdit()
        self.key_box.show()  # only show when we get a value

        self.setTitle("Latus key")
        self.setSubTitle("We now need to get your existing Latus key.  Please go to a computer already running Latus, "
                         "right-click the Latus icon in the tool bar, and select 'Export Key'.  Export the key "
                         "to a USB drive, bring it to this computer, and hit 'Import Key' below.")

        self.load_button = QtWidgets.QDialogButtonBox()
        self.load_button.addButton('Import Key', QtWidgets.QDialogButtonBox.AcceptRole)
        self.load_button.clicked.connect(self.load_key)
        self.load_button.show()

        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.load_button, 1, 0)
        layout.addWidget(self.key_box, 1, 4)
        self.setLayout(layout)

        self.registerField(KEY_FIELD_STRING, self.key_box)

    def initializePage(self):
        pass

    # controls the if the 'next' button is enabled or not
    def isComplete(self):
        if len(self.key_box.text()) > 0:
            is_complete = True
        else:
            is_complete = False
        if is_complete != self.prior_is_complete:
            self.prior_is_complete = is_complete
            self.complete_trigger.connect(self.completeChanged)
            self.complete_trigger.emit()  # inform the window to update the 'next' button state (call this method)
        return is_complete

    def load_key(self):
        self.isComplete()


class ConclusionPage(QtWidgets.QWizardPage):
    def __init__(self):
        super().__init__()

        self.setTitle("Complete!")

        label = QtWidgets.QLabel("Latus setup is now complete!")
        label.setWordWrap(True)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(label)
        self.setLayout(layout)


if __name__ == '__main__':

    import sys

    app = QtWidgets.QApplication(sys.argv)
    app_gui_wizard = GUIWizard()
    app_gui_wizard.exec_()
    print(app_gui_wizard.get_cloud_folder())
    print(app_gui_wizard.get_latus_folder())
    sys.exit()
