
import sqlite3
import time
import os
import sys
import win32api
import win32con
from . import logger, util


class sqlite:
    """ A layer on top of Python's SQLite capability.
    """
    def __init__(self, db_path):
        self.log = logger.get_log()
        self.type = {}
        self.cols_order = []
        self.ExecCount = 0 # of pending execs
        self.db_path = db_path # full path to db file
        self.conn = None
        self.cur = None
        self.last_command = None
        self.created_flag = not os.path.exists(db_path) # True if we created the db this instance - used to manage the file

    def __del__(self):
        if self.conn is not None:
            self.log.warning("conn not closed, db : %s, last_command : %s", self.db_path, self.last_command)
            self.close()
        if self.cur is not None:
            self.log.warning("cur not closed, db : %s, last_command : %s", self.db_path, self.last_command)
            self.close()

    def set_cols(self, cols):
        self.cols_order = cols

    def clean(self):
        self.close()
        ret = False
        # this is a bit brute force, but I'll use it for now
        if os.path.exists(self.db_path):
            self.log.debug("deleting %s", self.db_path)
            try:
                os.remove(self.db_path)
                ret = True
            except:
                self.log.warn("could not remove %s", self.db_path)
        return ret

    # returns True on successful connection
    def connect(self, create_flag = False):
        success_flag = False
        assert(self.db_path is not None)
        if os.path.exists(self.db_path) or create_flag:
            self.conn = sqlite3.connect(self.db_path)
            self.cur = self.conn.cursor()
            success_flag = True
        return success_flag

    def close(self):
        self.commit()
        if self.cur is not None:
            self.cur.close()
        if self.conn is not None:
            self.conn.close()
        self.cur = None
        self.conn = None
        if os.path.exists(self.db_path) and self.created_flag and util.is_windows():
            win32api.SetFileAttributes(self.db_path,win32con.FILE_ATTRIBUTE_HIDDEN)

    def exists(self):
        return os.path.exists(self.db_path)

    def add_col(self, name, type = 'text', isnonnull = False, isunique = False, is_builtin = False):
        if not is_builtin:
            self.cols_order.append(name)
        if isnonnull:
            type += ' NOT NULL'
        if isunique:
            type += ' UNIQUE'
        self.type[name] = type

    def add_col_auto_index(self):
        self.autoindex_str = 'autoindex'
        self.add_col(self.autoindex_str, 'INTEGER PRIMARY KEY AUTOINCREMENT', is_builtin=True)

    def add_col_timestamp(self):
        self.timestamp_str = 'timestamp'
        self.add_col(self.timestamp_str, 'DEFAULT CURRENT_TIMESTAMP', is_builtin=True)

    def add_col_text(self, name, isnonnull = False, isunique = False):
        self.add_col(name, 'text', isnonnull, isunique)

    def add_col_integer(self, name, isnonnull = False):
        self.add_col(name, 'integer', isnonnull)

    def add_col_float(self, name, isnonnull = False):
        self.add_col(name, 'float', isnonnull)

    def add_col_bool(self, name, isnonnull = False):
        self.add_col_integer(name, isnonnull)

    def create_table(self, table):
        self.log.info("creating %s : %s", self.db_path, table)
        self.table = table
        colstr = ''
        for col in self.cols_order:
            if len(colstr) > 0:
                colstr += ','
            colstr += str(col) + ' ' + self.type[col]
        colstr += "," + self.timestamp_str + ' ' + self.type[self.timestamp_str]
        colstr += "," + self.autoindex_str + ' ' + self.type[self.autoindex_str]
        cmd = 'CREATE TABLE IF NOT EXISTS ' + self.table + "(" + colstr + ")"
        self.connect(True)
        #self.log.info(cmd)
        self.exec_db(cmd)

    def create_index(self, key, unique = False):
        cmd = "CREATE"
        if unique:
            cmd += " UNIQUE"
        cmd += " INDEX"
        cmd += " idx_" + key
        cmd += " ON " + self.table + "(" + key + ")"
        #self.log.info(cmd)
        self.exec_db(cmd)

    def connect_to_table(self, table):
        self.table = table
        return self.connect()

    def make_str(self, plist, do_quotes = True):
        lstr = '('
        for elem in plist:
            if len(lstr) > 1:
                lstr += ','
            if do_quotes:
                lstr += "'"
            lstr += self.cue(elem)
            if do_quotes:
                lstr += "'"
        lstr += ')'
        return lstr

    def insert(self, vals):
        col_str = self.make_str(self.cols_order)
        val_str = self.make_str(vals)
        e = "INSERT INTO " + self.table + " " + col_str + " VALUES " + val_str
        self.exec_db(e, False)

    def update(self, values, where):
        # todo: do something like : c.execute('UPDATE objects SET created=?,modified=? WHERE id=?', (row[0:3])) ?
        valstr = ""
        for key in list(values.keys()):
            if len(valstr) > 0:
                valstr += ','
            # this expects the value strings to be quoted already (so the numeric values or equations can be unquoted)
            valstr += self.cue(key) + "=" + self.cue(values[key])
        wherestr = ""
        for key in list(where.keys()):
            if len(wherestr) > 0:
                wherestr += ' AND '
            wherestr += self.cue(key) + "='" + self.cue(where[key]) + "'"
        e = "UPDATE " + self.table + " SET " + valstr + " WHERE " + wherestr
        #print ("update", e)
        self.exec_db(e, False)

    # should call this for string constants
    # todo: just remove this
    def lstr(self, s):
        return s
        #return util.decode_text(s)

    # convert to unicode and escape (CUE)
    # Converts various types and escape out special characters for sqlite.
    def cue(self,s):
        s = str(s)
        s = s.replace("'", "''") # for sqlite string
        s = s.replace("\"", "'") # " --> ' for sqlite --- this is a kluge but I don't know of anything better ...
        return s

    # gets a list of entries of a particular column based on spec
    def get(self, qualifiers, col_name, operators = None):
        tolerance = 0.001 # todo: determine if this is really the best value - perhaps store strings instead of floating point?
        cmd = "SELECT " + self.cue(col_name) + " from " + self.cue(self.table) + " WHERE "
        subcmd = ""
        if qualifiers is not None:
            for col in list(qualifiers.keys()):
                if len(subcmd) > 1:
                    subcmd += " AND "
                if operators is None:
                    operator = "="
                else:
                    operator = operators[col] # e.g. LIKE or BETWEEN
                if operator.lower() == 'between':
                    # todo: assume (actually require) floats to come in as floats, and not convert them here
                    subcmd += self.cue(col) + " " + operator + " " + self.cue(float(qualifiers[col]) - tolerance) + \
                              " AND " + self.cue(float(qualifiers[col]) + tolerance)
                else:
                    subcmd += self.cue(col) + " " + operator + " '" + self.cue(qualifiers[col]) + "'"
            cmd += subcmd
        #print ("cmd", cmd)
        self.cur.execute(cmd)
        all = self.cur.fetchall()
        vals = []
        for one_row in all:
            vals.append(one_row[0]) # fetchall allows multiple columns - we're just getting one column entry
        if len(vals) < 1:
            vals = None
        #print ("vals", vals)
        return(vals)

    def commit(self):
        if self.conn is not None:
            try:
                self.conn.commit()
            except:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                self.log.warning("commit %s", str(exc_value))
        self.ExecCount = 0

    # For performance generally use commit_flag = False (default is True for safety sake)
    # and then follow up with a commit().
    # (avoiding commits every exec can make things ~10x faster)
    def exec_db(self, command, commit_flag = True):
        # for some reason, the database can just disappear for short periods of time
        # so this code tolerates this disappearance
        self.last_command = command # for debug
        #print "exec_db command", command
        Done = False
        TryCount = 0
        MaxTries = 3
        while not Done:
            TryCount += 1
            try:
                self.cur.execute(command)
                self.ExecCount += 1
                # since we write out a timestamp, don't wait too long between commits
                if commit_flag or (self.ExecCount > 1000):
                    self.commit()
                Done = True
            except sqlite3.OperationalError:
                # tolerate a few retries, but otherwise raise an exception
                if TryCount < MaxTries:
                    # for 'debug'
                    self.log.info("SQLite retry %s", command)
                    time.sleep(1)
                else:
                    raise
        self.commit()



