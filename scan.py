
import argparse
import core.db
import core.metadatapath

if __name__ == "__main__":
    description = "Scans a folder/directory and updates the metadata database."
    parser  = argparse.ArgumentParser()
    parser.add_argument('-m', '--metadata', metavar='path', required=True, help='metadata root folder')
    parser.add_argument('-p', '--path', metavar='path', required=True, help="folder to scan")
    parser.add_argument('-v', '--verbose', action='store_true', help="output status messages during execution")
    args = parser.parse_args()

    db = core.db.DB(core.metadatapath.MetadataPath(args.metadata))
    db.scan(args.path)
