
import requests
import requests.exceptions
import time
import logging

import latus.logger


"""
    Monotonically Increasing Value (miv)
"""


g_prior_miv = None
g_miv_count = 0


def _get_miv(node_id):
    global g_miv_count
    server = 'https://api.abel.co/miv'
    miv = None
    tries = 0
    while miv is None and tries < 3:
        r = None
        try:
            r = requests.get(server)
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
            latus.logger.log.info(str(e))
        if r and r.status_code == 200:
            # do a 'try' in case we get some strange text back
            try:
                miv = float(r.text)
            except ValueError:
                miv = None
            if miv:
                latus.logger.log.info('%s : miv %d from %s : %s' % (node_id, g_miv_count, server, str(miv)))
                break
            else:
                latus.logger.log.warn('%s : try %d : unexpected text from %s : %s' % (node_id, tries, server, r.text))
        tries += 1

    if miv is None:
        # the monotonic value from the server is based on time(), so if we can't use the server then use our local time
        miv = time.time()
        latus.logger.log.warn('%s : could not get miv from %s - using local time() : %s' % (node_id, server, str(miv)))

    g_miv_count += 1
    return miv


# node_id is for debug (logging)
def get_miv(node_id):
    # make sure we are actually monotonically increasing
    global g_prior_miv
    miv = _get_miv(node_id)
    retry_count = 10
    while g_prior_miv and miv <= g_prior_miv and retry_count > 0:
        time.sleep(10)
        latus.logger.log.warn('%s : miv retry' % node_id)
        miv = _get_miv(node_id)
        retry_count -= 1
    if retry_count <= 0:
        miv = None
        latus.logger.log.fatal('%s : miv fatal' % node_id)
    return miv

if __name__ == '__main__':
    node_id = 'xyz'
    latus.logger.init('temp')
    latus.logger.set_console_log_level(logging.INFO)
    print(get_miv(node_id))
    print(get_miv(node_id))
    print(get_miv(node_id))