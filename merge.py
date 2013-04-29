
import sys
import argparse
import os
import larg
from latus import logger, util, merge

if __name__ == "__main__":
    logger.setup()
    log = logger.get_log()

    epilog = """
Execute with no arguments to run the GUI version.

Command line example:
""" + os.path.split(sys.argv[0])[-1] + " -s my_source -d my_dest"

    parser = argparse.ArgumentParser(epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-s", "--source", help="path to source directory/folder")
    parser.add_argument("-d", "--dest", default = None, help="path to destination directory/folder")
    parser.add_argument("-m", "--mode", nargs=1, default = 'm', choices='acm', help="finddup, copy or move")
    parser.add_argument("-o", "--outfile", help="output file path")
    parser.add_argument("-t", "--test", nargs=1, help="special test parameters (metadata path)", default = None)
    larg.add_common_arg(parser)

    args = parser.parse_args()
    if args.source is None:
        # stub for GUI version
        sys.exit("-h for help")
    if args.test is None:
        metadata_override = None
    else:
        metadata_override = util.Metadata(args.test[0], None)
    verbose = args.verbose
    mode = merge.str_to_mode(args.mode)
    source = util.decode_text(args.source)
    dest = util.decode_text(args.dest)
    out_file_path = args.outfile

    logger.set_log_level(args.loglevel)
    m = merge.merge(source, out_file_path , dest, verbose = args.verbose,
              metadata_override= metadata_override, mode = mode)
    m.run()
    m.close()