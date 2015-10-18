
import requests
import time
import logging

import latus.logger


"""
    Monotonically Increasing Value (miv)
"""


def get_miv():
    server = 'http://mono.lat.us'
    miv = None
    tries = 0
    while miv is None and tries < 3:
        r = requests.get(server)
        if r.status_code == 200:
            # do a 'try' in case we get some strange text back
            try:
                miv = float(r.text)
            except ValueError:
                miv = None
            if miv:
                latus.logger.log.info('miv from %s : %s' % (server, str(miv)))
                return miv
            else:
                latus.logger.log.warn('try %d : unexpected text from %s : %s' % (tries, server, r.text))
        tries += 1

    # the monotonic value from the server is based on time(), so if we can't use the server then use our local time
    miv = time.time()
    latus.logger.log.warn('could not get miv from %s - using local time() : %s' % (server, str(miv)))

    return miv


if __name__ == '__main__':
    latus.logger.init('temp')
    latus.logger.set_console_log_level(logging.INFO)
    print(get_miv())