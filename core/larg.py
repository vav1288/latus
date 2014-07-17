# larg - latus argument utility routines

import argparse
import core.util

class LatusArg():
    def __init__(self, description, add_path = True):
        self.parser = argparse.ArgumentParser(description=description)
        self.parser.add_argument('-m', '--metadata', default = core.util.get_appdata_folder(), metavar='path', help='metadata root folder')
        self.parser.add_argument('-v', '--verbose', action='store_true', help="output status messages during execution")
        if add_path:
            self.parser.add_argument('-p', '--path', metavar='path', required=True, help="folder to scan")

    def parse(self):
        """
        If you like, do your own add_argument before calling this.
        :return: filled in arg object
        """
        return self.parser.parse_args()