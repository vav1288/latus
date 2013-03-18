
import sys
import os
import argparse
import logging
import logger
import merge

class merge_cli():
    def __init__(self):
        self.log = logger.get_log()

    def parse_args(self):
        usage_example = "example: " + os.path.split(sys.argv[0])[-1] + " -s my_source -d my_dest"
        parser = argparse.ArgumentParser(epilog=usage_example)
        parser.add_argument("-s", "--source", required=True, help="path to source directory/folder")
        parser.add_argument("-d", "--dest", default = None, help="path to destination directory/folder")
        parser.add_argument("-m", "--mode", nargs=1, default = 'm', choices='acm', help="analyze, copy or move")
        parser.add_argument("-o", "--outfile", help="output file path")
        parser.add_argument("-t", "--test", nargs=1, help="special test parameters (metadata path)", default = None)
        parser.add_argument("-v", "--verbose", help="print informational messages", action="store_true")

        args = parser.parse_args()
        if args.test is None:
            self.metadata_root_override = None
        else:
            self.metadata_root_override = args.test[0]
        self.verbose = args.verbose
        self.mode = merge.str_to_mode(args.mode)
        self.source = unicode(args.source)
        self.dest = unicode(args.dest)
        self.out_file_path = args.outfile

    def run(self):
        lm = merge.merge(self.source, self.out_file_path , self.dest, verbose=self.verbose,
                         metadata_root_override = self.metadata_root_override,
                         mode = self.mode)
        lm.run()
        lm.close()

if __name__ == "__main__":
    lm_cli = merge_cli()
    lm_cli.parse_args()
    logger.setup()
    if lm_cli.verbose:
        lm_cli.log.setLevel(logging.INFO)
    lm_cli.run()
