
import os
import datetime
import platform
import getpass
import glob
import time

import sqlalchemy
import sqlalchemy.exc

from latus.const import DB_EXTENSION, ChangeAttributes
import latus.logger
import latus.util
import latus.const

# DB schema version is the latus version where this schema was first introduced.  If your DB schema is earlier
# than (i.e. "less than") this, you need to do a drop all tables and start over.  This value is MANUALLY copied from
# latus.__version__ when a new and incompatible schema is introduced.
__db_version__ = '0.0.3'


# A note on OS interoperability on paths:
# We store paths in the DB MacOS/OSX/*nix style - i.e. with forward slashes
# External to the NodeDB class the paths are in the format of the OS we are running on (Win or Mac).  They can be
# passed into the NodeDB class in the native OS format and they are returned in the native OS format.

class NodeDB:
    def __init__(self, db_folder, node_id, write_flag=False, cloud_mode='csp'):

        self._node_id_string = 'nodeid'
        self._local_ip_string = 'localip'
        self._port_string = 'port'
        self._public_key_string = 'publickey'
        self._user_string = 'user'
        self._computer_string = 'computer'
        self._login_string = 'login'
        self._heartbeat_string = 'heartbeat'
        self._cloud_mode = cloud_mode

        self.retry_count = 0
        self.node_id = node_id
        if cloud_mode == 'csp':
            # The DB file name is based on the node id.  This is important ... this way we never have a conflict
            # writing to the DB since there is only one writer.
            self.database_file_name = node_id + DB_EXTENSION
        elif cloud_mode == 'aws':
            self.database_file_name = 'fsevents' + DB_EXTENSION
        else:
            raise NotImplementedError
        self.sqlite_file_path = os.path.join(db_folder, self.database_file_name)

        if not os.path.exists(self.sqlite_file_path) and not write_flag:
            latus.logger.log.error('DB does not exist and write_flag not set, can not initialize : %s' % self.sqlite_file_path)
            self.db_engine = None
            return

        if write_flag:
            try:
                os.makedirs(db_folder, mode=latus.const.MAKE_DIRS_MODE, exist_ok=True)
            except PermissionError as e:
                latus.logger.log.error('%s : %s (%s)' % (str(e), db_folder, os.path.abspath(db_folder)))

        # the 'bind' and 'connection' seem to be redundant - what do I really need????
        # (I seem to need the bind, so perhaps I can get rid of the connection?)
        self.db_engine = sqlalchemy.create_engine('sqlite:///' + os.path.abspath(self.sqlite_file_path))  # , echo=True)
        self.sa_metadata = sqlalchemy.MetaData()
        self.sa_metadata.bind = self.db_engine

        # general key/value store
        self.general_table = sqlalchemy.Table('general', self.sa_metadata,
                                              sqlalchemy.Column('key', sqlalchemy.String, primary_key=True),
                                              sqlalchemy.Column('value', sqlalchemy.String),
                                              sqlalchemy.Column('timestamp', sqlalchemy.DateTime),
                                              )

        self.change_table = sqlalchemy.Table('change', self.sa_metadata,
                                             sqlalchemy.Column('index', sqlalchemy.Integer, primary_key=True),
                                             sqlalchemy.Column('mivui', sqlalchemy.Integer, index=True),
                                             sqlalchemy.Column('originator', sqlalchemy.String),
                                             sqlalchemy.Column('event_type', sqlalchemy.Integer),
                                             sqlalchemy.Column('detection', sqlalchemy.Integer),
                                             sqlalchemy.Column('file_path', sqlalchemy.String, index=True),
                                             sqlalchemy.Column('src_path', sqlalchemy.String),  # source path for moves
                                             sqlalchemy.Column('size', sqlalchemy.Integer),
                                             sqlalchemy.Column('file_hash', sqlalchemy.String, index=True),
                                             sqlalchemy.Column('mtime', sqlalchemy.DateTime),

                                             # AWS: True = pending write to the cloud
                                             # csp: True = action has been taken
                                             sqlalchemy.Column('pending', sqlalchemy.Boolean),

                                             sqlalchemy.Column('timestamp', sqlalchemy.DateTime),
                                             )

        self.folders_table = sqlalchemy.Table('folders', self.sa_metadata,
                                              sqlalchemy.Column('name', sqlalchemy.String, primary_key=True),
                                              sqlalchemy.Column('encrypt', sqlalchemy.Boolean),
                                              sqlalchemy.Column('shared', sqlalchemy.Boolean),
                                              sqlalchemy.Column('cloud', sqlalchemy.Boolean),
                                              sqlalchemy.Column('timestamp', sqlalchemy.DateTime),
                                              )

        if write_flag:
            new_schema = False
            try:
                if not self.db_engine.has_table('general'):
                    latus.logger.log.info('%s : no tables in DB' % self.node_id)
                    new_schema = True
            except sqlalchemy.exc.OperationalError as e:
                latus.logger.log.info('%s : no DB' % self.node_id)
                new_schema = True
            if not new_schema:
                if latus.util.version_to_tuple(__db_version__) > latus.util.version_to_tuple(self._get_general('version')[0]):
                    new_schema = True
                    latus.logger.log.info('%s : new DB schema' % self.node_id)
            if new_schema:
                latus.logger.log.info('%s : start creating node DB version %s' % (node_id, __db_version__))
                try:
                    self.sa_metadata.drop_all()
                    self.sa_metadata.create_all()
                except sqlalchemy.exc.OperationalError as e:
                    latus.logger.log.fatal(str(e))
                self.set_all(node_id)
                self._set_general('version', __db_version__)  # keep track of this DB version as it was created
                latus.util.make_hidden(self.sqlite_file_path)
                latus.logger.log.info('%s : end creating node DB version %s' % (node_id, __db_version__))

    def delete(self):
        if os.path.exists(self.sqlite_file_path):
            try:
                os.remove(self.sqlite_file_path)
            except OSError:
                latus.logger.log.error('could not remove : %s' % self.sqlite_file_path)
        else:
            latus.logger.log.warn('already deleted : %s' % self.sqlite_file_path)

    def set_all(self, node_id):
        self.set_login(True)
        self.set_node_id(node_id)
        self.set_user(getpass.getuser())
        self.set_computer(platform.node())
        self.set_heartbeat()
        self.set_folder_preferences('', latus.const.FOLDER_PREFERENCE_DEFAULTS[0], latus.const.FOLDER_PREFERENCE_DEFAULTS[1], latus.const.FOLDER_PREFERENCE_DEFAULTS[2])  # latus root defaults

    def insert(self, mivui, originator, event_type, detection, file_path, src_path, size, file_hash, mtime, pending):
        file_path = norm_latus_path(file_path)
        src_path = norm_latus_path(src_path)
        conn = self.db_engine.connect()
        latus.logger.log.info('%s updating %d %s %s %s %s %s %s %s %s %s' % (self.node_id, mivui, originator, event_type, detection,
                                                                             file_path, src_path, size, file_hash, mtime, pending))
        command = self.change_table.select().where(self.change_table.c.mivui == mivui)
        result = self._execute_with_retry(conn, command, 'update_select')
        if not result.fetchone():
            if mtime:
                command = self.change_table.insert().values(mivui=mivui, originator=originator, event_type=event_type,
                                                            detection=detection, file_path=file_path, src_path=src_path,
                                                            size=size, file_hash=file_hash, mtime=mtime, pending=pending,
                                                            timestamp=datetime.datetime.utcnow())
            else:
                # if file has been deleted, there's no mtime (but we can't pass None into a datetime)
                command = self.change_table.insert().values(mivui=mivui, originator=originator, event_type=event_type,
                                                            detection=detection, file_path=file_path, src_path=src_path,
                                                            pending=pending, timestamp=datetime.datetime.utcnow())
            result = self._execute_with_retry(conn, command, 'update_insert')
        else:
            latus.logger.log.warn('mivui %d already found - not updating' % mivui)
        conn.close()

    def insert_info(self, info, pending):
        self.insert(info['mivui'], info['originator'], info['event_type'], info['detection'], info['file_path'], info['src_path'],
                    info['size'], info['file_hash'], info['mtime'], pending)

    def db_row_to_info(self, row):
        entry = {}
        entry['index'] = row[int(ChangeAttributes.index)]
        entry['mivui'] = row[int(ChangeAttributes.mivui)]
        entry['originator'] = row[int(ChangeAttributes.originator)]
        entry['event_type'] = row[int(ChangeAttributes.event_type)]
        entry['detection'] = row[int(ChangeAttributes.detection)]
        entry['path'] = row[int(ChangeAttributes.file_path)]
        entry['src_path'] = row[int(ChangeAttributes.src_path)]
        entry['size'] = row[int(ChangeAttributes.size)]
        entry['file_hash'] = row[int(ChangeAttributes.file_hash)]
        entry['mtime'] = row[int(ChangeAttributes.mtime)]
        entry['pending'] = row[int(ChangeAttributes.pending)]
        entry['timestamp'] = row[int(ChangeAttributes.timestamp)]
        return entry

    def get_database_file_name(self):
        return self.database_file_name

    def get_database_file_abs_path(self):
        return os.path.abspath(self.sqlite_file_path)

    def get_file_info(self, file_path):
        conn = self.db_engine.connect()
        command = self.change_table.select().where(self.change_table.c.path == file_path)
        result = self._execute_with_retry(conn, command, 'get_file_info')
        updates = []
        for row in result:
            updates.append(self.db_row_to_info(row))
        conn.close()
        return updates

    def get_latest_file_info(self, file_path):
        conn = self.db_engine.connect()
        command = self.change_table.select().where(self.change_table.c.path == file_path)
        result = self._execute_with_retry(conn, command, 'get_latest_file_info')
        update = None
        for row in result:
            update = self.db_row_to_info(row)  # just get last one
        conn.close()
        return update

    # todo: make an iterator
    def get_paths(self):
        conn = self.db_engine.connect()
        file_paths = set()
        if self.change_table.exists():
            command = self.change_table.select()
            result = self._execute_with_retry(conn, command, 'get_paths')
            for row in result:
                file_path = row[int(ChangeAttributes.file_path)]
                if file_path not in file_paths:
                    # return the file paths in the native OS format
                    file_paths.add(os.path.normpath(file_path))
        else:
            latus.logger.log.warning('change_table does not exist')
        conn.close()
        return file_paths

    def get_most_recent_hash(self, file_path):
        file_path = norm_latus_path(file_path)
        conn = self.db_engine.connect()
        file_hash = None
        command = self.change_table.select().where(self.change_table.c.file_path == file_path)
        result = self._execute_with_retry(conn, command, 'get_most_recent_hash')
        if result:
            all_hashes = result.fetchall()
            if all_hashes:
                file_hash = all_hashes[-1][int(ChangeAttributes.file_hash)]
        conn.close()
        return file_hash

    def get_most_recent_entry_for_path(self, non_norm_file_path):
        # get the most recent entry from either 'path' or 'src_path'

        conn = self.db_engine.connect()
        file_path = norm_latus_path(non_norm_file_path)

        # first the 'path' entry
        most_recent_path = None
        command = self.change_table.select().where(self.change_table.c.file_path == file_path)
        result = self._execute_with_retry(conn, command, 'get_most_recent_path')
        if result:
            all_entries = result.fetchall()
            if all_entries:
                most_recent_path = all_entries[-1]

        # second the 'src_path' entry
        most_recent_src_path = None
        command = self.change_table.select().where(self.change_table.c.src_path == file_path)
        result = self._execute_with_retry(conn, command, 'get_most_recent_src_path')
        if result:
            all_entries = result.fetchall()
            if all_entries:
                most_recent_src_path = all_entries[-1]

        conn.close()

        most_recent = most_recent_path
        if most_recent_src_path is not None and most_recent_path is not None:
            if most_recent_src_path['mivui'] > most_recent_path['mivui']:
                most_recent = most_recent_src_path

        return most_recent

    def get_most_recent_entry(self, originator_node_id):
        conn = self.db_engine.connect()
        most_recent = None
        if originator_node_id:
            command = self.change_table.select().where(self.change_table.c.originator == originator_node_id)
        else:
            command = self.change_table.select()
        result = self._execute_with_retry(conn, command, 'get_most_recent_entry')
        if result:
            all_rows = result.fetchall()
            if all_rows:
                most_recent = all_rows[-1]
        conn.close()
        return most_recent

    def get_rows_as_info(self):
        # todo: make this an interator, DB must stay open so to has to have a conn passed in
        infos = []
        with self.db_engine.connect() as conn:
            command = self.change_table.select()
            result = self._execute_with_retry(conn, command, 'get_rows_as_info')
            if result:
                for row in result:
                    infos.append(self.db_row_to_info(row))
            conn.close()
        return infos

    # useful for testing DB access contention
    def get_retry_count(self):
        return self.retry_count

    # Tolerate situations where multiple nodes try to access one DB (this will happen, albeit rarely, in
    # normal operation).
    def _execute_with_retry(self, conn, command, msg=None):
        result = None
        while result is None:
            try:
                result = conn.execute(command)
            except sqlalchemy.exc.OperationalError:
                self.retry_count += 1
                latus.logger.log.info('%s : execute retry : %s : %s : %d' % (self.node_id, str(command), str(msg), self.retry_count))
                result = None
                latus.util.wait_random(3)
        if result is None:
            latus.logger.log.error('execute error : %s' % str(msg))
        return result

    def _get_general(self, key):
        val_is_valid = False
        if self.db_engine is None:
            latus.logger.log.warn('_get_general: db_engine is None')
            return None, None
        conn = self.db_engine.connect()
        val = None
        timestamp = None
        command = self.general_table.select().where(self.general_table.c.key == key)
        result = self._execute_with_retry(conn, command, ('node DB get', key))
        if result:
            row = result.fetchone()
            if row:
                val_is_valid = True
                val = row[1]
                timestamp = row[2]
        conn.close()
        if not val_is_valid:
            latus.logger.log.error('node DB: %s : could not read %s' % (self.node_id, key))
            val = None
            timestamp = None
        return val, timestamp

    def _set_general(self, key, value):
        # todo: I noticed that sometimes somehow this test for doesn't exist fails - i.e. it says it doesn't
        # exist and it actually does, then the insert() causes a unique key exception.  Somehow this
        # should be fixed.
        if self.db_engine is None:
            latus.logger.log.warn('_set_general: db_engine is None')
            return None
        conn = self.db_engine.connect()
        select_command = self.general_table.select().where(self.general_table.c.key == key)
        select_result = self._execute_with_retry(conn, select_command, ('set', key, value))
        do_insert = True
        if select_result:
            row = select_result.fetchone()
            if row:
                do_insert = False
                db_value = row[1]
                if db_value != value:
                    update_command = self.general_table.update().where(self.general_table.c.key == key).\
                        values(value=value, timestamp=datetime.datetime.utcnow())
                    self._execute_with_retry(conn, update_command, ('node DB update', key, value))
        if do_insert:
            insert_command = self.general_table.insert().values(key=key, value=value,
                                                                timestamp=datetime.datetime.utcnow())
            self._execute_with_retry(conn, insert_command, ('node DB insert', key, value))
        conn.close()

    def set_node_id(self, node_id):
        self._set_general(self._node_id_string, node_id)

    def get_node_id(self):
        return self._get_general(self._node_id_string)[0]

    def set_local_ip(self, ip):
        self._set_general(self._local_ip_string, ip)

    def get_local_ip(self):
        return self._get_general(self._local_ip_string)[0]

    def set_port(self, port):
        self._set_general(self._port_string, port)

    def get_port(self):
        return self._get_general(self._port_string)[0]

    def set_user(self, user):
        self._set_general(self._user_string, user)

    def get_user(self):
        return self._get_general(self._user_string)[0]

    def set_computer(self, computer):
        self._set_general(self._computer_string, computer)

    def get_computer(self):
        return self._get_general(self._computer_string)[0]

    def set_heartbeat(self):
        self._set_general(self._heartbeat_string, str(time.time()))

    def get_heartbeat(self):
        return self._get_general(self._heartbeat_string)[0]

    def set_login(self, login):
        self._set_general(self._login_string, str(login))

    def get_login(self):
        return self._get_general(self._login_string)  # tuple of (is_logged_in, login_timestamp)

    def get_last_mivui(self, file_path):
        with self.db_engine.connect() as conn:
            q_cmd = self.change_table.select().where(self.change_table.c.path == file_path)
            q_result = self._execute_with_retry(conn, q_cmd, 'get_last_mivui')
            all_rows = q_result.fetchall()
            if all_rows:
                last = all_rows[-1]
                last_mivui = last[0]
            else:
                last_mivui = -1
                conn.close()
            return last_mivui

    def get_last_mivuis_info(self):
        # todo: make this an interator, DB must stay open so to has to have a conn passed in
        infos = []
        with self.db_engine.connect() as conn:

            # get all the paths that have a pending
            paths_pending = set()
            cmd = self.change_table.select().where(self.change_table.c.pending).distinct(self.change_table.c.path)
            result = self._execute_with_retry(conn, cmd, 'get_last_mivuis_info_0')
            if result:
                for row in result.fetchall():
                    paths_pending.add(row[int(ChangeAttributes.path)])

            # get the last entry for each path
            for path in paths_pending:
                q_cmd = self.change_table.select().where(sqlalchemy.and_(self.change_table.c.path == path, self.change_table.c.pending))
                q_result = self._execute_with_retry(conn, q_cmd, 'get_last_mivuis_info_1')
                all_rows = q_result.fetchall()
                if all_rows:
                    # get the most senior miv entry for each path
                    all_rows = sorted(all_rows, key=lambda x: x[int(ChangeAttributes.mivui)])
                    last = all_rows[-1]
                    infos.append(self.db_row_to_info(last))
            conn.close()

        return infos

    def get_info_from_path_and_mivui(self, path, mivui):
        with self.db_engine.connect() as conn:
            path = norm_latus_path(path)  # paths are stored in DB as latus normalized paths
            q_cmd = self.change_table.select().where(sqlalchemy.and_(self.change_table.c.mivui == mivui, self.change_table.c.path == path))
            q_result = self._execute_with_retry(conn, q_cmd, 'get_info_from_path_and_mivui')
            # todo: check that there is indeed only one entry returned
            if q_result:
                row = q_result.fetchone()
                if row:
                    conn.close()
                    return self.db_row_to_info(row)
            else:
                latus.logger.log.warn('DB execute error')
            conn.close()
        return None

    def any_pendings(self, path):
        any_pending_flag = False
        with self.db_engine.connect() as conn:
            cmd = self.change_table.select().where(sqlalchemy.and_(self.change_table.c.path == path, self.change_table.c.pending == True))
            result = self._execute_with_retry(conn, cmd, 'any_pendings')
            rows = result.fetchall()
            if len(rows) > 0:
                any_pending_flag = True
            conn.close()
        return any_pending_flag

    def update_pending(self, info, pending_flag=False):
        with self.db_engine.connect() as conn:
            result = None
            stmt = self.change_table.update().values(pending=pending_flag).where(self.change_table.c.file_path == info['file_path'] and self.change_table.c.mivui == info['mivui'])
            result = self._execute_with_retry(conn, stmt, 'clear_pending')
            if not result:
                latus.logger.log.error('clear_pending of %s %s failed' % (info['path'], info['mivui']))
            conn.close()

    def get_folder_preferences_from_path(self, partial_path):
        return self.get_folder_preferences_from_folder(os.path.dirname(partial_path))

    def get_folder_preferences_from_folder(self, partial_folder_path):
        encrypt = True
        shared = False
        cloud = False
        if self.db_engine:
            conn = self.db_engine.connect()
            command = self.folders_table.select().where(self.folders_table.c.name == partial_folder_path)
            result = self._execute_with_retry(conn, command, 'get_folder_preferences_from_folder')
            if result:
                row = result.fetchone()
                if row:
                    encrypt = row[1]
                    shared = row[2]
                    cloud = row[3]
                else:
                    latus.logger.log.warn('get_folder_preferences: %s : %s : no row, using defaults' % (self.get_node_id(), partial_folder_path))
            else:
                latus.logger.log.warn('get_folder_preferences: %s : %s : no result' % (self.get_node_id(), partial_folder_path))
            conn.close()
        else:
            latus.logger.log.warn('get_folder_preferences: %s : %s : db_engine error' % (self.get_node_id(), partial_folder_path))
        return encrypt, shared, cloud

    def set_folder_preferences(self, name, encrypt, shared, cloud):
        if self.db_engine is None:
            latus.logger.log.warn('set_folder_preferences: db_engine is None')
            return False
        conn = self.db_engine.connect()
        select_command = self.folders_table.select().where(self.folders_table.c.name == name)
        select_result = self._execute_with_retry(conn, select_command, 'set_folder_preferences_select')
        do_insert = True
        if select_result:
            row = select_result.fetchone()
            if row:
                do_insert = False
                update_command = self.folders_table.update().where(self.folders_table.c.name == name).\
                    values(name=name, encrypt=encrypt, shared=shared, cloud=cloud,
                           timestamp=datetime.datetime.utcnow())
                self._execute_with_retry(conn, update_command, 'set_folder_preferences_update')
        if do_insert:
            insert_command = self.folders_table.insert().values(name=name, encrypt=encrypt, shared=shared, cloud=cloud,
                                                                timestamp=datetime.datetime.utcnow())
            self._execute_with_retry(conn, insert_command, 'set_folder_preferences_insert')
        conn.close()
        return True


