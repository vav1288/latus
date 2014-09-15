
import win32event
import core.sync
import core.larg


def main():
    larg_parser = core.larg.LatusArg("securely syncs a folder to cloud storage")
    larg_parser.parser.add_argument('-p', '--password', required=True, help="latus password")
    larg_parser.parser.add_argument('-l', '--local', metavar='path', required=True, help="latus folder")
    larg_parser.parser.add_argument('-c', '--cloud', metavar='path', required=True, help="cloud folder")
    args = larg_parser.parse()

    keyboard_event_handle = win32event.CreateEvent(None, 0, 0, None)
    sync = core.sync.Sync(args.password,  args.local, args.cloud, exit_event_handle=keyboard_event_handle, verbose=args.verbose)
    sync.start()
    input('hit enter to exit')
    win32event.PulseEvent(keyboard_event_handle)

if __name__ == "__main__":
    main()

