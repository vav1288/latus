
import os
import sys
import argparse
import larg
from latus import logger, util, finddup

if __name__ == "__main__":

    util.check_text_encoding()

    logger.setup()

    epilog = """
Execute with no arguments to run the GUI version.

Command line example:
""" + os.path.split(sys.argv[0])[-1] + " -p my_source"

    parser = argparse.ArgumentParser(epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-p", "--path", help="path to directory/folder to finddup")
    parser.add_argument("-o", "--outfile", help="output file path")
    parser.add_argument("-t", "--test", nargs=1, help="special test parameters (metadata path)", default = None)
    larg.add_common_arg(parser)

    args = parser.parse_args()
    if args.path is None:
        # stub for GUI version
        sys.exit("-h for help")
    if args.test is None:
        metadata_root_override = None
    else:
        metadata_root_override = args.test[0]

    logger.set_log_level(args.loglevel)

    a = finddup.finddup(args.path, metadata_root_override, args.verbose)
    a.run()