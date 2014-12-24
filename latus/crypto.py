
import os
from cryptography.fernet import Fernet

def new_key():
    return Fernet.generate_key()

class Crypto():
    def __init__(self, key, verbose = False):
        self.__key = key
        self.__verbose = verbose
        self.__fernet = Fernet(self.__key)

    def compress(self, cwd, in_path, out_path):
        with open(os.path.join(cwd, in_path), 'rb') as in_file:
            token = self.__fernet.encrypt(in_file.read())
            with open(out_path, 'wb') as out_file:
                out_file.write(token)

    def expand(self, cwd, in_path, out_path):
        with open(os.path.join(cwd, in_path), 'rb') as in_file:
            b = self.__fernet.decrypt(in_file.read())
            with open(out_path, 'wb') as out_file:
                out_file.write(b)



