
import time

from PyQt5 import QtGui, QtWidgets, QtCore

import latus.wizard
import latus.config

CLOUD_FOLDER_STRING = 'cloud_folder'
LATUS_FOLDER_STRING = 'latus_folder'

class GUIWizard(QtWidgets.QWizard):

    def __init__(self):
        super().__init__()

        self.folder_wizard = latus.wizard.FolderWizard()

        self.addPage(IntroPage())
        self.addPage(CloudFolderPage(self.folder_wizard))
        self.addPage(LatusFolderPage())
        self.addPage(ConclusionPage())
        self.setWindowTitle("Latus Setup")
        self.show()

    def accept(self):
        cloud_folder = self.field(CLOUD_FOLDER_STRING)
        if cloud_folder:
            print(CLOUD_FOLDER_STRING, cloud_folder)
        latus_folder = self.field(LATUS_FOLDER_STRING)
        if latus_folder:
            print(LATUS_FOLDER_STRING, latus_folder)
        super(GUIWizard, self).accept()

    def done(self, result):
        self.folder_wizard.request_exit()
        super(GUIWizard, self).done(result)


class IntroPage(QtWidgets.QWizardPage):

    def __init__(self):
        super().__init__()
        self.setTitle("Latus Setup Wizard")

        label = QtWidgets.QLabel("This will guide you through the Latus setup process.")
        label.setWordWrap(True)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(label)
        self.setLayout(layout)


class CloudFolderPage(QtWidgets.QWizardPage):

    def __init__(self, folder_wizard):
        super().__init__()
        self.cloud_folder_list = QtWidgets.QListWidget()
        self.folder_wizard = folder_wizard
        self.cloud_folders = []
        self.prior_time = 0

        self.folder_wizard.set_found_alert(self.wizard_alert)
        self.folder_wizard.set_progress(self.progress)
        self.folder_wizard.start()

        self.setTitle("Cloud storage folder")
        self.setSubTitle("We will now attempt to automatically find your cloud storage folder.  This is the folder you "
                         "use for Dropbox, Microsoft's OneDrive, Google Drive, etc.\n\nYou don't have to wait for the "
                         "search to complete.  Once the cloud storage folder is displayed you can select it and go to "
                         "the next page.  Note that it may take a while to search your entire computer.")

        self.cloud_folder_list.show()

        self.progressbar = QtWidgets.QLineEdit()
        self.progressbar.setReadOnly(True)
        self.progressbar.setText('...')

        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.progressbar, 0, 0)
        layout.addWidget(self.cloud_folder_list, 1, 0)
        self.setLayout(layout)

        # use this for the value that's been selected
        self.cloud_folder_line = QtWidgets.QLineEdit()
        self.registerField(CLOUD_FOLDER_STRING, self.cloud_folder_line)

    def progress(self, d):
        t = time.time()
        if d:
            rate = 0.25  # if this rate is too frequent, Python (or PyQT) will crash ... I don't know why
            if t - self.prior_time > rate:
                self.progressbar.setText('Searching: ' + d)
                self.progressbar.setCursorPosition(0)
                self.prior_time = t
        else:
            self.progressbar.setText('Search complete.  Select a path below.')

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
        self.setSubTitle("This is the Latus folder on your computer:")

        self.latus_folder_box.show()

        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.latus_folder_box, 0, 1)
        self.setLayout(layout)

        self.registerField(LATUS_FOLDER_STRING, self.latus_folder_box)

    def initializePage(self):
        latus_folder = latus.wizard.latus_folder_from_cloud_folder(self.field('cloud_folder'))
        self.latus_folder_box.setText(latus_folder)


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
    sys.exit(app_gui_wizard.exec_())
