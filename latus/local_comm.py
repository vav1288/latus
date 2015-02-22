
import os
import threading
import socket
import datetime
import time
import random
import json

from http.server import BaseHTTPRequestHandler, HTTPServer

import sqlalchemy
import sqlalchemy.orm
import sqlalchemy.ext.declarative

import latus.logger
import latus.config

Base = sqlalchemy.ext.declarative.declarative_base()

crypto_key = None

# LAN communications


class CommTable(Base):
    __tablename__ = 'comm'

    id = sqlalchemy.Column(sqlalchemy.String(), primary_key=True)
    ip = sqlalchemy.Column(sqlalchemy.String())
    port = sqlalchemy.Column(sqlalchemy.Integer())
    datetime = sqlalchemy.Column(sqlalchemy.DateTime())


class CommServerHandler(BaseHTTPRequestHandler):

    """
    HTTP handler for crypto key
    """

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','application/json')
        self.end_headers()
        js = json.dumps({'key': str(crypto_key)})
        self.wfile.write(bytearray(js, 'utf-8'))
        return


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

    def __init__(self, node_id, local_comm_folder):
        self._request_exit_flag = False
        self.comm_server = None
        self.node_id = node_id

        if not os.path.exists(local_comm_folder):
            os.mkdir(local_comm_folder)
        sqlite_path = 'sqlite:///' + os.path.abspath(os.path.join(local_comm_folder, node_id + '.db'))
        self.__db_engine = sqlalchemy.create_engine(sqlite_path)  # , echo=True)
        Base.metadata.create_all(self.__db_engine)
        self.__Session = sqlalchemy.orm.sessionmaker(bind=self.__db_engine)

        super().__init__()

    # call this to exit this thread
    def request_exit(self):
        self._request_exit_flag = True

    def run(self):
        node_id, ip, port, dt = self.get()
        self.check_for_new_ip()
        self.start_server(port)

        while not self._request_exit_flag:
            if self.check_for_new_ip():
                node_id, ip, port, dt = self.get()
                self.start_server(port)  # restart
            time.sleep(0.1)  # todo: make this event driven instead of polling

        if self.comm_server:
            self.comm_server.shutdown()
            self.comm_server.join()  # todo: put in a timeout and check that the thread really stopped
            self.comm_server = None

    def check_for_new_ip(self):
        current_ip = socket.gethostbyname(socket.gethostname())
        prior_ip = self.get_ip()
        if current_ip != prior_ip:
            # new ip address
            latus.logger.log.info('new_ip : %s , prior_ip : %s' % (current_ip, prior_ip))
            port = random.randint(49152, 65535)  # http://en.wikipedia.org/wiki/Ephemeral_port
            session = self.__Session()
            config_table = CommTable(id=self.node_id, ip=current_ip, port=port, datetime=datetime.datetime.utcnow())
            q = session.query(CommTable).first()
            if q:
                session.delete(q)
            session.add(config_table)
            session.commit()
            session.close()
            return True
        return False

    def start_server(self, port):
        if self.comm_server:
            self.comm_server.shutdown()
            del self.comm_server
        self.comm_server = CommServer(port)
        self.comm_server.start()

    def get(self):
        node_id = None
        ip = None
        port = None
        dt = None
        session = self.__Session()
        row = session.query(CommTable).first()
        if row:
            node_id = row.id
            ip = row.ip
            port = row.port
            dt = row.datetime
        session.close()
        return node_id, ip, port, dt

    def get_ip(self):
        _, ip, _, _ = self.get()
        return ip

if __name__ == "__main__":
    temp_folder = 'temp'
    latus.logger.init(temp_folder)
    node_id = 'my_node'
    crypto_key = 'my_crypto_key'

    config = latus.config.Config(temp_folder)
    config.node_id_set(node_id)
    config.crypto_set_string(crypto_key)

    lc = LocalComm(node_id, temp_folder)
    lc.start()
    period = 5
    for s in range(0, 30, period):
        print(s)
        time.sleep(period)
    lc.request_exit()
    lc.join()