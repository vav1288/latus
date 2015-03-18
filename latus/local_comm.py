
import threading
import socket
import logging
import time
import random
import json
import os
import glob
import platform
import getpass

from http.server import BaseHTTPRequestHandler, HTTPServer
import http.client
import urllib.parse
import urllib.request
import urllib.error

import latus.logger
import latus.nodedb
import latus.folders
import latus.preferences
import latus.util
import latus.const


# LAN communications


# a global so the http server can get to it
g_app_data_folder = None

PROVIDING_KEY_STRING = 'providing_key'
KEY_STRING = 'key'
COMPUTER_STRING = 'computer'
USER_STRING = 'user'

class CommServerHandler(BaseHTTPRequestHandler):

    """
    HTTP handler for crypto key
    """

    def do_GET(self):
        global g_app_data_folder

        parsed = urllib.parse.urlparse(self.path)
        parsed_path = parsed.path
        node_id_in_url = parsed_path[1:]
        query = urllib.parse.parse_qs(parsed.query)
        json_values = {}
        response = http.client.NOT_FOUND
        ip = self.client_address[0]
        computer = None
        user = None
        if COMPUTER_STRING in query:
            computer = query[COMPUTER_STRING][0]
        if USER_STRING in query:
            user = query[USER_STRING][0]

        latus.logger.log.debug("server : path : %s" % self.path)
        latus.logger.log.info("server : requester : %s" % node_id_in_url)
        latus.logger.log.info("server : ip : %s" % ip)
        latus.logger.log.info("server : computer : %s" % computer)
        latus.logger.log.info("server : user : %s " % user)

        # todo: put a log of the key requests/services in this node's nodedb - this tells us what nodes have let
        # in other nodes.

        pref = latus.preferences.Preferences(g_app_data_folder)
        cloud_folders = latus.folders.CloudFolders(pref.get_cloud_root())
        if cloud_folders.nodedb:
            if os.path.exists(os.path.join(cloud_folders.nodedb, node_id_in_url + latus.const.DB_EXTENSION)):
                # This node is known to me, so respond to it.  This even works for my own node, but that's just
                # for testability.
                response = http.client.OK
                if pref.get_trusted_network():
                    json_values[PROVIDING_KEY_STRING] = True
                    json_values[KEY_STRING] = pref.get_crypto_key_string()
                    node_db = latus.nodedb.NodeDB(cloud_folders.nodedb, node_id_in_url, True)
                    node_db.set_join(ip, computer, user, pref.get_crypto_key_string())
                else:
                    # todo: what we really need here is to pop up a window to ask if it's OK to provide the key (this code as it sits always denies if on an untrusted network)
                    ns = 'functionality not yet implemented'
                    latus.logger.log.error(ns)
                    print(ns)

                    json_values[PROVIDING_KEY_STRING] = False

                latus.logger.log.info(str(json_values))
        self.send_response(response)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        json_values['response'] = response
        self.wfile.write(bytearray(json.dumps(json_values), 'utf-8'))
        return

    def log_message(self, log_format, *args):
        latus.logger.log.info(log_format % args)


class CommServer(threading.Thread):

    """
    HTTP server for crypto key
    """

    def __init__(self, port):
        self.port = port
        self.server = None
        super().__init__()

    def run(self):
        self.server = HTTPServer(('', int(self.port)), CommServerHandler)
        latus.logger.log.info('Started httpserver at http://%s:%s' %
                              (socket.gethostbyname(socket.gethostname()), str(self.port)))
        self.server.serve_forever()

    def shutdown(self):
        if self.server:
            self.server.shutdown()
            # self.server.socket.close()


