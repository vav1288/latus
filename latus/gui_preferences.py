
import os
import logging
import appdirs

from PyQt5.QtWidgets import QLabel, QDialogButtonBox, QVBoxLayout, QLineEdit, QGridLayout, QFileDialog, QDialog, \
    QGroupBox, QCheckBox, QRadioButton, QHBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.Qt import QApplication

import latus
import latus.logger
import latus.csp.sync_csp
import latus.preferences
import latus.util
import latus.crypto
import latus.gui_wizard
from latus import nodedb
import latus.csp.cloud_folders


class LineUI:
    """
    Set up the folder widgets
    """
    def __init__(self, name, value, method=None, button_text='Select...'):
        self.label = QLabel(name + ':')
        self.line = QLineEdit(value)
        self.line.setMinimumWidth(600)  # swag
        self.select_button = QDialogButtonBox()
        self.line.setReadOnly(True)  # guide user via dialog boxes - don't allow them to just type anything in
        if method:
            self.select_button.addButton(button_text, QDialogButtonBox.AcceptRole)
            self.select_button.accepted.connect(method)

    def layout(self, grid, column):
        grid.addWidget(self.label, column, 0)
        grid.addWidget(self.line, column, 1)
        grid.addWidget(self.select_button, column, 2)

    def get(self):
        return self.line.text()


