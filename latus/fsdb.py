
import os
import datetime
import sqlalchemy
import latus.logger


class FileSystemDB:
    def __init__(self, cloud_fs_db_folder, node_id):
        # The DB file name is based on the node id.  This is important ... this way we never have a conflict
        # writing to the DB since there is only one writer.
        self.database_file_name = node_id + '.db'
        sqlite_file_path = os.path.join(cloud_fs_db_folder, self.database_file_name)
        self.db_engine = sqlalchemy.create_engine('sqlite:///' + os.path.abspath(sqlite_file_path))
        self.sa_metadata = sqlalchemy.MetaData()
        self.conn = self.db_engine.connect()
        self.general_table = sqlalchemy.Table('general', self.sa_metadata,
                                              sqlalchemy.Column('key', sqlalchemy.String, primary_key=True),
                                              sqlalchemy.Column('value', sqlalchemy.String),
                                              )
        # 'sequence' is intended to be monotonically increasing (across all nodes) for this user.  It is used to
        # globally determine file modification order.  Exceptions can occur when 2 or more nodes are offline and
        # they both make changes.  This is only a problem when nodes modify the same file offline, which is
        # essentially a conflict.
        self.change_table = sqlalchemy.Table('change', self.sa_metadata,
                                             sqlalchemy.Column('sequence', sqlalchemy.Integer, primary_key=True),
                                             sqlalchemy.Column('path', sqlalchemy.Integer, index=True),
                                             sqlalchemy.Column('size', sqlalchemy.Integer),
                                             sqlalchemy.Column('hash', sqlalchemy.String, index=True),
                                             sqlalchemy.Column('mtime', sqlalchemy.DateTime),
                                             sqlalchemy.Column('timestamp', sqlalchemy.DateTime),
                                             )
        self.sa_metadata.create_all(self.db_engine)  # eventually we can make this conditional on the db file existence
        if self.get_node_id() != node_id:
            command = self.general_table.insert().values(key='nodeid', value=node_id)
            result = self.conn.execute(command)

    def update(self, sequence, file_path, size=None, hash=None, mtime=None):
        if mtime:
            command = self.change_table.insert().values(sequence=sequence, path=file_path, size=size, hash=hash,
                                                        mtime=datetime.datetime.utcfromtimestamp(mtime),
                                                        timestamp=datetime.datetime.utcnow())
        else:
            command = self.change_table.insert().values(sequence=sequence, path=file_path, size=size, hash=hash,
                                                        timestamp=datetime.datetime.utcnow())
        result = self.conn.execute(command)

    def get_file_info(self, file_path):
        command = self.change_table.select().where(self.change_table.c.path == file_path)
        result = self.conn.execute(command)
        changes = []
        for row in result:
            change = {}
            change['seq'] = row[0]
            change['path'] = row[1]
            change['size'] = row[2]
            change['hash'] = row[3]
            change['mtime'] = row[4]
            change['timestamp'] = row[5]
            changes.append(change)
        return changes

    def get_paths(self):
        command = self.change_table.select()
        result = self.conn.execute(command)
        file_paths = set()
        for row in result:
            file_path = row[1]
            if file_path not in file_paths:
                file_paths.add(row[1])
        return file_paths

    def get_most_recent_hash(self, file_path):
        file_hash = None
        command = self.change_table.select().where(self.change_table.c.path == file_path)
        result = self.conn.execute(command)
        if result:
            all_hashes = result.fetchall()
            if all_hashes:
                file_hash = all_hashes[-1][3]
        return file_hash

    def get_node_id(self):
        node_id = None
        command = self.general_table.select().where(self.general_table.c.key == 'nodeid')
        result = self.conn.execute(command)
        if result:
            row = result.fetchone()
            if row:
                node_id = row[1]
        return node_id

    def get_highest_sequence_value(self):
        highest_sequence_value = -1
        command = self.change_table.select()
        result = self.conn.execute(command)
        if result:
            for row in result:
                highest_sequence_value = max(highest_sequence_value,row[0])
        return highest_sequence_value

    def close(self):
        self.conn.close()

