
import os
import datetime
import platform
import getpass
import glob

import sqlalchemy
import sqlalchemy.exc

import latus.const
import latus.logger
import latus.util


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

        if not os.path.exists(cloud_node_db_folder):
            latus.util.make_dirs(cloud_node_db_folder)

        self.node_id = node_id
        # The DB file name is based on the node id.  This is important ... this way we never have a conflict
        # writing to the DB since there is only one writer.
        self.database_file_name = node_id + latus.const.DB_EXTENSION
        sqlite_file_path = os.path.join(cloud_node_db_folder, self.database_file_name)

        if not os.path.exists(sqlite_file_path) and not write_flag:
            latus.logger.log.error('DB does not exist and write_flag not set, can not initialize : %s' % sqlite_file_path)
            self.db_engine = None
            return

        # the 'bind' and 'connection' seem to be redundant - what do I really need????
        # (I seem to need the bind, so perhaps I can get rid of the connection?)
        self.db_engine = sqlalchemy.create_engine('sqlite:///' + os.path.abspath(sqlite_file_path))  # , echo=True)
        self.sa_metadata = sqlalchemy.MetaData()
        self.sa_metadata.bind = self.db_engine

        # general key/value store
        self.general_table = sqlalchemy.Table('general', self.sa_metadata,
                                              sqlalchemy.Column('key', sqlalchemy.String, primary_key=True),
                                              sqlalchemy.Column('value', sqlalchemy.String),
                                              sqlalchemy.Column('timestamp', sqlalchemy.DateTime),
                                              )

        # 'seq' is intended to be monotonically increasing (across all nodes) for this user.  It is used to
        # globally determine file modification order.  Exceptions can occur when 2 or more nodes are offline and
        # they both make changes.
        self.change_table = sqlalchemy.Table('change', self.sa_metadata,
                                             sqlalchemy.Column('index', sqlalchemy.Integer, primary_key=True),
                                             sqlalchemy.Column('seq', sqlalchemy.Integer, index=True),
                                             sqlalchemy.Column('originator', sqlalchemy.String),
                                             sqlalchemy.Column('path', sqlalchemy.String, index=True),
                                             sqlalchemy.Column('size', sqlalchemy.Integer),
                                             sqlalchemy.Column('hash', sqlalchemy.String, index=True),
                                             sqlalchemy.Column('mtime', sqlalchemy.DateTime),
                                             sqlalchemy.Column('timestamp', sqlalchemy.DateTime),
                                             )
        if write_flag:
            try:
                self.sa_metadata.create_all()
            except sqlalchemy.exc.OperationalError as e:
                # todo: this is really odd ... it keeps throwing these errors and I don't know why.  I shouldn't need
                # to do this since create_all() is supposed to check first.
                latus.logger.log.warn(str(e))
            self.set_all(node_id)

    def set_all(self, node_id):
        self.set_login(True)
        self.set_heartbeat()
        self.set_node_id(node_id)
        self.set_user(getpass.getuser())
        self.set_computer(platform.node())

    def update(self, seq, originator, file_path, size, hash, mtime):
        conn = self.db_engine.connect()
        latus.logger.log.info('%s updating %s %s %s %s %s %s' % (self.node_id, seq, originator, file_path, size, hash, mtime))
        command = self.change_table.select().where(self.change_table.c.seq == seq)
        result = conn.execute(command)
        if not result.fetchone():
            if mtime:
                command = self.change_table.insert().values(seq=seq, originator=originator, path=file_path, size=size,
                                                            hash=hash, mtime=mtime, timestamp=datetime.datetime.utcnow())
            else:
                # if file has been deleted, there's no mtime (but we can't pass None into a datetime)
                command = self.change_table.insert().values(seq=seq, originator=originator, path=file_path,
                                                            timestamp=datetime.datetime.utcnow())
            result = conn.execute(command)
        else:
            latus.logger.log.warn('seq %s already found - not updating' % seq)
        conn.close()

    def db_row_to_info(self, row):
        entry = {}
        entry['index'] = row[0]
        entry['seq'] = row[1]
        entry['originator'] = row[2]
        entry['path'] = row[3]
        entry['size'] = row[4]
        entry['hash'] = row[5]
        entry['mtime'] = row[6]
        entry['timestamp'] = row[7]
        return entry

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

    def get_paths(self):
        conn = self.db_engine.connect()
        file_paths = set()
        if self.change_table.exists():
            command = self.change_table.select()
            result = conn.execute(command)
            for row in result:
                file_path = row[3]  # todo: make these number indices defined somewhere
                if file_path not in file_paths:
                    file_paths.add(file_path)  # todo: make these number indices defined somewhere
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
                file_hash = all_hashes[-1][5]  # todo: make these number indices defined somewhere
        conn.close()
        return file_hash

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
            latus.logger.log.warn('db_engine is None')
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
        return val, timestamp

    def _set_general(self, key, value):
        if self.db_engine is None:
            latus.logger.log.warn('db_engine is None')
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

    def set_login(self, login):
        self._set_general(self._login_string, str(login))

    def get_login(self):
        return self._get_general(self._login_string)  # tuple of (is_logged_in, login_timestamp)

    def set_heartbeat(self):
        self._set_general(self._heartbeat_string, datetime.datetime.utcnow())

    def get_heartbeat(self):
        return self._get_general(self._heartbeat_string)[1]  # for heartbeat, value is irrelevant

    def get_last_seq(self, file_path):
        conn = self.db_engine.connect()
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


def get_existing_nodes(cloud_node_db_folder):
    node_db_files = glob.glob(os.path.join(cloud_node_db_folder, '*' + latus.const.DB_EXTENSION))
    return set(os.path.basename(p).split('.')[0] for p in node_db_files)

