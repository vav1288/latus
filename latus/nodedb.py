
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

# DB schema version is the latus version where this schema was first introduced.  If your DB schema is earlier
# than (i.e. "less than") this, you need to do a drop all tables and start over.  This value is MANUALLY copied from
# latus.__version__ when a new and incompatible schema is introduced.
__db_version__ = '0.0.0'


class NodeDB:
    def __init__(self, cloud_node_db_folder, node_id, write_flag=False):

        self._node_id_string = 'nodeid'
        self._local_ip_string = 'localip'
        self._port_string = 'port'
        self._public_key_string = 'publickey'
        self._user_string = 'user'
        self._computer_string = 'computer'
        self._login_string = 'login'
        self._heartbeat_string = 'heartbeat'

        self.retry_count = None

        self.node_id = node_id
        # The DB file name is based on the node id.  This is important ... this way we never have a conflict
        # writing to the DB since there is only one writer.
        self.database_file_name = node_id + DB_EXTENSION
        self.sqlite_file_path = os.path.join(cloud_node_db_folder, self.database_file_name)

        if not os.path.exists(self.sqlite_file_path) and not write_flag:
            latus.logger.log.error('DB does not exist and write_flag not set, can not initialize : %s' % self.sqlite_file_path)
            self.db_engine = None
            return

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
                                             sqlalchemy.Column('seq', sqlalchemy.Float, index=True),  # todo: make this a string
                                             sqlalchemy.Column('originator', sqlalchemy.String),
                                             sqlalchemy.Column('event', sqlalchemy.Integer),
                                             sqlalchemy.Column('detection', sqlalchemy.Integer),
                                             sqlalchemy.Column('path', sqlalchemy.String, index=True),
                                             sqlalchemy.Column('size', sqlalchemy.Integer),
                                             sqlalchemy.Column('hash', sqlalchemy.String, index=True),
                                             sqlalchemy.Column('mtime', sqlalchemy.DateTime),
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
            if self._get_general('version')[0] is None:
                new_schema = True
                latus.logger.log.info('%s : no version in DB' % self.node_id)
            elif latus.util.version_to_tuple(__db_version__) > latus.util.version_to_tuple(self._get_general('version')[0]):
                new_schema = True
                latus.logger.log.info('%s : new DB schema' % self.node_id)
            if not self.db_engine.has_table('general') or new_schema:
                latus.logger.log.info('%s : start creating node DB version %s' % (node_id, __db_version__))
                try:
                    self.sa_metadata.drop_all()
                    self.sa_metadata.create_all()
                except sqlalchemy.exc.OperationalError as e:
                    # todo: this is really odd ... it keeps throwing these errors and I don't know why.  I shouldn't need
                    # to do this since create_all() is supposed to check first.
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

    def update(self, seq, originator, event, detection, file_path, size, hash, mtime, pending):
        conn = self.db_engine.connect()
        latus.logger.log.info('%s updating %s %s %s %s %s %s %s %s %s' % (self.node_id, seq, originator, event, detection,
                                                                       file_path, size, hash, mtime, pending))
        command = self.change_table.select().where(self.change_table.c.seq == seq)
        result = conn.execute(command)
        if not result.fetchone():
            if mtime:
                command = self.change_table.insert().values(seq=seq, originator=originator, event=event,
                                                            detection=detection, path=file_path, size=size, hash=hash,
                                                            mtime=mtime, pending=pending,
                                                            timestamp=datetime.datetime.utcnow())
            else:
                # if file has been deleted, there's no mtime (but we can't pass None into a datetime)
                command = self.change_table.insert().values(seq=seq, originator=originator, event=event,
                                                            detection=detection, path=file_path, pending=pending,
                                                            timestamp=datetime.datetime.utcnow())
            result = conn.execute(command)
        else:
            latus.logger.log.warn('seq %s already found - not updating' % seq)
        conn.close()

    def update_info(self, info, pending):
        self.update(info['seq'], info['originator'], info['event'], info['detection'], info['path'], info['size'],
                    info['hash'], info['mtime'], pending)

    def db_row_to_info(self, row):
        entry = {}
        entry['index'] = row[int(ChangeAttributes.index)]
        entry['seq'] = row[int(ChangeAttributes.seq)]
        entry['originator'] = row[int(ChangeAttributes.originator)]
        entry['event'] = row[int(ChangeAttributes.event)]
        entry['detection'] = row[int(ChangeAttributes.detection)]
        entry['path'] = row[int(ChangeAttributes.path)]
        entry['size'] = row[int(ChangeAttributes.size)]
        entry['hash'] = row[int(ChangeAttributes.hash)]
        entry['mtime'] = row[int(ChangeAttributes.mtime)]
        entry['pending'] = row[int(ChangeAttributes.pending)]
        entry['timestamp'] = row[int(ChangeAttributes.timestamp)]
        return entry

    def get_database_file_name(self):
        return self.database_file_name

    def get_file_info(self, file_path):
        conn = self.db_engine.connect()
        command = self.change_table.select().where(self.change_table.c.path == file_path)
        result = conn.execute(command)
        updates = []
        for row in result:
            updates.append(self.db_row_to_info(row))
        conn.close()
        return updates

    def get_latest_file_info(self, file_path):
        conn = self.db_engine.connect()
        command = self.change_table.select().where(self.change_table.c.path == file_path)
        result = conn.execute(command)
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
            result = conn.execute(command)
            for row in result:
                file_path = row[int(ChangeAttributes.path)]
                if file_path not in file_paths:
                    file_paths.add(file_path)
        else:
            latus.logger.log.warning('change_table does not exist')
        conn.close()
        return file_paths

    def get_most_recent_hash(self, file_path):
        conn = self.db_engine.connect()
        file_hash = None
        command = self.change_table.select().where(self.change_table.c.path == file_path)
        result = conn.execute(command)
        if result:
            all_hashes = result.fetchall()
            if all_hashes:
                file_hash = all_hashes[-1][int(ChangeAttributes.hash)]
        conn.close()
        return file_hash

    def get_rows_as_info(self):
        # todo: make this an interator, DB must stay open so to has to have a conn passed in
        infos = []
        with self.db_engine.connect() as conn:
            command = self.change_table.select()
            result = conn.execute(command)
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
                latus.logger.log.info('execute retry : %s' % str(msg))
                result = None
                latus.util.wait_random_avg_1_sec()
        if result is None:
            latus.logger.log.error('execute error : %s' % str(msg))
        return result

    def _get_general(self, key):
        self.retry_count = 0
        val_is_valid = False
        if self.db_engine is None:
            latus.logger.log.warn('_get_general: db_engine is None')
            return None
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
        if self.db_engine is None:
            latus.logger.log.warn('_set_general: db_engine is None')
            return None
        self.retry_count = 0
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

    def get_last_seq(self, file_path):
        with self.db_engine.connect() as conn:
            q_cmd = self.change_table.select().where(self.change_table.c.path == file_path)
            q_result = conn.execute(q_cmd)
            all_rows = q_result.fetchall()
            if all_rows:
                last = all_rows[-1]
                last_seq = last[0]
            else:
                last_seq = -1
                conn.close()
            return last_seq

    def get_last_seqs_info(self):
        # todo: make this an interator, DB must stay open so to has to have a conn passed in
        infos = []
        with self.db_engine.connect() as conn:
            cmd = self.change_table.select().distinct(self.change_table.c.path)
            result = conn.execute(cmd)
            for row in result:
                q_cmd = self.change_table.select().where(sqlalchemy.and_(self.change_table.c.path == row[int(ChangeAttributes.path)], self.change_table.c.pending))
                q_result = conn.execute(q_cmd)
                all_rows = q_result.fetchall()
                if all_rows:
                    last = all_rows[-1]
                    infos.append(self.db_row_to_info(last))
                else:
                    last = None
            conn.close()
        return infos

    def get_info_from_path_and_seq(self, path, seq):
        with self.db_engine.connect() as conn:
            q_cmd = self.change_table.select().where(sqlalchemy.and_(self.change_table.c.seq == seq, self.change_table.c.path == path))
            q_result = conn.execute(q_cmd)
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
            result = conn.execute(cmd)
            rows = result.fetchall()
            print(len(rows))
            if len(rows) > 0:
                any_pending_flag = True
            conn.close()
        return any_pending_flag

    def clear_pending(self, info):
        with self.db_engine.connect() as conn:
            result = None
            stmt = self.change_table.update().values(pending=False).where(self.change_table.c.path == info['path'] and
                                                                          self.change_table.c.seq == info['seq'])
            result = conn.execute(stmt)
            if not result:
                latus.logger.log.error('clear_pending of %s %s failed' % (info['path'], info['seq']))

            conn.close()

    def get_folder_preferences_from_path(self, path):
        return self.get_folder_preferences_from_folder(os.path.basename(path))

    def get_folder_preferences_from_folder(self, folder):
        encrypt = True
        shared = False
        cloud = False
        if self.db_engine:
            conn = self.db_engine.connect()
            command = self.folders_table.select().where(self.folders_table.c.name == folder)
            result = conn.execute(command)
            if result:
                row = result.fetchone()
                if row:
                    encrypt = row[1]
                    shared = row[2]
                    cloud = row[3]
                else:
                    latus.logger.log.debug('get_folder_preferences: %s : %s : no row, using defaults' % (self.get_node_id(), folder))
            else:
                latus.logger.log.warn('get_folder_preferences: %s : %s : no result' % (self.get_node_id(), folder))
            conn.close()
        else:
            latus.logger.log.warn('get_folder_preferences: %s : %s : db_engine error' % (self.get_node_id(), folder))
        return encrypt, shared, cloud

    def set_folder_preferences(self, name, encrypt, shared, cloud):
        if self.db_engine is None:
            latus.logger.log.warn('set_folder_preferences: db_engine is None')
            return False
        conn = self.db_engine.connect()
        select_command = self.folders_table.select().where(self.folders_table.c.name == name)
        select_result = conn.execute(select_command)
        do_insert = True
        if select_result:
            row = select_result.fetchone()
            if row:
                do_insert = False
                update_command = self.folders_table.update().where(self.folders_table.c.name == name).\
                    values(name=name, encrypt=encrypt, shared=shared, cloud=cloud,
                           timestamp=datetime.datetime.utcnow())
                conn.execute(update_command)
        if do_insert:
            insert_command = self.folders_table.insert().values(name=name, encrypt=encrypt, shared=shared, cloud=cloud,
                                                                timestamp=datetime.datetime.utcnow())
            conn.execute(insert_command)
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
    for source_info in source_node_db.get_rows_as_info():
        dest_info = destination_node_db.get_info_from_path_and_seq(source_info['path'], source_info['seq'])
        if dest_info is None:
            destination_node_db.update_info(source_info, True)  # mark as pending
