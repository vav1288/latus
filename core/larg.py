# larg - latus argument utility routines

import argparse
import logging
import core.logger
import core.util

class LatusArg():
    def __init__(self, description, add_path = False, add_metadata = False):
        self.parser = argparse.ArgumentParser(description=description)
        self.parser.add_argument('-v', '--verbose', action='store_true', help="output status messages during execution")
        if add_metadata:
            self.parser.add_argument('-m', '--metadata', default = core.util.get_appdata_folder(), metavar='path',
                                     help='metadata root folder')
        if add_path:
            self.parser.add_argument('-p', '--path', metavar='path', required=True, help="folder to scan")

    def parse(self):
        """
        If you like, do your own add_argument call(s) before calling this.
        :return: filled in arg object
        """
        args = self.parser.parse_args()
        if args.verbose:
            core.logger.set_log_level(logging.INFO)
        return args