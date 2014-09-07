
import win32api
import subprocess
import os
import copy

class Compression():
    def __init__(self, password, verbose = False):
        self.password = password
        self.verbose = verbose
        self.exe_7zip_path = self.get_7zip_exe()

    def get_7zip_exe(self):
        # todo: store off the path so we don't have to scan every time
        drives = win32api.GetLogicalDriveStrings()
        drives = drives.split('\000')[:-1]
        for drive in drives:
            for r, _, fs in os.walk(drive):
                for f in fs:
                    p = os.path.join(r, f)
                    if os.path.split(p)[1] == '7z.exe':
                        if self.verbose:
                            print("7z found at", p)
                        return p
        return None

    def compress(self, cwd, in_path, out_path):
        self.run_7zip(cwd, 'a', out_path, in_path)

    def expand(self, cwd, in_path):
        success = self.run_7zip(cwd, 't', in_path) # test to ensure password is correct
        if success:
            self.run_7zip(cwd, 'x', in_path) # eXtract

    def run_7zip(self, cwd, command, archive, file_path = None):
        if self.verbose:
            call_stdout = None
        else:
            call_stdout = subprocess.DEVNULL

        command_line = [self.exe_7zip_path, command, '-y', '-p' + self.password, '-tzip', archive]
        if file_path is not None:
            command_line += [file_path]

        if self.verbose:
            print('cwd', cwd)
            print('command', command_line)
        try:
            subprocess.check_call(command_line, cwd=cwd, stdout=call_stdout)
            success_flag = True
        except:
            success_flag = False
        return success_flag
