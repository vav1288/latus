import os
import datetime

#import sqlalchemy
#import sqlalchemy.exc
#import sqlalchemy.ext.declarative

import requests
import time
import logging

import latus.logger
#import latus.const
#import latus.util

"""
    Monotonically Increasing Value (miv)
"""


def get_miv():
    # todo: allow us to use mono.lat.us .  Will have to deal with name servers, etc.
    server = 'http://monotonic-latus.rhcloud.com/'
    r = requests.get(server)
    if r.status_code == 200:
        miv = float(r.text.split()[0])
        latus.logger.log.info('miv from %s : %s' % (server, miv))
    else:
        # the monotonic value from the server is based on time(), so if we can use the server use our local time
        latus.logger.log.warn('miv: could not get time from server %s - using local time()' % server)
        miv = time.time()
    return miv


if __name__ == '__main__':
    latus.logger.init('temp')
    latus.logger.set_console_log_level(logging.INFO)
    print(get_miv())