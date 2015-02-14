
from PyQt5 import QtGui, QtWidgets, QtCore

import latus.wizard


def create_intro_page():
    page = QtWidgets.QWizardPage()
    page.setTitle("Latus Setup Wizard")

    label = QtWidgets.QLabel("This will guide you through the Latus setup process.")
    label.setWordWrap(True)

    layout = QtWidgets.QVBoxLayout()
    layout.addWidget(label)
    page.setLayout(layout)

    return page


def create_cloud_folder_selection_page(folder_wizard):
    page = QtWidgets.QWizardPage()
    page.setTitle("Cloud storage folder")
    page.setSubTitle("Please select the cloud storage folder on your computer (for example: Dropbox, Microsoft's "
                     "OneDrive, Google Drive, etc.):")

    cloud_folders = folder_wizard.find_folders()

    cloud_folder_list = QtWidgets.QListView()
    model = QtGui.QStandardItemModel(cloud_folder_list)

    for cloud_folder in cloud_folders:
        item = QtGui.QStandardItem(cloud_folder)
        item.setCheckable(True)
        model.appendRow(item)

    cloud_folder_list.setModel(model)
    cloud_folder_list.show()

    layout = QtWidgets.QGridLayout()
    layout.addWidget(cloud_folder_list, 0, 1)
    page.setLayout(layout)

    return page


def create_latus_folder_selection_page(folder_wizard):
    page = QtWidgets.QWizardPage()
    page.setTitle("Latus folder")
    page.setSubTitle("This is the Latus folder on your computer:")

    latus_folder_path = QtWidgets.QLabel(folder_wizard.latus_folder())

    latus_folder_path.show()

    layout = QtWidgets.QGridLayout()
    layout.addWidget(latus_folder_path, 0, 1)
    page.setLayout(layout)

    return page

def create_conclusion_page():
    page = QtWidgets.QWizardPage()
    page.setTitle("Complete!")

    label = QtWidgets.QLabel("Latus setup is now complete!")
    label.setWordWrap(True)

    layout = QtWidgets.QVBoxLayout()
    layout.addWidget(label)
    page.setLayout(layout)

    return page


if __name__ == '__main__':

    import sys

    app = QtWidgets.QApplication(sys.argv)

    folder_wizard = latus.wizard.FolderWizard()

    wizard = QtWidgets.QWizard()
    wizard.addPage(create_intro_page())
    wizard.addPage(create_cloud_folder_selection_page(folder_wizard))
    wizard.addPage(create_latus_folder_selection_page(folder_wizard))
    wizard.addPage(create_conclusion_page())

    wizard.setWindowTitle("")
    wizard.show()

    sys.exit(wizard.exec_())