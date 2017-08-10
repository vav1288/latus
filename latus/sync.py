
import latus.aws.sync_aws
import latus.csp.sync_csp
import latus.util
import latus.logger
import latus.preferences


def main():
    # Run latus from the command line with existing preferences.
    # This is particularly useful for testing.
    args = latus.util.arg_parse()
    latus.logger.init_from_args(args)
    pref = latus.preferences.Preferences(args.appdatafolder)
    if pref.get_cloud_mode() == 'aws':
        sync = latus.aws.sync_aws.Sync(args.appdatafolder)
    elif pref.get_cloud_mode() == 'csp':
        sync = latus.csp.sync_csp.Sync(args.appdatafolder)
    else:
        sync = None
    if sync:
        sync.start()
        input('hit enter to exit')
        if sync.request_exit():
            print('note: exit timed out')
    else:
        print('cloud mode "%s" not implemented' % pref.get_cloud_mode())
        raise NotImplementedError

if __name__ == '__main__':
    main()
