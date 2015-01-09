import os
import datetime
import time
import random

import sqlalchemy
import sqlalchemy.exc
import sqlalchemy.ext.declarative

import latus.logger

"""
    Monotonically Increasing Value (miv)
"""


Base = sqlalchemy.ext.declarative.declarative_base()


class MonotonicallyIncreasingValue():
    def __init__(self, folder):
        self.database_file_name = 'miv.db'
        sqlite_file_path = os.path.join(folder, self.database_file_name)
        self.db_engine = sqlalchemy.create_engine('sqlite:///' + os.path.abspath(sqlite_file_path))
        sa_metadata = sqlalchemy.MetaData()
        self.conn = self.db_engine.connect()
        self.miv_table = sqlalchemy.Table('miv', sa_metadata,
                                          sqlalchemy.Column('value', sqlalchemy.Integer, primary_key=True),
                                          sqlalchemy.Column('timestamp', sqlalchemy.DateTime),
                                          )
        sa_metadata.create_all(self.db_engine)
        value = self.get()
        if value is None:
            # initialize
            command = self.miv_table.insert().values(value=0, timestamp=datetime.datetime.utcnow())
            self.conn.execute(command)

    def next(self):
        command = self.miv_table.update().values(value=self.miv_table.c.value + 1, timestamp=datetime.datetime.utcnow())
        self.conn.execute(command)
        return self.get()

    def get(self):
        miv_value = None
        result = self.conn.execute(self.miv_table.select())
        if result:
            row = result.fetchone()
            if row:
                miv_value = row[0]
        latus.logger.log.info('miv : %s' % miv_value)
        return miv_value

    def close(self):
        self.conn.close()


def next_miv(folder):
    """
    Return next monotonically increasing value.  Returns None if it could not be determined.
    :param folder: folder where the sqlite db file resides
    :return: a monotonically increasing integer (or None on error)
    """
    value = None
    time_out_counter = 0
    while value is None and time_out_counter < 10:
        time_out_counter += 1
        # In case the DB is locked, wait and retry (in a loop).
        # If this fails it seems to take a few seconds to do so, so each iteration is a few seconds.
        try:
            miv = MonotonicallyIncreasingValue(folder)
            value = miv.next()
            miv.close()
        except sqlalchemy.exc.OperationalError:
            latus.logger.log.info('db retry %s' % time_out_counter)
            time.sleep(0.5 + random.random())  # 1 sec on average
    if value is None:
        latus.logger.log.error('monotonically increasing value could not be determined')
    return value

if __name__ == '__main__':
    latus.logger.init('temp')
    print(next_miv('temp'))