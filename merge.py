

import argparse
import core.db
import core.metadatapath

if __name__ == "__main__":
    description = "Merge one folder into another"
    parser  = argparse.ArgumentParser()
    parser.add_argument('-m', '--metadata', metavar='path', required=True, help='metadata root folder')
    parser.add_argument('-s', '--source', metavar='path', required=True, help="source folder")
    parser.add_argument('-d', '--dest', metavar='path', required=True, help="destination folder")
    parser.add_argument('-v', '--verbose', action='store_true', help="output status messages during execution")
    args = parser.parse_args()

    db = core.db.DB(core.metadatapath.MetadataPath(args.metadata))
    print("scanning", args.source)
    db.scan(args.source)
    print("scanning", args.dest)
    db.scan(args.dest)
    diff = db.difference(args.source, args.dest)
    print("to move", diff)
