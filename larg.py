
# larg - latus argument utility routines

def add_common_arg(parser):
    parser.add_argument("-v", "--verbose", action="store_true", help="print informational messages")
    parser.add_argument("-j", "--json", action="store_true", help="use JSON output format (default is from pprint)")
    parser.add_argument("-l", "--loglevel", choices=('d', 'debug', 'i', 'info', 'w', 'warning', 'e', 'error'),
                        default='w', nargs=1,help="set logging level")
