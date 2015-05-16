
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
    def __init__(self, cloud_node_db_folder, node_id, public_key=None, write_flag=False):

        self._node_id_string = 'nodeid'
        self._local_ip_string = 'localip'
        self._port_string = 'port'
        self._public_key_string = 'publickey'
        self._user_string = 'user'
        self._computer_string = 'computer'

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
            self.set_node_id(node_id)
            self.set_public_key(public_key)
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

    def acquire_lock(self):
        lock_state = None
        conn = self.db_engine.connect()
        trans = conn.begin()
        not_yet_acquired = True
        while not_yet_acquired:
            lock_state = self.get_lock_state(conn)
            if lock_state is False:
                lock_state = True
                command = self.general_table.update().where(self.general_table.c.key == 'lock').values(value=str(True))
                result = conn.execute(command)
                not_yet_acquired = False
            elif lock_state is None:
                lock_state = True
                command = self.general_table.insert().values(key='lock', value=str(True))
                result = conn.execute(command)
                not_yet_acquired = False
        trans.commit()
        conn.close()
        return lock_state

    def release_lock(self):
        conn = self.db_engine.connect()
        lock_state = self.get_lock_state(conn)
        if lock_state:
            trans = conn.begin()
            command = self.general_table.update().where(self.general_table.c.key == 'lock').values(value=str(False))
            result = conn.execute(command)
            trans.commit()
            conn.close()
        else:
            latus.logger.log.warn('%s : lock already released' % self.node_id)
            raise Exception('lock already released')

    def get_lock_state(self, conn_param=None):
        conn = conn_param
        if conn is None:
            conn = self.db_engine.connect()
        lock_state = None
        result = None
        command = self.general_table.select().where(self.general_table.c.key == 'lock')
        try:
            result = conn.execute(command)
        except sqlalchemy.exc.OperationalError as e:
            latus.logger.log.warn('%s : %s' % (self.node_id, e))
        if result:
            row = result.fetchone()
            if row:
                lock_state = row[1] == str(True)  # we store the state as a string
        if conn_param is None:
            conn.close()
        return lock_state

    def _get_general(self, key):
        if self.db_engine is None:
            latus.logger.log.warn('db_engine is None')
            return None
        conn = self.db_engine.connect()
        val = None
        command = self.general_table.select().where(self.general_table.c.key == key)
        result = conn.execute(command)
        if result:
            row = result.fetchone()
            if row:
                val = row[1]
        conn.close()
        return val

    def _set_general(self, key, value):
        if self.db_engine is None:
            latus.logger.log.warn('db_engine is None')
            return None
        conn = self.db_engine.connect()
        db_value = None
        command = self.general_table.select().where(self.general_table.c.key == key)
        result = conn.execute(command)
        if result:
            row = result.fetchone()
            if row:
                db_value = row[1]
        if not db_value:
            command = self.general_table.insert().values(key=key, value=value)
            result = conn.execute(command)
        elif db_value != value:
            command = self.general_table.update().where(self.general_table.c.key == key).values(value=value)
            result = conn.execute(command)
        conn.close()

    def get_node_id(self):
        return self._get_general(self._node_id_string)

    def set_node_id(self, node_id):
        self._set_general(self._node_id_string, node_id)

    def get_local_ip(self):
        return self._get_general(self._local_ip_string)

    def set_local_ip(self, ip):
        self._set_general(self._local_ip_string, ip)

    def get_port(self):
        return self._get_general(self._port_string)

    def set_port(self, port):
        self._set_general(self._port_string, port)

    def set_public_key(self, public_key):
        self._set_general(self._public_key_string, public_key)

    def get_public_key(self):
        return self._get_general(self._public_key_string)

    def set_user(self, user):
        self._set_general(self._user_string, user)

    def get_user(self):
        return self._get_general(self._user_string)

    def set_computer(self, computer):
        self._set_general(self._computer_string, computer)

    def get_computer(self):
        return self._get_general(self._computer_string)

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

def node_id_from_node_db_file_path(node_db_file_path):
    return os.path.basename(node_db_file_path).split('.')[0]

def get_existing_nodes(cloud_node_db_folder):
    node_db_files = glob.glob(os.path.join(cloud_node_db_folder, '*' + latus.const.DB_EXTENSION))
    return [node_id_from_node_db_file_path(node_db_file) for node_db_file in node_db_files]

