
import getpass
import json
import datetime
import platform

from PyQt5 import QtWidgets


def write_latus_key_gui(key):
    save_file_name = QtWidgets.QFileDialog.getSaveFileName(None, 'Save Latus key file:', filter='*.lky')
    if save_file_name and len(save_file_name[0]) > 0:
        key_file_path = save_file_name[0]
        write_latus_key_to_file(key, key_file_path)


def read_latus_key_gui():
    key = None
    key_file_name = QtWidgets.QFileDialog.getOpenFileName(None, 'Latus key file:', filter='*.lky')
    if key_file_name and len(key_file_name[0]) > 0:
        key_record = read_latus_key_from_file(key_file_name[0])
        if key_record:
            key = key_record['key']
    return key


def write_latus_key_to_file(latus_key, latus_key_file_path):
    with open(latus_key_file_path, 'w') as f:
        key_record = {'key': latus_key.decode("utf-8"),
                      'timestamp': str(datetime.datetime.utcnow()),
                      'user': getpass.getuser(),
                      'computer': platform.node()}
        json.dump(key_record, f)


def read_latus_key_from_file(latus_key_file_path):
    with open(latus_key_file_path, 'r') as f:
        key = json.load(f)
    return key

