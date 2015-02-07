
import os
import datetime
import sqlalchemy
import sqlalchemy.exc
import latus.logger


class FileSystemDB:
    def __init__(self, cloud_fs_db_folder, node_id, write_flag=False):
        self.node_id = node_id
        # The DB file name is based on the node id.  This is important ... this way we never have a conflict
        # writing to the DB since there is only one writer.
        self.database_file_name = node_id + '.db'
        sqlite_file_path = os.path.join(cloud_fs_db_folder, self.database_file_name)

        # the 'bind' and 'connection' seem to be redundant - what do I really need????
        # (I seem to need the bind, so perhaps I can get rid of the connection?)
        self.db_engine = sqlalchemy.create_engine('sqlite:///' + os.path.abspath(sqlite_file_path))
        self.sa_metadata = sqlalchemy.MetaData()
        self.sa_metadata.bind = self.db_engine

        self.general_table = sqlalchemy.Table('general', self.sa_metadata,
                                              sqlalchemy.Column('key', sqlalchemy.String, primary_key=True),
                                              sqlalchemy.Column('value', sqlalchemy.String),
                                              )
        # 'seq' is intended to be monotonically increasing (across all nodes) for this user.  It is used to
        # globally determine file modification order.  Exceptions can occur when 2 or more nodes are offline and
        # they both make changes.  This is only a problem when nodes modify the same file offline, which is
        # essentially a conflict.
        self.change_table = sqlalchemy.Table('change', self.sa_metadata,
                                             sqlalchemy.Column('seq', sqlalchemy.Integer, primary_key=True),
                                             sqlalchemy.Column('originator', sqlalchemy.String),
                                             sqlalchemy.Column('path', sqlalchemy.String, index=True),
                                             sqlalchemy.Column('size', sqlalchemy.Integer),
                                             sqlalchemy.Column('hash', sqlalchemy.String, index=True),
                                             sqlalchemy.Column('mtime', sqlalchemy.DateTime),
                                             sqlalchemy.Column('timestamp', sqlalchemy.DateTime),
                                             )
        if write_flag:
            self.sa_metadata.create_all(self.db_engine)
            self.set_node_id(node_id)

    def update(self, seq, originator, file_path, size, hash, mtime):
        conn = self.db_engine.connect()
        latus.logger.log.info('%s updating %s %s %s %s %s %s' % (self.node_id, seq, originator, file_path, size, hash, mtime))
        if mtime:
            command = self.change_table.insert().values(seq=seq, originator=originator, path=file_path, size=size,
                                                        hash=hash, mtime=mtime, timestamp=datetime.datetime.utcnow())
        else:
            # if file has been deleted, there's no mtime (but we can't pass None into a datetime)
            command = self.change_table.insert().values(seq=seq, originator=originator, path=file_path,
                                                        timestamp=datetime.datetime.utcnow())
        result = conn.execute(command)
        conn.close()

    def db_row_to_info(self, row):
        entry = {}
        entry['seq'] = row[0]
        entry['originator'] = row[1]
        entry['path'] = row[2]
        entry['size'] = row[3]
        entry['hash'] = row[4]
        entry['mtime'] = row[5]
        entry['timestamp'] = row[6]
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
                file_path = row[2]  # todo: make these number indices defined somewhere
                if file_path not in file_paths:
                    file_paths.add(row[2])  # todo: make these number indices defined somewhere
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
                file_hash = all_hashes[-1][4]  # todo: make these number indices defined somewhere
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


    def get_node_id(self):
        conn = self.db_engine.connect()
        node_id = None
        command = self.general_table.select().where(self.general_table.c.key == 'nodeid')
        result = conn.execute(command)
        if result:
            row = result.fetchone()
            if row:
                node_id = row[1]
        conn.close()
        return node_id

    def set_node_id(self, node_id):
        conn = self.db_engine.connect()
        db_node_id = self.get_node_id()
        latus.logger.log.debug('node_id : %s' % node_id)
        latus.logger.log.debug('db_node_id : %s' % db_node_id)
        if not db_node_id:
            latus.logger.log.debug('insert')
            command = self.general_table.insert().values(key='nodeid', value=node_id)
            result = conn.execute(command)
        elif db_node_id != node_id:
            latus.logger.log.debug('update')
            command = self.general_table.update().where(self.general_table.c.key == 'nodeid').values(value=node_id)
            result = conn.execute(command)
        else:
            latus.logger.log.debug('equal')
        conn.close()

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




