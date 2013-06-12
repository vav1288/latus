
import os
import sys
import argparse
import larg
from latus import logger, util, finddup

if __name__ == "__main__":

    logger.setup()

    epilog = """
Execute with no arguments to run the GUI version.

Command line example:
""" + os.path.split(sys.argv[0])[-1] + " -p my_source"

    parser = argparse.ArgumentParser(epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-p", "--path", help="path to directory/folder to finddup")
    parser.add_argument("-o", "--outfile", help="output file path")
    parser.add_argument("-t", "--test", nargs=1, help="special test parameters (metadata path)", default = None)
    larg.common_argparse(parser)

    args = parser.parse_args()
    if args.path is None:
        # stub for GUI version
        sys.exit("-h for help")
    if args.test is None:
        metadata_override = None
    else:
        metadata_override = util.Metadata(args.test[0], None)

    logger.set_log_level(args.loglevel)

    a = finddup.finddup(args.path, metadata_override, args.verbose)
    a.run()