
import core.sync
import core.larg

if __name__ == "__main__":
    larg_parser = core.larg.LatusArg("syncs a folder to cloud storage", False)
    larg_parser.parser.add_argument('-l', '--local', metavar='path', required=True, help="latus folder")
    larg_parser.parser.add_argument('-c', '--cloud', metavar='path', required=True, help="cloud folder")
    args = larg_parser.parse()

    sync = core.sync.Sync(args.cloud, args.local, verbose=args.verbose)
    sync.sync()
