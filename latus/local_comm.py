
import threading
import socket
import logging
import time
import random
import json
import os
import glob

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
import urllib.request

import latus.logger
import latus.nodedb
import latus.folders

g_node_db_folder = None
g_crypto_key = None

# LAN communications


class CommServerHandler(BaseHTTPRequestHandler):

    """
    HTTP handler for crypto key
    """

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        id_in_url = path[1:]
        json_values = {}
        if g_node_db_folder:
            if os.path.exists(os.path.join(g_node_db_folder, id_in_url + '.db')):
                response = 200
                json_values['key'] = g_crypto_key
                latus.logger.log.info(str(json_values))
            else:
                response = 404
            self.send_response(response)
            self.send_header('Content-type','application/json')
            self.end_headers()
            json_values['response'] = response
            self.wfile.write(bytearray(json.dumps(json_values), 'utf-8'))
        else:
            latus.logger.log.error('g_node_db_folder : %s' % str(g_node_db_folder))
        return

    def log_message(self, format, *args):
        latus.logger.log.info(format % args)

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
        latus.logger.log.info('Started httpserver on port %s' % str(self.port))
        self.server.serve_forever()

    def shutdown(self):
        if self.server:
            self.server.shutdown()
            # self.server.socket.close()


class LocalComm(threading.Thread):

    """
    Comm server that launches the HTTP server and then checks for IP address changes in order to properly restart.
    """

    def __init__(self, node_id, node_db_folder, crypto_key):
        self.node_id = node_id
        self.update_nodedb_folder(node_db_folder)
        self.update_crypto_key(crypto_key)
        self._request_exit_flag = False

        super().__init__()

    def update_nodedb_folder(self, nodedb_folder):
        global g_nodedb_folder
        g_nodedb_folder = nodedb_folder

    def update_crypto_key(self, crypto_key):
        global g_crypto_key
        g_crypto_key = crypto_key

    def get_key(self):
        # find an existing node
        for nodedb in glob.glob(os.path.join(g_node_db_folder, '*.db')):
            node_id = os.path.basename(nodedb).replace('.db', '')

    def request_exit(self):
        self._request_exit_flag = True

    def run(self):
        self._check_for_new_local_ip()
        if g_node_db_folder:
            node_db = latus.nodedb.NodeDB(g_node_db_folder, self.node_id, True)
            comm_server = CommServer(node_db.get_port())
            comm_server.start()

            while not self._request_exit_flag:
                if self._check_for_new_local_ip():
                    comm_server.shutdown()
                    del comm_server
                    comm_server = CommServer(node_db.get_port())
                    comm_server.start()
                time.sleep(0.1)  # todo: make this event driven instead of polling

            comm_server.shutdown()
            comm_server.join()  # todo: put in a timeout and check that the thread really stopped
        else:
            latus.logger.log.error('g_node_db_folder : %s' % g_node_db_folder)

    def _check_for_new_local_ip(self):
        if g_node_db_folder:
            node_db = latus.nodedb.NodeDB(g_node_db_folder, self.node_id, True)
            current_ip = socket.gethostbyname(socket.gethostname())
            prior_ip = node_db.get_local_ip()
            if current_ip != prior_ip:
                # new ip address
                latus.logger.log.info('new_ip : %s , prior_ip : %s' % (current_ip, prior_ip))
                node_db.set_local_ip(current_ip)
                node_db.set_port(random.randint(49152, 65535))  # http://en.wikipedia.org/wiki/Ephemeral_port
                return True
        else:
            latus.logger.log.error('g_node_db_folder : %s' % g_node_db_folder)
        return False


if __name__ == "__main__":
    temp_folder = 'temp'
    node_id = 'b9042ad1-a9d5-4ba6-b609-0b0e0a70d997'
    latus.logger.init(temp_folder)
    latus.logger.set_console_log_level(logging.INFO)

    # set up a test config
    #setup_config = latus.config.Config(temp_folder)
    #setup_config.set_node_id(node_id)
    #setup_config.set_crypto_key_string('my_secret_crypto_key')

    lc = LocalComm(node_id, temp_folder, 'my_secret_crypto_key')
    lc.start()
    period = 5
    for s in range(0, 30, period):
        print(s)
        time.sleep(period)
    lc.request_exit()
    lc.join()