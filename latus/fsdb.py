
import os
import datetime
import sqlalchemy
import latus.const


class FileSystemDB:
    def __init__(self, file_as_cloud_folder, partial_path=None):
        self.DATABASE_FILE_NAME = '.' + latus.const.NAME + '_sync' + '.db' # reserved
        sqlite_file_path = os.path.join(file_as_cloud_folder, self.DATABASE_FILE_NAME)
        self.db_engine = sqlalchemy.create_engine('sqlite:///' + os.path.abspath(sqlite_file_path))
        self.sa_metadata = sqlalchemy.MetaData()
        self.conn = self.db_engine.connect()
        self.general_table = sqlalchemy.Table('general', self.sa_metadata,
                                              sqlalchemy.Column('key', sqlalchemy.String),
                                              sqlalchemy.Column('value', sqlalchemy.String),
                                              )
        self.change_table = sqlalchemy.Table('change', self.sa_metadata,
                                             sqlalchemy.Column('index', sqlalchemy.Integer, index=True),
                                             sqlalchemy.Column('size', sqlalchemy.Integer),
                                             sqlalchemy.Column('hash', sqlalchemy.String),
                                             sqlalchemy.Column('mtime', sqlalchemy.DateTime),
                                             )
        self.sa_metadata.create_all(self.db_engine)  # eventually we can make this conditional on the db file existence
        if partial_path and not self.get_path():
            command = self.general_table.insert().values(key='path', value=partial_path)
            result = self.conn.execute(command)

    def update(self, size, hash, mtime, ):
        print('update', size, hash, mtime)
        command = self.change_table.insert().values(size=size, hash=hash,
                                                    mtime=datetime.datetime.utcfromtimestamp(mtime))
        result = self.conn.execute(command)

    def read(self):
        file_path = self.get_path()
        command = self.change_table.select()
        result = self.conn.execute(command)
        changes = []
        for row in result:
            change = {}
            change['size'] = row[1]
            change['hash'] = row[2]
            change['mtime'] = row[3]
            changes.append(change)
        return changes

    def get_path(self):
        file_path = None
        command = self.general_table.select().where(self.general_table.c.key=='path')
        general_result = self.conn.execute(command)
        if general_result:
            row = general_result.fetchone()
            if row:
                file_path = row[1]
        return file_path

    def close(self):
        self.conn.close()