def get_existing_nodes(cloud_node_db_folder):
    node_db_files = glob.glob(os.path.join(cloud_node_db_folder, '*' + DB_EXTENSION))
    return set(os.path.basename(p).split('.')[0] for p in node_db_files)


def get_node_id_from_db_file_path(db_file_path):
    ext_len = len(DB_EXTENSION)
    return os.path.basename(db_file_path)[:-ext_len]


def sync_dbs(cloud_node_folder, source_node_id, destination_node_id):
    source_node_db = NodeDB(cloud_node_folder, source_node_id)
    destination_node_db = NodeDB(cloud_node_folder, destination_node_id)
    source_infos = source_node_db.get_rows_as_info()
    for source_info in source_infos:
        dest_info = destination_node_db.get_info_from_path_and_mivui(source_info['path'], source_info['mivui'])
        if dest_info is None:
            destination_node_db.insert_info(source_info, True)  # mark as pending


def norm_latus_path(path):
    """
    Return a normalized latus path - this is a path with only forward slashes.
    This is chosen since converting from MacOS/OSX/Linux to Windows (forward slashes to backward slashes) is
    straightforward and most of the Python OS routines make this conversion automatically.  Converting from
    backward slashes to forward slashes are problematic since backward slash is also an escape character.
    :param path: file system path
    :return: normalized latus style path
    """
    if path is None:
        p = None
    else:
        # os.path.normpath() also provides collapsing and up leveling
        p = os.path.normpath(path).replace('\\', '/')
    return p
