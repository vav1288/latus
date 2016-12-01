
import os
import datetime

import sqlalchemy
import sqlalchemy.orm
import sqlalchemy.ext.declarative

import latus.util
import latus.const
import latus.logger


# DB schema version is the latus version where this schema was first introduced.  If your DB schema is earlier
# than (i.e. "less than") this, you need to do a drop all tables and start over.  This value is MANUALLY copied from
# latus.__version__ when a new and incompatible schema is introduced.
__db_version__ = '0.0.0'


Base = sqlalchemy.ext.declarative.declarative_base()


class PreferencesTable(Base):
    __tablename__ = 'preferences'

    key = sqlalchemy.Column(sqlalchemy.String(), primary_key=True)
    value = sqlalchemy.Column(sqlalchemy.String())
    datetime = sqlalchemy.Column(sqlalchemy.DateTime())


class Preferences:

    PREFERENCES_FILE = 'preferences' + latus.const.DB_EXTENSION

    def __init__(self, latus_appdata_folder, init=False):

        # todo: do I still need 'init' parameter?  I think I can just get rid of it and act as if it's True

        self.__id_string = 'nodeid'
        self.__key_string = 'cryptokey'
        self.__most_recent_key_folder_string = 'keyfolder'
        self.__cloud_root_string = 'cloudroot'
        self.__latus_folder_string = 'latusfolder'
        self.__check_new_version_string = 'checknewversion'
        self.__upload_usage_string = 'uploadusage'
        self.__upload_logs_string = 'uploadlogs'
        self.__version_key_string = 'version'
        self.__verbose_string = 'verbose'

        os.makedirs(latus_appdata_folder, exist_ok=True)
        self.__db_path = os.path.abspath(os.path.join(latus_appdata_folder, self.PREFERENCES_FILE))
        sqlite_path = 'sqlite:///' + self.__db_path
        self.__db_engine = sqlalchemy.create_engine(sqlite_path)  # , echo=True)
        # todo: check the version in the DB against the current __version__ to see if we need to force a drop table
        # (since this schema is so simple, we probably won't ever have to do this)
        if init:
            Base.metadata.create_all(self.__db_engine)
        self.__Session = sqlalchemy.orm.sessionmaker(bind=self.__db_engine)
        if init:
            latus.logger.log.info('creating preferences DB version %s' % __db_version__)
            self.__pref_set(self.__version_key_string, __db_version__)

    def __pref_set(self, key, value):
        latus.logger.log.debug('pref_set : %s to %s' % (str(key), str(value)))
        session = self.__Session()
        pref_table = PreferencesTable(key=key, value=value, datetime=datetime.datetime.utcnow())
        q = session.query(PreferencesTable).filter_by(key=key).first()
        if q:
            session.delete(q)
        session.add(pref_table)
        session.commit()
        session.close()

    def __pref_get(self, key):
        # latus.logger.log.debug('pref_get : %s' % str(key))
        session = self.__Session()
        row = session.query(PreferencesTable).filter_by(key=key).first()
        if row:
            value = row.value
        else:
            value = None
        session.close()
        # latus.logger.log.debug('pref_get : %s' % str(value))
        return value

    def set_crypto_key(self, key):
        self.__pref_set(self.__key_string, key)

    def get_crypto_key(self):
        return self.__pref_get(self.__key_string)

    def set_cloud_root(self, folder):
        self.__pref_set(self.__cloud_root_string, os.path.abspath(folder))

    def get_cloud_root(self):
        return self.__pref_get(self.__cloud_root_string)

    def set_latus_folder(self, folder):
        self.__pref_set(self.__latus_folder_string, os.path.abspath(folder))

    def get_latus_folder(self):
        return self.__pref_get(self.__latus_folder_string)

    def set_verbose(self, value):
        self.__pref_set(self.__verbose_string, str(value))

    def get_verbose(self):
        return bool(self.__pref_get(self.__verbose_string))

    def set_key_folder(self, folder):
        self.__pref_set(self.__most_recent_key_folder_string, folder)

    def get_key_folder(self):
        return self.__pref_get(self.__most_recent_key_folder_string)

    def set_check_new_version(self, check_flag):
        self.__pref_set(self.__check_new_version_string, check_flag)

    def get_check_new_version(self):
        ul = self.__pref_get(self.__check_new_version_string)
        if ul:
            return bool(int(ul))
        else:
            return False

    def set_upload_usage(self, upload_usage_flag):
        self.__pref_set(self.__upload_usage_string, upload_usage_flag)

    def get_upload_usage(self):
        ul = self.__pref_get(self.__upload_usage_string)
        if ul:
            return bool(int(ul))
        else:
            return False

    def set_upload_logs(self, upload_logs_flag):
        self.__pref_set(self.__upload_logs_string, upload_logs_flag)

    def get_upload_logs(self):
        ul = self.__pref_get(self.__upload_logs_string)
        if ul:
            return bool(int(ul))
        else:
            return False

    def set_node_id(self, new_node_id):
        self.__pref_set(self.__id_string, new_node_id)

    def get_node_id(self):
        return self.__pref_get(self.__id_string)

    def get_db_path(self):
        return self.__db_path

    def folders_are_set(self):
        return self.get_cloud_root() is not None and self.get_latus_folder() is not None