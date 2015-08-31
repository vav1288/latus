
import getpass
import json
import datetime
import platform


def write_latus_key_to_file(latus_key, latus_key_file_path):
    with open(latus_key_file_path, 'w') as f:
        key_record = {'key': latus_key.decode("utf-8"),
                      'timestamp': str(datetime.datetime.utcnow()),
                      'user': getpass.getuser(),
                      'computer': platform.node()}
        json.dump(key_record, f)


def read_latus_key(latus_key_file_path):
    with open(latus_key_file_path, 'r') as f:
        key = json.load(f)
    return key

