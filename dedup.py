from core import larg
import core.db
import core.util
import core.metadatapath

if __name__ == "__main__":

    larg_parser = core.larg.LatusArg("Deduplicate a folder")
    args = larg_parser.parse()

    db = core.db.DB(core.metadatapath.MetadataPath(args.metadata))
    db.scan(args.path)
