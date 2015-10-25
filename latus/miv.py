
import requests
import requests.exceptions
import time
import logging

import latus.logger


"""
    Monotonically Increasing Value (miv)
"""


g_prior_miv = None


def _get_miv():
    server = 'http://mono.lat.us'
    miv = None
    tries = 0
    while miv is None and tries < 3:
        r = None
        try:
            r = requests.get(server)
        except requests.exceptions.ConnectionError:
            pass
        if r and r.status_code == 200:
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


def get_miv():
    # make sure we are actually monotonically increasing
    global g_prior_miv
    miv = _get_miv()
    retry_count = 10
    while g_prior_miv and miv <= g_prior_miv and retry_count > 0:
        time.sleep(10)
        latus.logger.log.warn('miv retry')
        miv = _get_miv()
        retry_count -= 1
    if retry_count <= 0:
        miv = None
        latus.logger.log.fatal('miv fatal')
    return miv

if __name__ == '__main__':
    latus.logger.init('temp')
    latus.logger.set_console_log_level(logging.INFO)
    print(get_miv())
    print(get_miv())
    print(get_miv())