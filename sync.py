
import argparse
import logging

import core.logger
import core.db
import core.sync
import core.metadatapath
import core.larg

if __name__ == "__main__":
    larg_parser = core.larg.LatusArg("syncs a folder to cloud storage", False)
    larg_parser.parser.add_argument('-l', '--local', metavar='path', required=True, help="local folder")
    larg_parser.parser.add_argument('-i', '--id', metavar='path', required=True, help="identifier for this 'node'")
    args = larg_parser.parse()

    sync = core.sync.Sync(args.metadata, args.local, args.id)
    sync.scan()
    sync.sync()
