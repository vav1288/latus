
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
    def __init__(self, latus_appdata_folder):

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

    def crypto_set_string(self, key):
        self.__config_set(self.__key_string, key)

    # Crypto keys are bytes, but we store them as a string.
    def crypto_set(self, key):
        s = key.decode()  # to string
        self.__config_set(self.__key_string, s)

    # string version
    def crypto_get_string(self):
        return self.__config_get(self.__key_string)

    # bytes version (for use by crypto routines)
    def crypto_get(self):
        b = None
        key = self.crypto_get_string()
        if key:
            b = key.encode()  # to bytes
        return b

    def cloud_root_set(self, folder):
        self.__config_set(self.__cloud_root_string, os.path.abspath(folder))

    def cloud_root_get(self):
        return self.__config_get(self.__cloud_root_string)

    def latus_folder_set(self, folder):
        self.__config_set(self.__latus_folder_string, os.path.abspath(folder))

    def latus_folder_get(self):
        return self.__config_get(self.__latus_folder_string)

    def verbose_set(self, value):
        self.__config_set(self.__verbose_string, str(value))

    def verbose_get(self):
        return bool(self.__config_get(self.__verbose_string))

    def key_folder_set(self, folder):
        self.__config_set(self.__most_recent_key_folder_string, folder)

    def key_folder_get(self):
        self.__config_get(self.__most_recent_key_folder_string)

    def node_id_set(self, new_node_id):
        self.__config_set(self.__id_string, new_node_id)

    def node_id_get(self):
        return self.__config_get(self.__id_string)

    def init(self):
        Base.metadata.drop_all(self.__db_engine)
        Base.metadata.create_all(self.__db_engine)

