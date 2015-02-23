
import os
import datetime

import sqlalchemy
import sqlalchemy.orm
import sqlalchemy.ext.declarative

import latus.util
import latus.const

Base = sqlalchemy.ext.declarative.declarative_base()


class ConfigTable(Base):
    __tablename__ = 'config'

    key = sqlalchemy.Column(sqlalchemy.String(),primary_key=True)
    value = sqlalchemy.Column(sqlalchemy.String())
    datetime = sqlalchemy.Column(sqlalchemy.DateTime())


class Config:
    def __init__(self, latus_appdata_folder, init=False):

        self.__id_string = 'nodeid'
        self.__key_string = 'cryptokey'
        self.__most_recent_key_folder_string = 'keyfolder'
        self.__cloud_root_string = 'cloudroot'
        self.__latus_folder_string = 'latusfolder'
        self.__verbose_string = 'verbose'

        if not os.path.exists(latus_appdata_folder):
            latus.util.make_dirs(latus_appdata_folder)
        sqlite_path = 'sqlite:///' + os.path.abspath(os.path.join(latus_appdata_folder, 'config.db'))
        self.__db_engine = sqlalchemy.create_engine(sqlite_path)  # , echo=True)
        if init:
            self.init()
        Base.metadata.create_all(self.__db_engine)
        self.__Session = sqlalchemy.orm.sessionmaker(bind=self.__db_engine)

    def __config_set(self, key, value):
        session = self.__Session()
        config_table = ConfigTable(key=key,value=value,datetime=datetime.datetime.utcnow())
        q = session.query(ConfigTable).filter_by(key=key).first()
        if q:
            session.delete(q)
        session.add(config_table)
        session.commit()
        session.close()

    def __config_get(self, key):
        session = self.__Session()
        row = session.query(ConfigTable).filter_by(key=key).first()
        if row:
            value = row.value
        else:
            value = None
        session.close()
        return value

    def set_crypto_key_string(self, key):
        self.__config_set(self.__key_string, key)

    # Crypto keys are bytes, but we store them as a string.
    def set_crypto_key(self, key):
        s = key.decode()  # to string
        self.__config_set(self.__key_string, s)

    # string version
    def get_crypto_key_string(self):
        return self.__config_get(self.__key_string)

    # bytes version (for use by crypto routines)
    def get_crypto_key(self):
        b = None
        key = self.get_crypto_key_string()
        if key:
            b = key.encode()  # to bytes
        return b

    def set_cloud_root(self, folder):
        self.__config_set(self.__cloud_root_string, os.path.abspath(folder))

    def get_cloud_root(self):
        return self.__config_get(self.__cloud_root_string)

    def set_latus_folder(self, folder):
        self.__config_set(self.__latus_folder_string, os.path.abspath(folder))

    def get_latus_folder(self):
        return self.__config_get(self.__latus_folder_string)

    def set_verbose(self, value):
        self.__config_set(self.__verbose_string, str(value))

    def get_verbose(self):
        return bool(self.__config_get(self.__verbose_string))

    def set_key_folder(self, folder):
        self.__config_set(self.__most_recent_key_folder_string, folder)

    def get_key_folder(self):
        return self.__config_get(self.__most_recent_key_folder_string)

    def set_node_id(self, new_node_id):
        self.__config_set(self.__id_string, new_node_id)

    def get_node_id(self):
        return self.__config_get(self.__id_string)

    def init(self):
        Base.metadata.drop_all(self.__db_engine)
        Base.metadata.create_all(self.__db_engine)

    def are_all_set(self):
        # Return True if everything is set, and we're all set to go!
        return self.get_crypto_key() and self.get_node_id() and self.get_cloud_root() and self.get_latus_folder()