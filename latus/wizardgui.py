
from PyQt5 import QtGui, QtWidgets, QtCore

import latus.wizard
import latus.config


class GUIWizard(QtWidgets.QWizard):

    def __init__(self):
        super(GUIWizard, self).__init__()
        app_folder_wizard = latus.wizard.FolderWizard()
        self.cloud_folder_list = QtWidgets.QListWidget()

        self.addPage(IntroPage())
        self.addPage(CloudFolderPage(app_folder_wizard, self.cloud_folder_list))
        self.addPage(LatusFolderPage(app_folder_wizard, self.cloud_folder_list))
        self.addPage(ConclusionPage())
        self.setWindowTitle("")
        self.show()

    def accept(self):
        print(self.cloud_folder_list.currentItem().text())
        print(self.field('latus_folder'))
        super(GUIWizard, self).accept()


class IntroPage(QtWidgets.QWizardPage):

    def __init__(self):
        super(IntroPage, self).__init__()
        self.setTitle("Latus Setup Wizard")

        label = QtWidgets.QLabel("This will guide you through the Latus setup process.")
        label.setWordWrap(True)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(label)
        self.setLayout(layout)


class CloudFolderPage(QtWidgets.QWizardPage):

    def __init__(self, folder_wizard, cloud_folder_list):
        super(CloudFolderPage, self).__init__()
        self.folder_wizard = folder_wizard
        self.cloud_folder_list = cloud_folder_list
        self.cloud_folders = []

        self.setTitle("Cloud storage folder")
        self.setSubTitle("Please select the cloud storage folder on your computer (for example: Dropbox, Microsoft's "
                         "OneDrive, Google Drive, etc.):")

        self.cloud_folder_list.show()

        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.cloud_folder_list, 0, 1)
        self.setLayout(layout)

    def initializePage(self):
        item_count = 0
        for folder in self.folder_wizard.find_cloud_folders():
            item = QtWidgets.QListWidgetItem()
            item.setText(folder)
            self.cloud_folder_list.insertItem(item_count, item)
            item_count += 1


class LatusFolderPage(QtWidgets.QWizardPage):

    def __init__(self, folder_wizard, cloud_folder_list):
        super(LatusFolderPage, self).__init__()
        self.folder_wizard = folder_wizard
        self.cloud_folder_list = cloud_folder_list

        self.setTitle("Latus folder")
        self.setSubTitle("This is the Latus folder on your computer:")

        self.latus_folder_box = QtWidgets.QLineEdit()
        self.latus_folder_box.setReadOnly(True)
        self.latus_folder_box.show()

        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.latus_folder_box, 0, 1)
        self.setLayout(layout)

    def initializePage(self):
        latus_folder = latus.wizard.latus_folder_from_cloud_folder(self.cloud_folder_list.currentItem().text())
        self.latus_folder_box.setText(latus_folder)
        self.registerField('latus_folder', self.latus_folder_box)

class ConclusionPage(QtWidgets.QWizardPage):
    def __init__(self):
        super(ConclusionPage, self).__init__()

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