
import os

from simplecrypto import RsaKeypair, RsaPublicKey

import sqlalchemy
import sqlalchemy.orm
import sqlalchemy.ext.declarative

import latus.const
import latus.nodedb
import latus.preferences

Base = sqlalchemy.ext.declarative.declarative_base()


class KeyManagementTable(Base):
    __tablename__ = 'keymanagement'

    index = sqlalchemy.Column(sqlalchemy.Integer(), primary_key=True)
    source = sqlalchemy.Column(sqlalchemy.String())
    destination = sqlalchemy.Column(sqlalchemy.String())
    encrypted_key = sqlalchemy.Column(sqlalchemy.String())
    datetime = sqlalchemy.Column(sqlalchemy.DateTime())


class KeyManagement:

    KEY_MANAGEMENT_FILE = 'keys' + latus.const.DB_EXTENSION

    def __init__(self, app_data_folder):
        self.app_data_folder = app_data_folder
        pref = latus.preferences.Preferences(self.app_data_folder)
        sqlite_path = 'sqlite:///' + os.path.abspath(os.path.join(pref.get_cloud_root(), 'keys', self.KEY_MANAGEMENT_FILE))
        self.__db_engine = sqlalchemy.create_engine(sqlite_path)  # , echo=True)
        Base.metadata.create_all(self.__db_engine)
        self.__Session = sqlalchemy.orm.sessionmaker(bind=self.__db_engine)

    def get_key(self):
        pass

    def request_key(self):
        pass