
import os
import getpass
import json
import datetime
import platform

import latus.const
import latus.logger

from PyQt5.QtWidgets import QFileDialog, QApplication


def write_latus_key_gui(key):
    dialog_return = QFileDialog.getSaveFileName(caption='Save Latus key file:',
                                                directory=os.path.join(os.getcwd(), getpass.getuser() + latus.const.LATUS_KEY_FILE_EXT),
                                                filter=latus.const.LATUS_KEY_FILE_EXT)
    if dialog_return and len(dialog_return) > 0:
        key_file_path = dialog_return[0]
        if key_file_path and len(key_file_path) > 0:
            write_latus_key_to_file(key, key_file_path)
            return key_file_path
    latus.logger.log.warn('key_file_path not provided by dialog box')
    return None


def read_latus_key_gui():
    key = None
    key_file_name = QFileDialog.getOpenFileName(None, 'Latus key file:',
                                                filter=latus.const.LATUS_KEY_FILE_EXT)
    if key_file_name and len(key_file_name[0]) > 0:
        key_record = read_latus_key_from_file(key_file_name[0])
        if key_record:
            key = key_record['key']
    return key


def write_latus_key_to_file(latus_key, latus_key_file_path):
    latus.logger.log.info('writing latus key %s to %s' % (latus_key, latus_key_file_path))
    with open(latus_key_file_path, 'w') as f:
        key_record = {'key': latus_key,
                      'timestamp': str(datetime.datetime.utcnow()),
                      'user': getpass.getuser(),
                      'computer': platform.node()}
        json.dump(key_record, f)


def read_latus_key_from_file(latus_key_file_path):
    with open(latus_key_file_path, 'r') as f:
        key = json.load(f)
    return key

if __name__ == '__main__':
    latus.logger.init('temp')
    print(latus.logger.get_log_folder())
    app = QApplication([''])
    write_latus_key_gui(b'dummy_key')