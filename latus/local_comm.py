
import os
import threading
import socket
import datetime
import time
import random

import sqlalchemy
import sqlalchemy.orm
import sqlalchemy.ext.declarative

import latus.util
import latus.const
import latus.config
import latus.folders

Base = sqlalchemy.ext.declarative.declarative_base()

# LAN communications


class ConfigTable(Base):
    __tablename__ = 'config'

    id = sqlalchemy.Column(sqlalchemy.String(),primary_key=True)
    ip = sqlalchemy.Column(sqlalchemy.String())
    port = sqlalchemy.Column(sqlalchemy.String())
    datetime = sqlalchemy.Column(sqlalchemy.DateTime())


class LocalComm(threading.Thread):
    def __init__(self, node_id, local_comm_folder):
        self._request_exit_flag = False
        self.node_id = node_id
        if not os.path.exists(local_comm_folder):
            os.mkdir(local_comm_folder)
        sqlite_path = 'sqlite:///' + os.path.abspath(os.path.join(local_comm_folder, node_id + '.db'))
        self.__db_engine = sqlalchemy.create_engine(sqlite_path)  # , echo=True)
        Base.metadata.create_all(self.__db_engine)
        self.__Session = sqlalchemy.orm.sessionmaker(bind=self.__db_engine)
        super().__init__()

    def request_exit(self):
        self._request_exit_flag = True

    def run(self):
        self.set_local_ip()
        time_base = 0.1
        update_rate = 60*60  # sec
        count = 0
        while not self._request_exit_flag:
            if count > update_rate/time_base:
                self.set_local_ip()
                count = 0
            count += 1
            time.sleep(time_base)

    def set_local_ip(self):
        ip = socket.gethostbyname(socket.gethostname())
        session = self.__Session()
        port = random.randint(49152, 65535)  # http://en.wikipedia.org/wiki/Ephemeral_port
        config_table = ConfigTable(id=self.node_id, ip=ip, port=port, datetime=datetime.datetime.utcnow())
        q = session.query(ConfigTable).first()
        if q:
            session.delete(q)
        session.add(config_table)
        session.commit()
        session.close()

