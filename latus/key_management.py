
import os
import datetime

from simplecrypto import RsaKeypair, RsaPublicKey

import sqlalchemy
import sqlalchemy.orm
import sqlalchemy.ext.declarative

import latus.const
import latus.nodedb
import latus.preferences
import latus.folders
import latus.logger
import latus.util

Base = sqlalchemy.ext.declarative.declarative_base()


class KeyManagementTable(Base):
    __tablename__ = 'keys'

    index = sqlalchemy.Column(sqlalchemy.Integer(), primary_key=True)
    source = sqlalchemy.Column(sqlalchemy.String())
    destination = sqlalchemy.Column(sqlalchemy.String())
    encrypted_latus_key = sqlalchemy.Column(sqlalchemy.String())
    datetime = sqlalchemy.Column(sqlalchemy.DateTime())


class KeyRequestTable(Base):
    __tablename__ = 'requests'

    requester = sqlalchemy.Column(sqlalchemy.String(), primary_key=True)
    datetime = sqlalchemy.Column(sqlalchemy.DateTime())


class KeyManagement:

    KEY_MANAGEMENT_FILE = 'keys' + latus.const.DB_EXTENSION

    def __init__(self, app_data_folder):
        self.app_data_folder = app_data_folder
        pref, node_db = create_pref_and_node_db(self.app_data_folder)
        cloud_folders = latus.folders.CloudFolders(pref.get_cloud_root())
        if not os.path.exists(cloud_folders.keys):
            os.mkdir(cloud_folders.keys)
        sqlite_path = 'sqlite:///' + os.path.abspath(os.path.join(cloud_folders.keys, self.KEY_MANAGEMENT_FILE))
        self.__db_engine = sqlalchemy.create_engine(sqlite_path)  # , echo=True)
        Base.metadata.create_all(self.__db_engine)
        self.__Session = sqlalchemy.orm.sessionmaker(bind=self.__db_engine)

    def get_requesters(self):
        # delete really old (> 1 day) requests
        session = self.__Session()
        q = session.query(KeyRequestTable).all()
        if q:
            for row in q:
                if row.datetime < datetime.datetime.utcnow() - datetime.timedelta(days=1):
                    session.delete(row)
        session.commit()
        requesters = []
        rows = session.query(KeyRequestTable).all()
        for row in rows:
            requesters.append(row.requester)
        session.close()
        return requesters

    def get_requester_info(self, requester):
        pref = latus.preferences.Preferences(self.app_data_folder)
        cloud_folders = latus.folders.CloudFolders(pref.get_cloud_root())
        requester_node_db = latus.nodedb.NodeDB(cloud_folders.nodedb, requester)
        return requester_node_db.get_user(), requester_node_db.get_computer()

    def respond_to_request(self, requester):
        latus.logger.log.info('responding to %s' % requester)
        pref = latus.preferences.Preferences(self.app_data_folder)
        cloud_folders = latus.folders.CloudFolders(pref.get_cloud_root())
        requester_node_db = latus.nodedb.NodeDB(cloud_folders.nodedb, requester)
        private_key = RsaPublicKey(requester_node_db.get_public_key())
        encrypted_latus_key = private_key.encrypt(pref.get_crypto_key_string())
        session = self.__Session()
        this_node_id = pref.get_node_id()
        requester = requester_node_db.get_node_id()
        kmt = KeyManagementTable(source=this_node_id, destination=requester,
                                 encrypted_latus_key=encrypted_latus_key, datetime=datetime.datetime.utcnow())
        q = session.query(KeyManagementTable).filter_by(source=this_node_id).filter_by(destination=requester).first()
        if q:
            session.delete(q)
        session.add(kmt)
        session.commit()
        session.close()

    def get_key(self):
        pref = latus.preferences.Preferences(self.app_data_folder)
        session = self.__Session()
        rows = session.query(KeyManagementTable).filter_by(destination=pref.get_node_id()).all()
        latus_key = None
        for row in rows:
            private_key = RsaKeypair(pref.get_private_key())
            latus_key = private_key.decrypt(row.encrypted_latus_key)
        session.close()
        return latus_key.decode("utf-8")

    def request_key(self, timestamp=datetime.datetime.utcnow()):
        pref, node_db = create_pref_and_node_db(self.app_data_folder)
        session = self.__Session()
        this_node_id = pref.get_node_id()
        request_table = KeyRequestTable(requester=this_node_id, datetime=timestamp)
        q = session.query(KeyRequestTable).filter_by(requester=this_node_id).first()
        if q:
            session.delete(q)
        session.add(request_table)
        session.commit()
        session.close()


def create_pref_and_node_db(app_data_folder):
    pref = latus.preferences.Preferences(app_data_folder)
    cloud_folders = latus.folders.CloudFolders(pref.get_cloud_root())
    node_db = latus.nodedb.NodeDB(cloud_folders.nodedb, pref.get_node_id())
    return pref, node_db

