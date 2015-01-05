
import os
import json
import datetime
import cryptography.fernet
import latus.util
import latus.logger


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
        dt = datetime.datetime.utcnow()
        key_info = {'latusid': latus.util.get_latus_guid(),  # ensure no collisions or aliasing with other user files
                    'cryptokey': key,
                    'timestamp': str(dt)}
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

    def compress(self, cwd, partial_path, out_path):
        token = None
        full_path = os.path.join(cwd, partial_path)
        latus.logger.log.info('compress : %s to %s' % (full_path, out_path))
        if os.path.exists(full_path):
            with open(full_path, 'rb') as in_file:
                try:
                    token = self.__fernet.encrypt(in_file.read())
                except cryptography.exceptions.UnsupportedAlgorithm as e:
                    latus.logger.log.error('%s : %s %s' % (e, full_path, out_path))
                if token:
                    with open(out_path, 'wb') as out_file:
                        out_file.write(token)
        else:
            latus.logger.log.warn('does not exist : %s' % partial_path)

    def expand(self, in_path, out_path):
        latus.logger.log.info('expand : %s to %s' % (in_path, out_path))
        success = False
        if os.path.exists(in_path):
            with open(in_path, 'rb') as in_file:
                b = None
                try:
                    b = self.__fernet.decrypt(in_file.read())
                except cryptography.fernet.InvalidToken as e:
                    latus.logger.log.error('InvalidToken %s : %s %s' % (str(e), in_path, out_path))
                    print(e)
                except cryptography.exceptions.UnsupportedAlgorithm as e:
                    print(e)
                    latus.logger.log.error('UnsupportedAlgorithm %s : %s %s' % (str(e), in_path, out_path))
                if b:
                    with open(out_path, 'wb') as out_file:
                        out_file.write(b)
                        success = True
        else:
            latus.logger.log.warn('does not exist : %s' % in_path)
        return success



