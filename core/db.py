
import os
import core.logger
import core.util
import core.walker
import core.hash
import datetime
import sqlalchemy
import sqlalchemy.orm
import sqlalchemy.ext.declarative

Base = sqlalchemy.ext.declarative.declarative_base()

class Common(Base):
    __tablename__ = 'common'
    key = sqlalchemy.Column(sqlalchemy.String, primary_key=True)
    val = sqlalchemy.Column(sqlalchemy.String)

class Files(Base):
    __tablename__ = 'files'
    path = sqlalchemy.Column(sqlalchemy.String) # path (off of root) for this file
    sha512 = sqlalchemy.Column(sqlalchemy.String) # sha512 for this file
    size = sqlalchemy.Column(sqlalchemy.BigInteger) # size of this file
    mtime = sqlalchemy.Column(sqlalchemy.DateTime) # most recent modification time of this file (UTC)
    hidden = sqlalchemy.Column(sqlalchemy.Boolean) # does this file have the hidden attribute set?
    system = sqlalchemy.Column(sqlalchemy.Boolean) # does this file have the system attribute set?
    count = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)

class DB:
    DB_EXT = '.db'
    def __init__(self, root, metadata_path, id = 'fs'):
        """
        root is the root folder of the filesystem
        metadata_path is an instance of the MetadataPath class that has the metadata folder
        id is use to create the mysql database filename
        """
        self.log = core.logger.get_log()
        self.root = root

        self.sqlite_db_path = 'sqlite:///' + "/".join(metadata_path.db_folder_as_list) + "/" + id + self.DB_EXT
        self.engine = sqlalchemy.create_engine(self.sqlite_db_path)
        Session = sqlalchemy.orm.sessionmaker(bind=self.engine)
        self.session = Session()

        if not self.engine.has_table(Common.__tablename__):
            Base.metadata.create_all(self.engine)
            self.session.add(Common(key = 'root', val = root))
            self.session.add(Common(key = 'absroot', val = os.path.abspath(root)))
            self.session.add(Common(key = 'updatetime', val = str(datetime.datetime.utcnow())))
            self.session.commit()

    def commit(self):
        self.session.query(Common).filter(Common.key == 'updatetime').update({"val" : str(datetime.datetime.utcnow())})
        self.session.commit()

    def is_time_different(self, time_a, time_b):
        return abs(time_a - time_b) > datetime.timedelta(seconds=1)

    def put_file_info(self, rel_path):
        full_path = os.path.join(self.root, rel_path)
        # todo: handle when file deleted
        if not core.util.is_locked(full_path):
            mtime = datetime.datetime.utcfromtimestamp(os.path.getmtime(full_path))
            size = os.path.getsize(full_path)
            # get the most recent row for this file
            db_entry = self.session.query(Files).filter(Files.path == rel_path).order_by(-Files.count).first()
            # Test to see if the file is new or has been updated.
            # On the same (i.e. local) file system, for a given file path, if the mtime is the same then the contents
            # are assumed to be the same.  Note that there is some debate if file size is necessary here, but I'll
            # use it just to be safe.
            if db_entry is None or db_entry.size != size or self.is_time_different(db_entry.mtime, mtime):
                hidden = core.util.is_hidden(full_path)
                system = core.util.is_system(full_path)
                is_big = size > 1024 * 1024 # only time big files
                sha512, sha512_time = core.hash.calc_sha512(full_path, is_big)
                if is_big:
                    # todo: have a table of longest sha512 calc times
                    print("todo:have a table of longest sha512 calc times", full_path, size, sha512_time)

                file_info = Files(path = rel_path, sha512 = sha512, size = size, mtime = mtime, hidden = hidden, system = system)
                self.session.add(file_info)
                self.commit()

    def get_info(self, rel_path):
        db_entry = None
        if rel_path is None:
            self.log.warning("rel_path is None")
        else:
            db_entry = self.session.query(Files).filter(Files.path == rel_path).order_by(-Files.count).first()
            if db_entry is None:
                self.log.warning('not found in db:' + rel_path)
        return db_entry

    def scan(self):
        source_walker = core.walker.Walker(self.root)
        for file_path in source_walker:
            self.put_file_info(file_path)