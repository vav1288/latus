
import os
import json
import datetime
from cryptography.fernet import Fernet, InvalidToken
import cryptography.exceptions
import latus.util
import latus.logger


def new_key():
    return Fernet.generate_key()


class Crypto:
    def __init__(self, key, node_id=None):
        self.__key = key
        self.__node_id = node_id
        self.__fernet = Fernet(self.__key)

    def encrypt_file(self, in_path, out_path):
        token = None
        latus.logger.log.info('%s : encrypt : %s to %s' % (self.__node_id, in_path, out_path))
        if os.path.exists(in_path):
            with open(in_path, 'rb') as in_file:
                try:
                    # todo: don't use __fernet directly - look into latest cryptography API
                    token = self.__fernet.encrypt(in_file.read())
                except cryptography.exceptions.UnsupportedAlgorithm as e:
                    latus.logger.log.error('%s : %s %s' % (e, in_path, out_path))
                if token:
                    with open(out_path, 'wb') as out_file:
                        out_file.write(token)
        else:
            latus.logger.log.error('does not exist : %s' % in_path)

    def decrypt_file(self, in_path, out_path):
        latus.logger.log.info('%s : decrypt : %s to %s' % (self.__node_id, in_path, out_path))
        success = False
        if os.path.exists(in_path):
            with open(in_path, 'rb') as in_file:
                b = None
                try:
                    b = self.__fernet.decrypt(in_file.read())
                except InvalidToken as e:
                    latus.logger.log.error('InvalidToken (possible key error) %s : %s %s' % (str(e), in_path, out_path))
                except cryptography.exceptions.UnsupportedAlgorithm as e:
                    latus.logger.log.error('UnsupportedAlgorithm %s : %s %s' % (str(e), in_path, out_path))
                if b:
                    with open(out_path, 'wb') as out_file:
                        out_file.write(b)
                        success = True
        else:
            latus.logger.log.warn('does not exist : %s' % in_path)
        return success

    def get_key(self):
        return self.__key

