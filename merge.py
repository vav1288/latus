

import core.larg
import core.db
import core.metadatapath

if __name__ == "__main__":

    larg_parser = core.larg.LatusArg("Merge one folder into another", False)
    larg_parser.parser.add_argument('-s', '--source', metavar='path', required=True, help="source folder")
    larg_parser.parser.add_argument('-d', '--dest', metavar='path', required=True, help="destination folder")
    args = larg_parser.parse()

    db = core.db.DB(core.metadatapath.MetadataPath(args.metadata))
    print("scanning", args.source)
    db.scan(args.source)
    print("scanning", args.dest)
    db.scan(args.dest)
    diff = db.difference(args.source, args.dest)
    print("to move", diff)