class PreferencesDialog(QDialog):
    def __init__(self, latus_appdata_folder):
        latus.logger.log.info('starting PreferencesDialog')
        latus.logger.log.info('preferences folder : %s' % latus_appdata_folder)

        # todo: self.pref and preferences are redundant - get rid of one
        self.pref = latus.preferences.Preferences(latus_appdata_folder)
        cloud_folders = latus.csp.cloud_folders.CloudFolders(self.pref.get_cloud_root())
        self.node_db = nodedb.NodeDB(cloud_folders.nodes, self.pref.get_node_id())

        super().__init__()
        self.blank = QLabel('')
        overall_layout = QVBoxLayout()
        col = 0
        row = 1

        folder_preferences_group_box = QGroupBox("Folder Preferences")
        folder_preferences_layout = QGridLayout()
        headers = ['Folder', 'Encrypted', 'Shared', 'Cloud']
        for header in headers:
            folder_preferences_layout.addWidget(QLabel(header), 0, col)
            col += 1
        self.folders = latus.util.get_latus_folders(self.pref)
        if len(self.folders) > 0:
            self.check_boxes = {}
            for folder in self.folders:
                folder_preferences_layout.addWidget(QLabel(folder))
                col = 1
                self.check_boxes[folder] = []
                partial_folder = os.path.relpath(folder, self.pref.get_latus_folder())
                for attribute in self.node_db.get_folder_preferences_from_folder(partial_folder):
                    ss = Qt.Unchecked
                    if attribute:
                        ss = Qt.Checked
                    cb = QCheckBox()
                    cb.setCheckState(ss)
                    folder_preferences_layout.addWidget(cb, row, col)
                    self.check_boxes[folder].append(cb)
                    col += 1
                row += 1
        else:
            folder_preferences_layout.addWidget(QLabel("(No Folders Created Yet)"))
        folder_preferences_group_box.setLayout(folder_preferences_layout)

        self.cloud_mode = self.pref.get_cloud_mode()
        cloud_preferences_group_box = QGroupBox("Cloud Preferences")
        cloud_preferences_layout = QHBoxLayout()
        radio_button_aws = QRadioButton("AWS")
        radio_button_aws.setChecked(self.cloud_mode == 'aws')
        radio_button_aws.toggled.connect(self.radio_button_aws)
        cloud_preferences_layout.addWidget(radio_button_aws)
        radio_button_csp = QRadioButton("Cloud Storage Provider")
        radio_button_csp.setChecked(self.cloud_mode == 'csp')
        radio_button_csp.toggled.connect(self.radio_button_csp)
        cloud_preferences_layout.addWidget(radio_button_csp)
        cloud_preferences_group_box.setLayout(cloud_preferences_layout)

        folder_locations_group_box = QGroupBox("Folder Locations")
        folder_locations_layout = QGridLayout()
        self.latus_folder = LineUI('Latus Folder', self.pref.get_latus_folder(), self.new_folder)
        self.cloud_folder = LineUI('Cloud Folder', self.pref.get_cloud_root(), self.new_folder)

        support_preferences_group_box = QGroupBox("Support Preferences")
        support_preferences_layout = QGridLayout()
        headers = ['Option', 'Enabled']
        col = 0
        for header in headers:
            support_preferences_layout.addWidget(QLabel(header), 0, col)
            col += 1
        row = 1
        self.support_selections = []
        self.support_selections.append({'str': 'Check For New Version', 'set': self.pref.set_check_new_version, 'get': self.pref.get_check_new_version})
        self.support_selections.append({'str': 'Upload Issue Logs', 'set': self.pref.set_upload_logs, 'get': self.pref.get_upload_logs})
        self.support_selections.append({'str': 'Upload Usage Information', 'set': self.pref.set_upload_usage, 'get': self.pref.get_upload_usage})
        for ss in self.support_selections:
            support_preferences_layout.addWidget(QLabel(ss['str']), row, 0)
            ss['cb'] = QCheckBox()
            if ss['get']():
                ss['cb'].setCheckState(Qt.Checked)
            support_preferences_layout.addWidget(ss['cb'], row, 1)
            row += 1
        support_preferences_group_box.setLayout(support_preferences_layout)

        ok_buttonBox = QDialogButtonBox(QDialogButtonBox.Ok)
        ok_buttonBox.accepted.connect(self.ok)
        cancel_buttonBox = QDialogButtonBox(QDialogButtonBox.Cancel)
        cancel_buttonBox.rejected.connect(self.cancel)

        self.latus_folder.layout(folder_locations_layout, row)
        self.cloud_folder.layout(folder_locations_layout, row + 1)
        folder_locations_group_box.setLayout(folder_locations_layout)

        overall_layout.addWidget(folder_preferences_group_box)
        overall_layout.addWidget(cloud_preferences_group_box)
        overall_layout.addWidget(folder_locations_group_box)
        overall_layout.addWidget(support_preferences_group_box)

        # todo: alignment
        overall_layout.addWidget(ok_buttonBox)     # , alignment=QtCore.Qt.AlignLeft)
        overall_layout.addWidget(cancel_buttonBox) # , alignment=QtCore.Qt.AlignLeft)

        self.setLayout(overall_layout)

        self.setWindowTitle("Preferences")

    def radio_button_aws(self, state):
        if state:
            self.cloud_mode = 'aws'

    def radio_button_csp(self, state):
        if state:
            self.cloud_mode = 'csp'

    def ok(self):
        if self.pref.get_latus_folder() != self.latus_folder.get():
            latus.logger.log.info('new latus folder location "%s"' % self.latus_folder.get())
            self.pref.set_latus_folder(self.latus_folder.get())
        if self.pref.get_cloud_root() != self.cloud_folder.get():
            latus.logger.log.info('new cloud folder location "%s"' % self.cloud_folder.get())
            self.pref.set_cloud_root(self.cloud_folder.get())
        for folder in self.folders:
            cb_states = tuple([cb.isChecked() for cb in self.check_boxes[folder]])
            current_preferences = self.node_db.get_folder_preferences_from_folder(folder)
            if current_preferences != cb_states:
                latus.logger.log.info('new folder preferences for %s : %s --> %s' % (folder, str(current_preferences), str(cb_states)))
                self.node_db.set_folder_preferences(folder, cb_states[0], cb_states[1], cb_states[2])
        for ss in self.support_selections:
            if ss['cb'].isChecked() != ss['get']():
                latus.logger.log.info('new support preferences for %s : %s --> %s' % (ss['str'], str(ss['get']()), str(ss['cb'].isChecked())))
                ss['set'](ss['cb'].isChecked())
        if self.pref.get_cloud_mode() != self.cloud_mode:
            latus.logger.log.info('new cloud mode "%s"' % self.cloud_mode)
            self.pref.set_cloud_mode(self.cloud_mode)
        self.close()

    def cancel(self):
        self.close()

    def new_folder(self):
        f = QFileDialog.getExistingDirectory()
        return f


def main():
    import sys

    app = QApplication(sys.argv)

    app_data_folder = appdirs.user_config_dir(latus.__application_name__, latus.__author__)
    preferences = latus.preferences.Preferences(app_data_folder)
    if not preferences.get_node_id():
        preferences.set_node_id(latus.util.new_node_id())
    preferences_dialog = PreferencesDialog(app_data_folder)
    preferences_dialog.show()
    preferences_dialog.exec_()

if __name__ == '__main__':
    latus.logger.init(None)
    latus.logger.set_console_log_level(logging.INFO)
    main()
