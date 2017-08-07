
import requests
import requests.exceptions
import time
import logging
import json

import latus.logger


"""
    Monotonically Increasing Value (miv)
"""


g_prior_miv = None
g_miv_count = 0


def _get_mivui(node_id):
    """
    get miv as a string
    :param node_id: node ID, mainly for debug
    :return: miv as an integer
    """
    global g_miv_count
    # todo: Make this https.  I get this error with https:
    #       SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:645)

    # todo: a big one here ... try a list of miv URLs in case one isn't working ...
    #       (and create a strategy for quickly determining which works or not)

    # miv.abel.co stopped working for some reason ... :(
    # server = 'http://miv.abel.co'
    server = 'http://api.abel.co/miv'

    mivui = None
    json_text = None
    tries = 0
    while mivui is None and tries < 3:
        r = None
        latus.logger.log.debug('%s : starting %s' % (node_id, server))
        try:
            r = requests.get(server)
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
            latus.logger.log.warn(str(e))
        latus.logger.log.debug('%s : end %s' % (node_id, server))
        if r and r.status_code == 200:
            # do a 'try' in case we get some strange text back
            try:
                json_text = r.text
            except ValueError:
                json_text = None
            if json_text:
                latus.logger.log.debug('%s : miv %d from %s : %s' % (node_id, g_miv_count, server, str(json_text)))
                break
            else:
                latus.logger.log.warn('%s : try %d : unexpected text from %s : %s' % (node_id, tries, server, json_text))
        tries += 1
    if json_text:
        json_miv = json.loads(json_text)
        mivui = json_miv['mivui']

    if mivui is None:
        # the monotonic value from the server is based on time(), so if we can't use the server then use our local time
        mivui = int(round(time.time() * 1E6))
        latus.logger.log.warn('%s : could not get miv from %s - using local time() : %d' % (node_id, server, mivui))

    g_miv_count += 1
    return mivui


def get_mivui(node_id):
    """
    get miv
    :param node_id: node ID, mainly for debugging
    :return: mivui as an integer
    """
    # make sure we are actually monotonically increasing
    global g_prior_miv
    mivui = _get_mivui(node_id)
    retry_count = 10
    while g_prior_miv and mivui <= g_prior_miv and retry_count > 0:
        time.sleep(1)
        latus.logger.log.warn('%s : miv retry' % node_id)
        mivui = _get_mivui(node_id)
        retry_count -= 1
    if retry_count <= 0:
        mivui = None
        latus.logger.log.fatal('%s : miv fatal' % node_id)
    g_prior_miv = mivui
    return mivui

if __name__ == '__main__':
    test_node_id = 'xyz'
    latus.logger.init('temp')
    latus.logger.set_console_log_level(logging.DEBUG)
    print(get_mivui(test_node_id))
    print(get_mivui(test_node_id))
    print(get_mivui(test_node_id))
