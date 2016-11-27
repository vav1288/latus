
import re
import collections
import os
import time


def get_activity_states(log_file_path):
    """
    :param log_file_path: path to the log file to parse
    :return: a dict of the state of each log file
    """
    states = collections.defaultdict()
    while not os.path.exists(log_file_path):
        time.sleep(1)
    with open(log_file_path) as f:
        for l in f:
            m = re.search(r'([-_0-9a-z]+)( : )(active|ready : 0)', l, re.IGNORECASE)
            if m:
                states[m.group(1)] = m.group(3)
                # print(l.strip())
    return states


def is_active(log_file_path):
    """
    :param log_file_path: path to the log file to parse
    :return: True if any pending activity
    """
    states = get_activity_states(log_file_path)
    return any(['active' in states[state] for state in states])


def main():
    # for testing
    # hopefully something is in this file ...
    log_file_path = os.path.join('/Users/james/Library/Logs/latus/latus.log')
    states = get_activity_states(log_file_path)
    for state in sorted(states):
        print('%s : %s' % (state, states[state]))
    print(is_active(log_file_path))

if __name__ == '__main__':
    main()
