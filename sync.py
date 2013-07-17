
import sys
import os
import larg
from latus import logger, util, sync

if __name__ == "__main__":
    logger.setup()
    log = logger.get_log()

    epi = ["Examples:",\
           os.path.split(sys.argv[0])[-1] + "                                          # uses default location for settings",
           os.path.split(sys.argv[0])[-1] + " -s C:\\joe\\latus\\settings\\                # explicitly specify settings folder",
           os.path.split(sys.argv[0])[-1] + " -d                                       # dump settings",
           os.path.split(sys.argv[0])[-1] + " -a local C:\\Users\\joe\\Documents\\latus\\   # assign local folder",
           os.path.split(sys.argv[0])[-1] + " -a cloud C:\\Users\\joe\\Documents\\DropBox\\ # assign cloud storage folder"]

    parser = larg.init("latus folder sync")
    parser.add_argument("-s", "--settings", metavar='path', help="path to settings folder")
    parser.add_argument("-d", "--dump", action="store_true", help="print settings information")
    parser.add_argument("-a", "--assign", nargs=2, metavar=('key','value'), help="assign a value to a particular setting")
    args = larg.parse_args(parser, epi)
    verbose = args.verbose
    logger.set_log_level(args.loglevel)
