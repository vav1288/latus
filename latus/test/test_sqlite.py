
import unittest
import os
from . import test_latus
from .. import logger, sqlite, metadata_location, util

class TestSQLite(unittest.TestCase):
    def setUp(self):
        self.log = logger.get_log()

    def create_table(self):
        md = util.Metadata(test_latus.get_root(), self.__module__)
        if not os.path.exists(test_latus.get_root()):
            os.makedirs(test_latus.get_root())
        db_name = metadata_location.get_metadata_db_path(md)
        self.table = 'test_table'
        self.key_string = 'key'
        self.value_string = 'value'
        self.first_name_key = 'first'
        self.first_name = 'james'
        self.last_name_key = 'last'
        self.last_name = 'abel'

        print("db_name", db_name)
        self.db = sqlite.sqlite(db_name)
        self.db.add_col_text(self.table, self.key_string, True, True)
        self.db.add_col_text(self.table, self.value_string, True, True)
        self.db.add_col_auto_index(self.table, )
        self.db.add_col_timestamp(self.table, )
        print("self.table", self.table)
        self.db.create_table(self.table)

    def write_table(self):
        self.db.connect()
        self.db.insert(self.table, [self.first_name_key, self.first_name])
        self.db.insert(self.table, [self.last_name_key, self.last_name])
        key_val_dict = {}
        key_val_dict[self.key_string] = self.first_name_key
        self.assertEqual(self.first_name, self.db.get(self.table, key_val_dict, self.value_string)[0])
        key_val_dict[self.key_string] = self.last_name_key
        self.assertEqual(self.last_name, self.db.get(self.table, key_val_dict, self.value_string)[0])
        self.db.update(self.table, [self.value_string], [self.key_string], {self.key_string : self.first_name_key})

    def close(self):
        self.db.close()

    def test_create_table(self):
        self.create_table()
        self.close()

    def test_write_table(self):
        self.create_table()
        self.write_table()
        self.close()

if __name__ == "__main__":
    unittest.main()