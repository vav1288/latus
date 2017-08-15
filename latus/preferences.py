
import os
import datetime

import sqlalchemy
import sqlalchemy.orm
import sqlalchemy.ext.declarative
import sqlalchemy.exc

import latus.util
import latus.const
import latus.logger


# DB schema version is the latus version where this schema was first introduced.  If your DB schema is earlier
# than (i.e. "less than") this, you need to do a drop all tables and start over.  This value is MANUALLY copied from
# latus.__version__ when a new and incompatible schema is introduced.
__db_version__ = '0.0.3'


Base = sqlalchemy.ext.declarative.declarative_base()

PREFERENCES_FILE = 'preferences' + latus.const.DB_EXTENSION


class PreferencesTable(Base):
    __tablename__ = 'preferences'

    key = sqlalchemy.Column(sqlalchemy.String(), primary_key=True)
    value = sqlalchemy.Column(sqlalchemy.String())
    datetime = sqlalchemy.Column(sqlalchemy.DateTime())


class Preferences:

    def __init__(self, latus_appdata_folder, init=False):

        # todo: do I still need 'init' parameter?  I think I can just get rid of it and act as if it's True

        self._id_string = 'nodeid'
        self._key_string = 'cryptokey'
        self._most_recent_key_folder_string = 'keyfolder'
        self._cloud_root_string = 'cloudroot'
        self._cloud_mode_string = 'cloudmode'  # e.g. 'aws', 'csp'
        self._use_aws_local_string = 'awslocal'
        self._aws_location_string = 'awslocation'  # e.g. 'us-west-1'
        self._latus_folder_string = 'latusfolder'
        self._check_new_version_string = 'checknewversion'
        self._upload_usage_string = 'uploadusage'
        self._upload_logs_string = 'uploadlogs'
        self._version_key_string = 'version'
        self._verbose_string = 'verbose'

        self._cloud_mode = None

        if not latus_appdata_folder:
            raise RuntimeError

        self.app_data_folder = latus_appdata_folder
        os.makedirs(self.app_data_folder, exist_ok=True)
        self.__db_path = os.path.abspath(os.path.join(self.app_data_folder, PREFERENCES_FILE))
        sqlite_path = 'sqlite:///' + self.__db_path
        self.__db_engine = sqlalchemy.create_engine(sqlite_path)  # , echo=True)
        # todo: check the version in the DB against the current __version__ to see if we need to force a drop table
        # (since this schema is so simple, we probably won't ever have to do this)
        if init:
            Base.metadata.create_all(self.__db_engine)
        self.__Session = sqlalchemy.orm.sessionmaker(bind=self.__db_engine)
        if init:
            self._pref_set(self._version_key_string, __db_version__, False)
            # defaults
            self._pref_set(self._cloud_mode_string, 'aws', False)

    def _pref_set(self, key, value, overwrite=True):
        latus.logger.log.debug('pref_set : %s to %s (overwrite=%s)' % (str(key), str(value), str(overwrite)))
        session = self.__Session()
        pref_table = PreferencesTable(key=key, value=value, datetime=datetime.datetime.utcnow())
        q = session.query(PreferencesTable).filter_by(key=key).first()
        if q and overwrite:
            session.delete(q)
        if q is None or overwrite:
            session.add(pref_table)
            session.commit()
        session.close()

    def _pref_get(self, key):
        # latus.logger.log.debug('pref_get : %s' % str(key))
        value = None
        session = self.__Session()
        try:
            row = session.query(PreferencesTable).filter_by(key=key).first()
        except sqlalchemy.exc.OperationalError as e:
            row = None
        if row:
            value = row.value
        session.close()
        # latus.logger.log.debug('pref_get : %s' % str(value))
        return value

    def set_crypto_key(self, key):
        self._pref_set(self._key_string, key)

    def get_crypto_key(self):
        return self._pref_get(self._key_string)

    def set_cloud_root(self, folder):
        self._pref_set(self._cloud_root_string, os.path.abspath(folder))

    def get_cloud_root(self):
        return self._pref_get(self._cloud_root_string)

    def set_latus_folder(self, folder):
        self._pref_set(self._latus_folder_string, os.path.abspath(folder))

    def get_latus_folder(self):
        return self._pref_get(self._latus_folder_string)

    def set_aws_location(self, aws_location):
        self._pref_set(self._aws_location_string, aws_location)

    def get_aws_location(self):
        return self._pref_get(self._aws_location_string)

    def set_verbose(self, value):
        self._pref_set(self._verbose_string, str(value))

    def get_verbose(self):
        return eval(self._pref_get(self._verbose_string))

    def set_cloud_mode(self, mode):
        self._pref_set(self._cloud_mode_string, mode)

    def get_cloud_mode(self):
        return self._pref_get(self._cloud_mode_string)

    def set_aws_local(self, value):
        self._pref_set(self._use_aws_local_string, value)

    def get_aws_local(self):
        # True if using AWS localstack
        value = self._pref_get(self._use_aws_local_string)
        if value:
            value = eval(value)
        return value

    def set_check_new_version(self, check_flag):
        self._pref_set(self._check_new_version_string, check_flag)

    def get_check_new_version(self):
        ul = self._pref_get(self._check_new_version_string)
        if ul:
            return bool(int(ul))
        else:
            return False

    def set_upload_usage(self, upload_usage_flag):
        self._pref_set(self._upload_usage_string, upload_usage_flag)

    def get_upload_usage(self):
        ul = self._pref_get(self._upload_usage_string)
        if ul:
            return bool(int(ul))
        else:
            return False

    def set_upload_logs(self, upload_logs_flag):
        self._pref_set(self._upload_logs_string, upload_logs_flag)

    def get_upload_logs(self):
        ul = self._pref_get(self._upload_logs_string)
        if ul:
            return bool(int(ul))
        else:
            return False

    def set_node_id(self, new_node_id):
        self._pref_set(self._id_string, new_node_id)

    def get_node_id(self):
        return self._pref_get(self._id_string)

    def get_db_path(self):
        return self.__db_path

    def folders_are_set(self):
        return self.get_cloud_root() is not None and self.get_latus_folder() is not None

    def get_app_data_folder(self):
        return self.app_data_folder

    def get_cache_folder(self):
        return os.path.join(self.app_data_folder, 'cache')


def preferences_db_exists(folder):
    """
    Return True if preferences DB exists in the folder.
    :param folder: folder that (potentially) holds the preferences DB
    :return: True if DB found, False otherwise
    """
    try:
        return os.path.exists(os.path.join(folder, PREFERENCES_FILE))
    except TypeError:
        return False
