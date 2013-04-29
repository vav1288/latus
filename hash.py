import os
import win32con
import larg
from latus import logger, hash, lprint

if __name__ == "__main__":
    import sys
    import argparse

    logger.setup()

    epilog = """
example:
""" + os.path.split(sys.argv[0])[-1] + " -p myfolder"

    parser = argparse.ArgumentParser(epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-p", "--path", default='.', help="path to source directory/folder")
    parser.add_argument("-a", "--all", action="store_true", help="hash all files (default is to ignore hidden and system files)")
    larg.add_common_arg(parser)

    args = parser.parse_args()
    if args.all:
        file_attrib = (win32con.FILE_ATTRIBUTE_HIDDEN, win32con.FILE_ATTRIBUTE_SYSTEM)
    else:
        file_attrib = []
    h = hash.hash(None, verbose=args.verbose, include_attrib=file_attrib)
    calculated_hash = h.get_hash(args.path)
    # need to dump as a dict to include the names in the namedtuple
    lprint.lprint(calculated_hash.__dict__, lprint.JSON_STYLE)

