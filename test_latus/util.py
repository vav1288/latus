
import os
import time
import logging
import json

import latus.logger


def logger_init(log_folder):
    latus.logger.init(log_folder)
    latus.logger.set_console_log_level(logging.INFO)
    latus.logger.set_file_log_level(logging.DEBUG)

# get an mtime back in time
def get_mtime_time():
    return time.mktime(time.strptime("12", "%y"))

def make_dirs(p):
    if not os.path.exists(p):
        os.makedirs(p)

def wait_on_nodes(log_folders_param):
    for log_folder in log_folders_param:
        wait_for_node(log_folder)


def wait_for_node(log_folder):
    # wait for this node to settle down and cease all activity
    # returns True if stability found, False if we merely timed out and gave up

    sleep_time = 0.1  # sec
    time_out = 30/sleep_time  # sec to timeout
    stable = 2/sleep_time  # number of seconds we need to see stable files to declare it stable
    time_out_count = time_out
    stable_count = stable
    unstable_file = None

    status = []
    log_files = ['cloud.log', 'local.log']
    prior_status = {}
    for log_file in log_files:
        prior_status[log_file] = None
    while stable_count > 0 and time_out_count > 0:
        stable_flag = True
        for log_file in log_files:
            file_path = os.path.join(log_folder, log_file)
            if os.path.exists(file_path):
                with open(file_path) as json_file:
                    try:
                        status = json.load(json_file)
                    except ValueError:
                        stable_flag = False
                    if prior_status[log_file]:
                        #print('status', status)
                        if status['count'] != prior_status[log_file]['count'] or status['status'] != 'waiting':
                            stable_flag = False
                            unstable_file = file_path
                    else:
                        stable_flag = False
                    prior_status[log_file] = status
            else:
                stable_flag = False
        #print('stable_flag', stable_flag)
        if stable_flag:
            stable_count -= 1
        else:
            stable_count = stable
        time_out_count -= 1
        time.sleep(0.1)
    if time_out_count <= 0:
        latus.logger.log.warn('timeout : %s' % unstable_file)
    return time_out_count > 0