
from pprint import pprint

import threading

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
        sync = latus.aws.sync_aws.AWSSync(args.appdatafolder, args.localstack)
    elif pref.get_cloud_mode() == 'csp':
        latus.logger.log.warn('deprecated')
        sync = latus.csp.sync_csp.Sync(args.appdatafolder)
    else:
        sync = None
    if sync:
        sync.start()
        input('hit enter to exit')
        latus.logger.log.info('%s : got input keypress' % pref.get_node_id())
        if sync.request_exit():
            latus.logger.log.warn('note: exit timed out in %s' % function.__name__)
    else:
        print('cloud mode "%s" not implemented' % pref.get_cloud_mode())
        raise NotImplementedError
    latus.logger.log.info('exiting sync.py main()')

if __name__ == '__main__':
    main()
