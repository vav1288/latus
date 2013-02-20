
import tempfile
import unittest
import logging
import logger
import os
import sqlite
import test_latus

class TestSQLite(unittest.TestCase):
    def setUp(self):
        self.log = logger.get_log()

    def create_table(self):
        db_name = tempfile.mktemp('.db')
        self.table = 'test_table'
        self.key_string = 'key'
        self.value_string = 'value'
        self.first_name_key = 'first'
        self.first_name = 'james'
        self.last_name_key = 'last'
        self.last_name = 'abel'

        self.db = sqlite.sqlite(db_name)
        self.db.add_col_text(self.key_string, True, True)
        self.db.add_col_text(self.value_string, True, True)
        self.db.add_col_auto_index()
        self.db.add_col_timestamp()
        self.db.create_table(self.table)

    def write_table(self):
        self.db.connect_to_table(self.table)
        self.db.insert((self.first_name_key, self.first_name))
        self.db.insert((self.last_name_key, self.last_name))
        key_val_dict = {}
        key_val_dict[self.key_string] = self.first_name_key
        self.assertEqual(self.first_name, self.db.get(key_val_dict, self.value_string)[0])
        key_val_dict[self.key_string] = self.last_name_key
        self.assertEqual(self.last_name, self.db.get(key_val_dict, self.value_string)[0])
        self.db.update({self.value_string : "JC"}, {self.key_string : self.first_name_key})

    def close(self):
        self.db.close()

    def test_create_table(self):
        self.create_table()
        self.close()

    def test_write_table(self):
        self.create_table()
        self.write_table()
        self.close()
