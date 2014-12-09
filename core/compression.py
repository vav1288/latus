
import os
from cryptography.fernet import Fernet

class Compression():
    def __init__(self, key, verbose = False):
        self.key = key
        self.verbose = verbose
        self.f = Fernet(self.key)

    def compress(self, cwd, in_path, out_path):
        with open(os.path.join(cwd, in_path), 'rb') as in_file:
            token = self.f.encrypt(in_file.read())
            with open(out_path, 'wb') as out_file:
                out_file.write(token)

    def expand(self, cwd, in_path, out_path):
        with open(os.path.join(cwd, in_path), 'rb') as in_file:
            b = self.f.decrypt(in_file.read())
            with open(out_path, 'wb') as out_file:
                out_file.write(b)



