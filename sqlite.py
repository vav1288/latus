
import sqlite3
import time
import os
import sys
import logging
import logger

class sqlite():
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
        self.exec_db(cmd)

    def connect_to_table(self, table):
        self.table = table
        return self.connect()

    def make_str(self, plist, do_quotes = True):
        lstr = self.lstr('(')
        for elem in plist:
            if len(lstr) > 1:
                lstr += self.lstr(',')
            if do_quotes:
                lstr += self.lstr("'")
            lstr += self.cue(elem)
            if do_quotes:
                lstr += self.lstr("'")
        lstr += u')'
        return lstr

    def insert(self, vals):
        col_str = self.make_str(self.cols_order)
        val_str = self.make_str(vals)
        e = self.lstr("INSERT INTO ") + self.table + self.lstr(" ") + col_str + self.lstr(" VALUES ") + val_str
        self.exec_db(e, False)

    def update(self, values, where):
        # todo: do something like : c.execute('UPDATE objects SET created=?,modified=? WHERE id=?', (row[0:3])) ?
        valstr = self.lstr("")
        for key in values.keys():
            if len(valstr) > 0:
                valstr += self.lstr(',')
            valstr += self.cue(key) + self.lstr("='") + self.cue(values[key]) + self.lstr("'")
        wherestr = self.lstr("")
        for key in where.keys():
            if len(wherestr) > 0:
                wherestr += self.lstr(' AND ')
            wherestr += self.cue(key) + u"='" + self.cue(where[key]) + u"'"
        e = self.lstr("UPDATE ") + self.table + self.lstr(" SET ") + valstr + self.lstr(" WHERE ") + wherestr
        #print e
        self.exec_db(e, False)

    # Latus STRing - should call this for string constants
    def lstr(self, s):
        return unicode(s)

    # convert unicode and escape (CUE)
    # Converts various types and escape out special characters for sqlite.
    # returns a unicode string
    def cue(self,s):
        #print s
        if not isinstance(s, basestring):
            s = str(s) # e.g. numerics
        if not isinstance(s, unicode):
            s = unicode(s, "U8", "replace") # required for non-ascii filenames
        s = s.replace(self.lstr("'"), self.lstr("''")) # for sqlite
        #print s.encode("U8")
        return s

    # gets a list of entries of a particular column based on spec
    def get(self, qualifiers, col_name, operators = None):
        cmd = self.lstr("SELECT ") + unicode(col_name) + self.lstr(" from ") + unicode(self.table) + self.lstr(" WHERE ")
        subcmd = u""
        if qualifiers is not None:
            for col in qualifiers.keys():
                if len(subcmd) > 1:
                    subcmd += self.lstr(" AND ")
                if operators is None:
                    operator = self.lstr("=")
                else:
                    operator = operators[col] # e.g. LIKE
                subcmd += self.cue(col) + self.lstr(" ") + operator + self.lstr(" '") + self.cue(qualifiers[col]) + self.lstr("'")
            cmd += subcmd
        #print "cmd", cmd
        self.cur.execute(cmd)
        all = self.cur.fetchall()
        vals = []
        for one_row in all:
            vals.append(one_row[0]) # fetchall allows multiple columns - we're just getting one column entry
        if len(vals) < 1:
            vals = None
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



