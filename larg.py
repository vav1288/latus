# larg - latus argument utility routines

import argparse
import sys

def init(description):
    parser = argparse.ArgumentParser(description=description, formatter_class=argparse.ArgumentDefaultsHelpFormatter,\
                                     add_help=False)
    # do my own help, since ArgumentDefaultsHelpFormatter squishes all the text together
    parser.add_argument("-h", "--help", action="store_true", help="print help")
    parser.add_argument("-v", "--verbose", action="store_true", help="print informational messages")
    parser.add_argument("-j", "--json", action="store_true", help="use JSON output format")
    parser.add_argument("-l", "--loglevel", choices=('d', 'debug', 'i', 'info', 'w', 'warning', 'e', 'error'),
                        default='w', nargs=1,help="set logging level")
    return parser

# MUST use this parse_args (don't run the one from parser directly or else you won't get the help)
# help_epilog is a list of strings - we'll print one per line
def parse_args(parser, help_epilog = None):
    args = parser.parse_args()
    if args.help:
        parser.print_help()
        if help_epilog:
            print()
            for l in help_epilog:
                print(l)
        sys.exit()
    return args
