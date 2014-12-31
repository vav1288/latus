
import os
import json
import datetime
import cryptography.fernet
import latus.util


def new_key():
    return cryptography.fernet.Fernet.generate_key()

class CryptoFile():

    def __init__(self, path):
        self.__path = path

    def save(self, key):
        """
        save key to a file
        :param key: key as bytes
        :return: True on success, False on error
        """
        dt = datetime.datetime.now()
        key_info = {'id': latus.util.get_latus_guid(), 'cryptokey': key, 'timestamp': str(dt)}
        with open(self.__path, 'w') as f:
            json.dump(key_info, f, indent=4)  # todo: stopped here
        return True

    def load_key(self):
        with open(self.__path) as f:
            key_info = json.load(f)
        return key_info

class Crypto():
    def __init__(self, key, verbose = False):
        self.__key = key
        self.__verbose = verbose
        self.__fernet = cryptography.fernet.Fernet(self.__key)

    def compress(self, cwd, in_path, out_path):
        with open(os.path.join(cwd, in_path), 'rb') as in_file:
            token = self.__fernet.encrypt(in_file.read())
            with open(out_path, 'wb') as out_file:
                out_file.write(token)

    def expand(self, cwd, in_path, out_path):
        success = False
        with open(os.path.join(cwd, in_path), 'rb') as in_file:
            try:
                b = self.__fernet.decrypt(in_file.read())
            except cryptography.fernet.InvalidToken:
                b = None
            if b:
                with open(out_path, 'wb') as out_file:
                    out_file.write(b)
                    success = True
            return success



