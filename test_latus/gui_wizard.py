
import os
import shutil

from PyQt5 import QtWidgets, QtCore

import latus.gui_wizard
import latus.util
import latus.logger

import test_latus.create_files

def get_gui_wizard_root():
    return os.path.join(test_latus.create_files.get_data_root(), "gui_wizard")

if os.path.exists(get_gui_wizard_root()):
    shutil.rmtree(get_gui_wizard_root())

log_folder = os.path.join(get_gui_wizard_root(), 'log')
latus.util.make_dirs(log_folder)
latus.logger.init(log_folder)

latus.logger.log.info('test_gui_wizard : start')

app_data_folder = os.path.join(get_gui_wizard_root(), 'app_data_folder', 'latus')

app = QtWidgets.QApplication([])
app_gui_wizard = latus.gui_wizard.GUIWizard(app_data_folder)
app_gui_wizard.exec_()