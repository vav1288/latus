
import os
import sys
import argparse
from latus import logger, util, analyze


if __name__ == "__main__":
    logger.setup()

    epilog = """
Execute with no arguments to run the GUI version.

Command line example:
""" + os.path.split(sys.argv[0])[-1] + " -p my_source"

    parser = argparse.ArgumentParser(epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-p", "--path", help="path to directory/folder to analyze")
    parser.add_argument("-o", "--outfile", help="output file path")
    parser.add_argument("-t", "--test", nargs=1, help="special test parameters (metadata path)", default = None)
    util.add_common_arg(parser)

    args = parser.parse_args()
    if args.path is None:
        # stub for GUI version
        sys.exit("-h for help")
    if args.test is None:
        metadata_root_override = None
    else:
        metadata_root_override = args.test[0]
    path = util.decode_text(args.path)

    logger.set_log_level(args.loglevel)

    a = analyze.analyze(path, metadata_root_override, args.verbose)
    a.run()