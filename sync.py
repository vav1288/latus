
import argparse
import logging

import core.logger
import core.db
import core.sync
import core.metadatapath

if __name__ == "__main__":
    description = "syncs a folder to cloud storage"
    parser  = argparse.ArgumentParser()
    parser.add_argument('-m', '--metadata', metavar='path', required=True, help='metadata root')
    parser.add_argument('-l', '--local', metavar='path', required=True, help="local folder")
    parser.add_argument('-i', '--id', metavar='path', required=True, help="identifier for this 'node'")
    parser.add_argument('-v', '--verbose', action='store_true', help="output status messages during execution")
    args = parser.parse_args()

    if args.verbose:
        core.logger.set_log_level(logging.INFO)
    sync = core.sync.Sync(args.metadata, args.local, args.id)
    sync.scan()
    sync.sync()
