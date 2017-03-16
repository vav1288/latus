
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
    """
    get miv as a string
    :param node_id: node ID, mainly for debug
    :return: miv as a string
    """
    global g_miv_count
    # todo: Make this https.  I get this error with https:
    #       SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:645)
    server = 'http://api.abel.co/miv'
    miv = None
    tries = 0
    while miv is None and tries < 3:
        r = None
        try:
            latus.logger.log.info('%s : starting %s' % (node_id, server))
            time.sleep(1)
            r = requests.get(server)
            latus.logger.log.info('%s : end %s' % (node_id, server))
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
            latus.logger.log.info(str(e))
        if r and r.status_code == 200:
            # do a 'try' in case we get some strange text back
            try:
                miv = r.text
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
        miv = str(time.time())
        latus.logger.log.warn('%s : could not get miv from %s - using local time() : %s' % (node_id, server, str(miv)))

    g_miv_count += 1
    return miv


def get_miv(node_id):
    """
    get miv
    :param node_id: node ID, mainly for debugging
    :return: miv as a string
    """
    # make sure we are actually monotonically increasing
    global g_prior_miv
    miv = _get_miv(node_id)
    retry_count = 10
    while g_prior_miv and float(miv) <= float(g_prior_miv) and retry_count > 0:
        time.sleep(10)
        latus.logger.log.warn('%s : miv retry' % node_id)
        miv = _get_miv(node_id)
        retry_count -= 1
    if retry_count <= 0:
        miv = None
        latus.logger.log.fatal('%s : miv fatal' % node_id)
    g_prior_miv = miv
    return miv

if __name__ == '__main__':
    node_id = 'xyz'
    latus.logger.init('temp')
    latus.logger.set_console_log_level(logging.INFO)
    print(get_miv(node_id))
    print(get_miv(node_id))
    print(get_miv(node_id))