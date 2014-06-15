
import argparse

import core.db
import core.sync
import core.metadatapath

if __name__ == "__main__":
    description = "syncs a folder to cloud storage"
    parser  = argparse.ArgumentParser()
    parser.add_argument('-m', '--metadata', metavar='path', required=True, help='metadata root')
    parser.add_argument('-l', '--local', metavar='path', required=True, help="local folder")
    parser.add_argument('-c', '--cloud', metavar='path', required=True, help="cloud folder")
    parser.add_argument('-i', '--id', metavar='path', required=True, help="identifier for this 'node'")
    parser.add_argument('-v', '--verbose', action='store_true', help="output status messages during execution")
    args = parser.parse_args()

    m = core.metadatapath.MetadataPath(args.metadata)
    ldb = core.db.DB(m, args.id)
    ldb.scan(args.local)
    sdb = core.db.DB(m, 's') # sync
    cdb = core.db.DB(m, 'c') # cloud
    sync = core.sync.Sync(ldb, sdb, cdb)
    sync.sync()
