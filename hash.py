import os
import win32con
import larg
from latus import logger, hash, lprint

if __name__ == "__main__":
    import argparse

    logger.setup()

    epilog = [
'Discussion:',
'"concatenated" does a hash by doing a digest on the contents of each (ordered) file.  Conceptually this is a hash on',
'the concatenation of the contents of all files (after ordering the file list).  Consequently, if any file changes in',
"the folder, it has to re-calculate the hash from all files.  Therefore, this is often the slower option.",
'',
'"hash-of-hash" (hoh) takes the (potentially cached) hash of each file and creates a hash of these file hashes.',
'Since pre-computed (cached) hashes can be utilized, this is often a faster option if only some files have changed.'
]

    parser = larg.init("get the hash of a folder or file", True)
    parser.add_argument("-p", "--path", default='.', help="path to source directory/folder")
    parser.add_argument("-c", "--cat", action="store_true", default=False, help="concatenated hash")
    parser.add_argument("-o", "--hoh", action="store_true", default=False, help="hash-of-hash")
    # todo: add -hidden and -system flags
    parser.add_argument("-a", "--all", action="store_true", help="hash all file attributes (e.g. system, hidden)")
    args = larg.parse_args(parser, epilog)

    args = parser.parse_args()
    if args.all:
        file_attrib = set([win32con.FILE_ATTRIBUTE_HIDDEN, win32con.FILE_ATTRIBUTE_SYSTEM])
    else:
        file_attrib = set()

    if not (args.cat or args.hoh):
        print("nothing to do - specify -c or -o")

    if args.cat:
        print("cat:")
        h = hash.hash(args.path, None, verbose=args.verbose, include_attrib=file_attrib, hoh=False)
        calculated_hash = h.get_hash(args.path)
        # need to dump as a dict to include the names in the namedtuple
        lprint.lprint(calculated_hash.__dict__, lprint.JSON_STYLE)

    # hash of hash style
    if args.hoh:
        print("hoh:")
        h = hash.hash(args.path, None, verbose=args.verbose, include_attrib=file_attrib, hoh=True)
        calculated_hash = h.get_hash(args.path)
        # need to dump as a dict to include the names in the namedtuple
        lprint.lprint(calculated_hash.__dict__, lprint.JSON_STYLE)