class LocalComm(threading.Thread):

    """
    Provide local communication between nodes.
    """

    def __init__(self, app_data_folder):
        global g_app_data_folder
        g_app_data_folder = app_data_folder

        self._request_exit_flag = False
        self._port = None

        super().__init__()

    def get_key(self):
        # local comm client
        key = None
        pref = latus.preferences.Preferences(g_app_data_folder)
        cloud_folders = latus.folders.CloudFolders(pref.get_cloud_root())
        if cloud_folders.nodedb:
            for other_node_db in glob.glob(os.path.join(cloud_folders.nodedb, '*' + latus.const.DB_EXTENSION)):
                # Note that you get get your own key, but that's just for testability.
                other_node_id = os.path.basename(other_node_db).replace(latus.const.DB_EXTENSION, '')
                other_node_db = latus.nodedb.NodeDB(cloud_folders.nodedb, other_node_id)
                query = urllib.parse.urlencode({COMPUTER_STRING: platform.node(), USER_STRING:  getpass.getuser()})
                url = 'http://' + other_node_db.get_local_ip() + ':' + other_node_db.get_port() + '/'
                url += pref.get_node_id() + '?' + query
                latus.logger.log.info('client : get_key url : %s' % url)
                js = None
                try:
                    js = urllib.request.urlopen(url).read()
                except urllib.error.HTTPError as err:
                    latus.logger.log.info(str(err))
                if js:
                    node_info = json.loads(js.decode("utf-8"))
                    key = None
                    if node_info[PROVIDING_KEY_STRING]:
                        key = node_info[KEY_STRING]
                    latus.logger.log.info('client : key : %s' % key)
        return key

    def request_exit(self):
        self._request_exit_flag = True

    def run(self):
        # local comm server
        pref = latus.preferences.Preferences(g_app_data_folder)
        cloud_folders = latus.folders.CloudFolders(pref.get_cloud_root())
        self._check_for_new_local_ip()
        if cloud_folders.nodedb:
            this_node_db = latus.nodedb.NodeDB(cloud_folders.nodedb, pref.get_node_id(), True)
            self._port = this_node_db.get_port()
            comm_server = CommServer(self._port)
            comm_server.start()

            while not self._request_exit_flag:
                if self._check_for_new_local_ip():
                    comm_server.shutdown()
                    del comm_server
                    self._port = this_node_db.get_port()
                    comm_server = CommServer(self._port)
                    comm_server.start()
                time.sleep(0.1)  # todo: make this event driven instead of polling

            comm_server.shutdown()
            comm_server.join()  # todo: put in a timeout and check that the thread really stopped
        else:
            latus.logger.log.error('cloud_folders.nodedb : %s' % cloud_folders.nodedb)

    def _check_for_new_local_ip(self):
        pref = latus.preferences.Preferences(g_app_data_folder)
        cloud_folders = latus.folders.CloudFolders(pref.get_cloud_root())
        if cloud_folders.nodedb:
            node_db = latus.nodedb.NodeDB(cloud_folders.nodedb, pref.get_node_id(), True)
            current_ip = socket.gethostbyname(socket.gethostname())
            prior_ip = node_db.get_local_ip()
            if current_ip != prior_ip:
                # new ip address
                latus.logger.log.info('new_ip : %s , prior_ip : %s' % (current_ip, prior_ip))
                node_db.set_local_ip(current_ip)
                node_db.set_port(random.randint(49152, 65535))  # http://en.wikipedia.org/wiki/Ephemeral_port
                node_db.set_key_hash(pref.get_crypto_key_string())
                return True
        else:
            latus.logger.log.error('cloud_folders.nodedb : %s' % cloud_folders.nodedb)
        return False

    def get_port(self):
        return self._port

if __name__ == "__main__":
    # this is a basic start of the "server"

    import latus.sync

    node_str = 'aea275dd-8947-490d-a198-f5d98e43688d'
    key = 'my_secret_crypto_key'

    temp_folder = os.path.join('temp', node_str)

    latus.logger.init(os.path.join(temp_folder, 'log'))
    latus.logger.set_console_log_level(logging.INFO)

    cloud_folder = os.path.join(temp_folder, 'cloud')

    app_data_folder = os.path.join(temp_folder, 'appdata')
    c = latus.preferences.Preferences(app_data_folder)
    c.set_cloud_root(cloud_folder)
    c.set_node_id(node_str)
    c.set_crypto_key_string(key)
    c.set_trusted_network(True)

    cf = latus.folders.CloudFolders(c.get_cloud_root())
    latus.util.make_dirs(cf.nodedb)

    lc = LocalComm(app_data_folder)
    lc.start()
    current_ip = socket.gethostbyname(socket.gethostname())
    period = 5
    for s in range(0, 30, period):
        print(s)
        time.sleep(period)
        latus.logger.log.info('key accessible at http://%s:%s/%s' % (current_ip, lc.get_port(), node_str))
        lc.get_key()
    lc.request_exit()
    lc.join()