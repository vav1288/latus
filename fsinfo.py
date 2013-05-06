
import sys
from latus import util, logger, fsinfo

if __name__ == "__main__":
    logger.setup()
    if len(sys.argv) < 2:
        path = "."
    else:
        path = sys.argv[1]
        if path == "-h" or path == '--help':
            print("usage: fsinfo [path]")
            print("default path is current folder/directory")
            exit("")
    path = util.decode_text(path)
    info = fsinfo.fsinfo(path)
    info.run()